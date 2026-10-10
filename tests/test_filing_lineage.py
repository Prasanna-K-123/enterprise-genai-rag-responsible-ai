import copy
import csv
from decimal import Decimal
import json
import xml.etree.ElementTree as ET
import pytest
from src.filing_lineage import RECEIPT, ROOT, canonical_sha, inline_value, parse_inline, validate_row, verify_receipt
from src.financial_tools import answer


def receipt():return json.loads(RECEIPT.read_text())


def test_all_registered_values_have_two_reconciled_source_representations():
    proof=receipt();summary=verify_receipt(proof)
    assert summary['register_rows']==39 and summary['distinct_fact_contexts']==33
    assert summary['companyfacts_matches']==39 and summary['inline_matches']==39
    assert summary['filing_byte_hash_matches']==0 and summary['filing_snapshots']==2
    assert all(x['captured_sha256']!=x['registered_capture_sha256'] for x in proof['filing_snapshots'])


def test_observation_year_is_not_the_comparative_filing_fy():
    output=answer(dict(entity='CCL',year=2023,metric='revenue'))
    assert output['fiscal_year']==2023 and output['value']==21593
    e=output['evidence'][0];assert e['period_end']=='2023-11-30' and e['observation_start']=='2022-12-01'
    proof=receipt();row=next(r for r in proof['records'] if r['register_row_sha256']==e['lineage_row_sha256'])
    assert row['companyfacts'][0]['fy']==2025


@pytest.mark.parametrize('field,value',[('value_raw','999'),('end','2026-05-31'),('unit','EUR'),('accession','unknown')])
def test_changed_register_fact_cannot_reuse_an_old_receipt(field,value):
    p=receipt();row=copy.deepcopy(p['records'][0]['register_row']);row[field]=value
    with pytest.raises(ValueError,match='register_row_not_reconciled'):validate_row(row,p)


def test_source_metadata_mutation_is_detected_even_if_its_local_digest_is_recomputed():
    p=receipt();r=p['records'][0];row=r['register_row']
    r['companyfacts'][0]['start']='2023-06-01';r['companyfacts_sha256']=canonical_sha(r['companyfacts'])
    with pytest.raises(ValueError,match='companyfacts_mismatch'):validate_row(row,p)
    p=receipt();p['records'][0]['resolved_tag']='Assets'
    with pytest.raises(ValueError,match='concept_mismatch'):validate_row(p['records'][0]['register_row'],p)


def test_company_namespace_and_evidence_cardinality_are_required():
    p=receipt();row=p['records'][0]['register_row'];p['cik']=320193
    with pytest.raises(ValueError,match='entity_or_schema'):validate_row(row,p)
    p=receipt();row=p['records'][0]['register_row'];p['records'].append(copy.deepcopy(p['records'][0]))
    with pytest.raises(ValueError,match='register_row_not_reconciled'):validate_row(row,p)


def test_inline_scale_is_distinct_from_rounding_decimals():
    n=ET.fromstring('<fact scale="6" decimals="-6" format="ixt:num-dot-decimal">2,790</fact>')
    assert inline_value(n)==Decimal('2790000000')
    n=ET.fromstring('<fact scale="3" decimals="-6" sign="-">1,000</fact>')
    assert inline_value(n)==Decimal('-1000000')
    with pytest.raises(ValueError,match='unsupported_inline_number_format'):
        inline_value(ET.fromstring('<fact format="ixt:num-comma-decimal">2,5</fact>'))


def test_segment_facts_are_not_consolidated_entity_facts():
    raw=b'''<root xmlns:x="urn:x" xmlns:ix="urn:ix" xmlns:d="urn:dimension">
      <x:context id="c"><x:identifier>0000815097</x:identifier><x:startDate>2024-12-01</x:startDate><x:endDate>2025-11-30</x:endDate><d:explicitMember>segment</d:explicitMember></x:context>
      <x:unit id="usd"><x:measure>iso4217:USD</x:measure></x:unit>
      <ix:nonFraction name="us-gaap:Revenue" contextRef="c" unitRef="usd" scale="6">100</ix:nonFraction>
    </root>'''
    assert parse_inline(raw)==[]
