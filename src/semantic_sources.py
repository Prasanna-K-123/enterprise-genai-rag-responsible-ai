"""Capture exact SEC concept histories and reconcile selected inline contexts.

Raw companyconcept JSON is retained. Full filing HTML is fetched into an
operator cache, not redistributed. Exact selected context/unit/fact XML nodes
are retained for offline reconciliation. Two representations of the same
disclosures are not an independent accounting audit.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET
from .semantic_contract import sha

ISSUERS = {'0000320193':'AAPL','0000789019':'MSFT'}
CONCEPTS = ['RevenueFromContractWithCustomerExcludingAssessedTax',
            'OperatingIncomeLoss', 'NetCashProvidedByUsedInOperatingActivities',
            'PaymentsToAcquirePropertyPlantAndEquipment']
YEARS = [2023,2024,2025]
CUTOFF = '2026-10-11'


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def local(tag): return tag.rsplit('}',1)[-1].lower()


def raw_fetch(url, path):
    if path.exists(): raise ValueError('source_capture_exists')
    request = urllib.request.Request(url,headers={'User-Agent':'Independent portfolio research ae26prasanna@mse.ac.in'})
    with urllib.request.urlopen(request,timeout=60) as response: raw=response.read()
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return {'url':url,'sha256':digest(path),'bytes':len(raw),
            'captured_at_utc':datetime.now(timezone.utc).isoformat()}


def select_accession(histories):
    groups={}
    for concept, source in histories.items():
        for fact in source['units'].get('USD',[]):
            if fact.get('form')!='10-K' or fact.get('filed','9999')>CUTOFF or not fact.get('start'):continue
            start,end=date.fromisoformat(fact['start']),date.fromisoformat(fact['end'])
            if end.year not in YEARS or not 350 <= (end-start).days <=380:continue
            groups.setdefault(fact['accn'],{}).setdefault((concept,end.year),[]).append(fact)
    complete=[]
    for accession,group in groups.items():
        if set(group)!={(c,y) for c in CONCEPTS for y in YEARS}:continue
        if any(len({(f['start'],f['end'],str(f['val'])) for f in fs})!=1 for fs in group.values()):continue
        complete.append((max(f['filed'] for fs in group.values() for f in fs),accession,group))
    if not complete:raise ValueError('no_complete_unambiguous_common_annual_accession')
    _,accession,group=max(complete,key=lambda x:(x[0],x[1]))
    return accession,{key:sorted(fs,key=lambda f:json.dumps(f,sort_keys=True))[0] for key,fs in group.items()}


def inline_nodes(raw,cik):
    tree=ET.fromstring(raw);contexts={};units={};out=[]
    for node in tree.iter():
        if local(node.tag)=='context':
            c={'start':'','end':'','entity':None,'dimensions':[]}
            for item in node.iter():
                name=local(item.tag);text=''.join(item.itertext()).strip()
                if name=='identifier':c['entity']=str(int(text)).zfill(10)
                elif name=='startdate':c['start']=text
                elif name in {'enddate','instant'}:c['end']=text
                elif name in {'explicitmember','typedmember'}:c['dimensions'].append(text)
            contexts[node.get('id')]=(c,ET.tostring(node,encoding='unicode'))
        elif local(node.tag)=='unit':
            measures=[''.join(x.itertext()).strip().split(':')[-1] for x in node.iter() if local(x.tag)=='measure']
            unit=measures[0] if len(measures)==1 and not any(local(x.tag)=='divide' for x in node.iter()) else 'unsupported'
            units[node.get('id')]=(unit,ET.tostring(node,encoding='unicode'))
    for node in tree.iter():
        if local(node.tag)!='nonfraction' or node.get('name') not in {'us-gaap:'+c for c in CONCEPTS}:continue
        context=contexts.get(node.get('contextRef'));unit=units.get(node.get('unitRef'))
        if not context or not unit or context[0]['entity']!=cik or context[0]['dimensions'] or unit[0]!='USD':continue
        fmt=node.get('format','').split(':')[-1]
        if fmt not in {'num-dot-decimal','fixed-zero',''}:continue
        text=re.sub(r'\s+','',''.join(node.itertext())).replace(',','').replace('$','')
        negative=text.startswith('(') and text.endswith(')');text=text.strip('()')
        try:
            value=Decimal(0) if fmt=='fixed-zero' else Decimal(text)
            if negative or node.get('sign')=='-':value=-abs(value)
            scale=int(node.get('scale','0'))
            if not -12<=scale<=12 or not value.is_finite():continue
            value*=Decimal(10)**scale
        except (ValueError,ArithmeticError):continue
        out.append({**context[0],'concept':node.get('name'),'unit':unit[0],'value':str(value),
                    'context_id':node.get('contextRef'),'fact_id':node.get('id'),
                    'scale':node.get('scale','0'),'decimals':node.get('decimals',''),
                    'context_xml':context[1],'unit_xml':unit[1],
                    'fact_xml':ET.tostring(node,encoding='unicode')})
    return out


def capture(directory,cache):
    directory=Path(directory);cache=Path(cache)
    if (directory/'CAPTURE.json').exists():raise ValueError('capture_exists')
    source_files=[];issuers=[];facts=[]
    for cik,alias in ISSUERS.items():
        histories={};meta={}
        for concept in CONCEPTS:
            name=cik+'/'+concept+'.json';path=directory/name
            receipt=raw_fetch(f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json',path)
            source=json.loads(path.read_text());assert source['cik']==int(cik) and source['tag']==concept and source['taxonomy']=='us-gaap'
            histories[concept]=source;meta[concept]={'path':name,**receipt};source_files.append(meta[concept])
        accession,selected=select_accession(histories)
        name=cik+'/submissions.json';receipt=raw_fetch(f'https://data.sec.gov/submissions/CIK{cik}.json',directory/name)
        submissions=json.loads((directory/name).read_text());recent=submissions['filings']['recent']
        if accession not in recent['accessionNumber']:raise ValueError('selected_accession_not_in_recent_submissions')
        index=recent['accessionNumber'].index(accession);document=recent['primaryDocument'][index]
        url=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/{document}'
        filing=raw_fetch(url,cache/f'{cik}_{document}');nodes=inline_nodes((cache/f'{cik}_{document}').read_bytes(),cik)
        source_files.append({'path':name,**receipt})
        issuer={'entity':cik,'alias':alias,'entity_name':submissions['name'],'accession':accession,'filing':filing,'selected':[]}
        for concept,year in [(c,y) for c in CONCEPTS for y in YEARS]:
            raw=selected[(concept,year)];matches=[n for n in nodes if n['concept']=='us-gaap:'+concept and n['start']==raw['start'] and n['end']==raw['end']]
            if not matches or any(Decimal(n['value'])!=Decimal(str(raw['val'])) for n in matches):raise ValueError('inline_context_value_mismatch')
            chosen=sorted(matches,key=lambda n:(n['context_id'],n['fact_id'] or ''))[0]
            ref='f_'+cik+'_'+str(CONCEPTS.index(concept))+'_'+str(year)
            fact={'ref':ref,'entity':cik,'accession':accession,'concept':'us-gaap:'+concept,
                  'start':raw['start'],'end':raw['end'],'unit':'USD','dimensions':[],
                  'value':str(raw['val']),'form':raw['form'],'filed':raw['filed'],
                  'source_path':meta[concept]['path'],'source_sha256':meta[concept]['sha256'],
                  'filing_url':url,'filing_sha256':filing['sha256'],'inline_fact_id':chosen['fact_id'],
                  'inline_context_id':chosen['context_id']}
            facts.append(fact);issuer['selected'].append({'ref':ref,'companyconcept_record':raw,'inline':chosen,
                                                       'equivalent_inline_matches':len(matches)})
        issuers.append(issuer)
    result={'schema':'semantic-sec-capture-v1','selection_cutoff':CUTOFF,'years':YEARS,
            'source_files':source_files,'issuers':issuers,'facts':facts,'facts_sha256':sha(facts),
            'scope':'Exact selected concept/unit/entity/observation dates and values reconcile between SEC concept JSON and inline filing nodes. Same disclosures, not independent accounting validation. Full HTML not redistributed.'}
    (directory/'CAPTURE.json').write_text(json.dumps(result,indent=2)+'\n')
    verify(directory)
    return result


def verify(directory):
    directory=Path(directory);receipt=json.loads((directory/'CAPTURE.json').read_text());expected=[]
    if receipt['schema']!='semantic-sec-capture-v1' or receipt['selection_cutoff']!=CUTOFF or receipt['years']!=YEARS:raise ValueError('capture_contract')
    for source in receipt['source_files']:
        path=directory/source['path']
        if digest(path)!=source['sha256'] or path.stat().st_size!=source['bytes']:raise ValueError('source_byte_mismatch')
    for issuer in receipt['issuers']:
        cik=issuer['entity'];histories={c:json.loads((directory/cik/(c+'.json')).read_text()) for c in CONCEPTS}
        accession,selected=select_accession(histories)
        if accession!=issuer['accession']:raise ValueError('accession_selection_mismatch')
        for record in issuer['selected']:
            original=next(f for f in receipt['facts'] if f['ref']==record['ref']);concept=original['concept'].split(':')[1];year=date.fromisoformat(original['end']).year
            raw=selected[(concept,year)]
            if raw!=record['companyconcept_record']:raise ValueError('raw_context_mismatch')
            inline=record['inline'];wrapper=('<root>'+inline['context_xml']+inline['unit_xml']+inline['fact_xml']+'</root>').encode()
            parsed=inline_nodes(wrapper,cik)
            if len(parsed)!=1 or any(parsed[0][k]!=inline[k] for k in ['entity','concept','start','end','unit','value','dimensions','fact_id','context_id','scale','decimals']):raise ValueError('inline_fragment_mismatch')
            if Decimal(inline['value'])!=Decimal(str(raw['val'])) or inline['start']!=raw['start'] or inline['end']!=raw['end']:raise ValueError('source_reconciliation_mismatch')
            source=next(s for s in receipt['source_files'] if s['path']==cik+'/'+concept+'.json')
            fact={'ref':record['ref'],'entity':cik,'accession':accession,'concept':'us-gaap:'+concept,
                  'start':raw['start'],'end':raw['end'],'unit':'USD','dimensions':[],
                  'value':str(raw['val']),'form':raw['form'],'filed':raw['filed'],
                  'source_path':source['path'],'source_sha256':source['sha256'],
                  'filing_url':issuer['filing']['url'],'filing_sha256':issuer['filing']['sha256'],
                  'inline_fact_id':inline['fact_id'],'inline_context_id':inline['context_id']}
            expected.append(fact)
    if expected!=receipt['facts'] or sha(expected)!=receipt['facts_sha256']:raise ValueError('capture_facts_mismatch')
    if {i['entity'] for i in receipt['issuers']}!=set(ISSUERS) or len(expected)!=24:raise ValueError('capture_coverage')
    return receipt
