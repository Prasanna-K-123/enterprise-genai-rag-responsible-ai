"""Reconcile the frozen CCL register with SEC XBRL and inline filing facts.

This checks two representations of the same issuer disclosures. It is not an
independent financial audit, source authenticity certificate or NLP benchmark.
Observation periods are taken from start/end dates, never the filing FY label.
"""
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CIK=815097
URL='https://data.sec.gov/api/xbrl/companyfacts/CIK0000815097.json'
EXTRA_TAGS={'depreciation_amortization':'DepreciationAndAmortization',
            'interest_expense':'InterestExpenseNonoperating'}
RECEIPT=ROOT/'reference/financial_tools/lineage_receipt.json'


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def local(tag):
    return tag.rsplit('}',1)[-1].lower()


def inline_value(node):
    fmt=node.get('format','').split(':')[-1]
    if fmt not in {'','num-dot-decimal','fixed-zero'}:
        raise ValueError('unsupported_inline_number_format')
    text=''.join(node.itertext()).strip().replace(',','').replace('\xa0','')
    text=re.sub(r'\s+','',text)
    if fmt=='fixed-zero':value=Decimal(0)
    else:
        negative=text.startswith('(') and text.endswith(')');text=text.strip('()$')
        try:value=Decimal(text)
        except InvalidOperation as e:raise ValueError('invalid_inline_number') from e
        if negative:value=-abs(value)
    try:scale=int(node.get('scale','0'))
    except ValueError as e:raise ValueError('invalid_inline_scale') from e
    if not -12<=scale<=12 or not value.is_finite():raise ValueError('inline_number_bounds')
    sign=node.get('sign','')
    if sign not in {'','-'}:raise ValueError('invalid_inline_sign')
    if sign=='-':value=-abs(value)
    return value*(Decimal(10)**scale)


def parse_inline(raw):
    tree=ET.fromstring(raw);contexts={};units={}
    for n in tree.iter():
        if local(n.tag)=='context':
            c={'id':n.get('id'),'dimensions':False,'start':'','end':'','cik':None}
            for x in n.iter():
                name=local(x.tag);text=''.join(x.itertext()).strip()
                if name=='identifier':
                    try:c['cik']=int(text)
                    except ValueError:c['cik']=None
                elif name=='startdate':c['start']=text
                elif name in {'enddate','instant'}:c['end']=text
                elif name in {'explicitmember','typedmember'}:c['dimensions']=True
            contexts[n.get('id')]=c
        elif local(n.tag)=='unit':
            measures=[''.join(x.itertext()).strip() for x in n.iter() if local(x.tag)=='measure']
            units[n.get('id')]=measures[0].split(':')[-1] if len(measures)==1 and not any(local(x.tag)=='divide' for x in n.iter()) else 'unsupported'
    facts=[]
    for n in tree.iter():
        if local(n.tag)!='nonfraction':continue
        context=contexts.get(n.get('contextRef'))
        if not context or context['cik']!=CIK or context['dimensions']:continue
        if units.get(n.get('unitRef'))!='USD':continue
        try:value=inline_value(n)
        except ValueError:continue
        facts.append(dict(tag=n.get('name'),start=context['start'],end=context['end'],
                          cik=context['cik'],unit='USD',value=str(value),fact_id=n.get('id'),
                          context_id=context['id'],scale=n.get('scale','0'),format=n.get('format',''),
                          sign=n.get('sign',''),decimals=n.get('decimals','')))
    return facts


def period_start(row,register):
    if row['source_type']=='sec_companyfacts' or row['start']:return row['start']
    # The table-collected rows omitted starts. Resolve only through a unique
    # existing typed companion period from the SAME evidence set/accession.
    starts={r['start'] for r in register if r['source_type']=='sec_companyfacts' and r['start']
            and all(r[k]==row[k] for k in ['evidence_set','ttm_bridge_role','accession','end'])}
    if len(starts)!=1:raise ValueError('ambiguous_or_missing_companion_period')
    return next(iter(starts))


def build_receipt(directory):
    register=list(csv.DictReader((ROOT/'reference/financial_tools/source_register.csv').open()))
    api_raw=(directory/'CIK0000815097.json').read_bytes();api=json.loads(api_raw)
    if api.get('cik')!=CIK:raise ValueError('source_cik_mismatch')
    filing_records=[];parsed={}
    for url in sorted({r['source_url'] for r in register if r['source_type']=='sec_filing_table'}):
        raw=(directory/url.rsplit('/',1)[-1]).read_bytes();sha=hashlib.sha256(raw).hexdigest()
        old={r['source_sha256'] for r in register if r['source_url']==url}
        if len(old)!=1:raise ValueError('ambiguous_registered_filing_hash')
        filing_records.append(dict(url=url,captured_sha256=sha,registered_capture_sha256=next(iter(old)),
                                   captured_at_utc=datetime.fromtimestamp((directory/url.rsplit('/',1)[-1]).stat().st_mtime,timezone.utc).isoformat(),
                                   same_bytes_as_registered_capture=sha in old,size_bytes=len(raw)))
        accession=next(r['accession'] for r in register if r['source_url']==url)
        parsed[accession]=[{**f,'accession':accession,'source_url':url,'source_sha256':sha} for f in parse_inline(raw)]
    records=[]
    for row in register:
        if row['unit']!='USD':raise ValueError('unsupported_register_unit')
        tag=row['xbrl_tag'] or EXTRA_TAGS.get(row['metric'])
        if not tag:raise ValueError('unsupported_register_concept')
        start=period_start(row,register);expected=Decimal(row['value_raw'])
        candidates=[f for f in api['facts']['us-gaap'][tag]['units']['USD']
                    if f.get('start','')==start and all(f.get(a)==row[b] for a,b in
                    [('end','end'),('accn','accession'),('form','form'),('filed','filed')])]
        if not candidates or any(Decimal(str(f['val']))!=expected for f in candidates):
            raise ValueError('companyfacts_value_or_context_mismatch')
        ix=[f for f in parsed[row['accession']] if f['tag']=='us-gaap:'+tag and f['start']==start and f['end']==row['end']]
        if not ix or any(Decimal(f['value'])!=expected for f in ix):
            raise ValueError('inline_value_or_context_mismatch')
        records.append(dict(register_row=row,register_row_sha256=canonical_sha(row),resolved_tag=tag,
            observed_start=start,observed_end=row['end'],unit='USD',companyfacts=candidates,
            companyfacts_sha256=canonical_sha(candidates),inline=ix,inline_sha256=canonical_sha(ix)))
    unique={(r['resolved_tag'],r['observed_start'],r['observed_end'],r['register_row']['accession']) for r in records}
    return dict(schema_version='ccl-sec-lineage-v1',cik=CIK,entity_namespace='CCL',
        current_api_entity_name=api['entityName'],generated_at_utc=datetime.now(timezone.utc).isoformat(),
        capture_time_basis='Local file timestamps immediately after HTTPS downloads from SEC domains',
        historical_register_snapshot='2026-09-02',
        companyfacts_source=dict(url=URL,sha256=hashlib.sha256(api_raw).hexdigest(),size_bytes=len(api_raw),
                                 captured_at_utc=datetime.fromtimestamp((directory/'CIK0000815097.json').stat().st_mtime,timezone.utc).isoformat()),
        filing_snapshots=filing_records,records=records,
        summary=dict(register_rows=len(records),distinct_fact_contexts=len(unique),companyfacts_matches=len(records),
            inline_matches=len(records),filing_byte_hash_matches=sum(f['same_bytes_as_registered_capture'] for f in filing_records),
            filing_snapshots=len(filing_records),
            scope='Exact unit, tag, accession and observation-date reconciliation across two representations of the same SEC disclosures. Historical values unchanged. Filing FY is not observation year. Current served HTML hashes differ from previous captures and are retained separately. Not an independent financial audit or general NLP accuracy.'))


def validate_row(row,receipt):
    if receipt.get('schema_version')!='ccl-sec-lineage-v1' or receipt.get('cik')!=CIK or receipt.get('entity_namespace')!='CCL':
        raise ValueError('lineage_entity_or_schema_mismatch')
    source=receipt['companyfacts_source']
    if source['url']!=URL or not re.fullmatch('[0-9a-f]{64}',source['sha256']):raise ValueError('lineage_source_mismatch')
    key=canonical_sha(row);matches=[r for r in receipt['records'] if r['register_row_sha256']==key]
    if len(matches)!=1:raise ValueError('register_row_not_reconciled')
    r=matches[0]
    if r['register_row']!=row or canonical_sha(r['companyfacts'])!=r['companyfacts_sha256'] or canonical_sha(r['inline'])!=r['inline_sha256']:
        raise ValueError('lineage_digest_mismatch')
    expected=Decimal(row['value_raw'])
    if r['resolved_tag']!=(row['xbrl_tag'] or EXTRA_TAGS.get(row['metric'])):raise ValueError('lineage_concept_mismatch')
    if r['unit']!='USD' or r['observed_end']!=row['end']:raise ValueError('lineage_period_or_unit_mismatch')
    for f in r['companyfacts']:
        if Decimal(str(f['val']))!=expected or f.get('start','')!=r['observed_start'] or any(f.get(a)!=row[b] for a,b in [('end','end'),('accn','accession'),('form','form'),('filed','filed')]):
            raise ValueError('lineage_companyfacts_mismatch')
    for f in r['inline']:
        sources=[s for s in receipt['filing_snapshots'] if s['url']==f['source_url'] and s['captured_sha256']==f['source_sha256']]
        if len(sources)!=1 or f['accession']!=row['accession'] or f['cik']!=CIK or f['unit']!='USD' or f['tag']!='us-gaap:'+r['resolved_tag'] or f['start']!=r['observed_start'] or f['end']!=row['end'] or Decimal(f['value'])!=expected:
            raise ValueError('lineage_inline_mismatch')
    if not r['companyfacts'] or not r['inline']:raise ValueError('lineage_evidence_missing')
    return r


def verify_receipt(receipt):
    rows=list(csv.DictReader((ROOT/'reference/financial_tools/source_register.csv').open()))
    if len(rows)!=len(receipt['records']):raise ValueError('lineage_coverage_mismatch')
    for row in rows:validate_row(row,receipt)
    return receipt['summary']


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path);p.add_argument('--output',type=Path,default=RECEIPT);a=p.parse_args()
    if a.build:
        if a.output.exists():raise RuntimeError('Receipt exists; do not overwrite source captures silently')
        receipt=build_receipt(a.build);a.output.write_text(json.dumps(receipt,indent=2)+'\n')
    else:receipt=json.loads(RECEIPT.read_text())
    print(json.dumps(verify_receipt(receipt),indent=2))
