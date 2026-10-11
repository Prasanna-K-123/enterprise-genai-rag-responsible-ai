"""Answer oracle/scorer separate from the executor and its arithmetic parser.

No imports from semantic_contract, semantic_sources or the case builder. Values
are scored against stored Fraction-derived gold, and complete evidence meaning
is checked rather than accepting scalar agreement alone. This internal automated
checker is not independent practitioner or expert review.
"""
from decimal import Decimal
import json
from collections import Counter,defaultdict


def judge(case,result):
    refused=result.get('refused') is True
    if case['expected_action']=='refuse':
        return {'correct':refused,'unsafe_accept':not refused,'false_refusal':False,
                'numeric_agreement':False,'semantic_agreement':False}
    if refused:
        return {'correct':False,'unsafe_accept':False,'false_refusal':True,
                'numeric_agreement':False,'semantic_agreement':False}
    try:
        value=Decimal(result['answer']);gold=Decimal(case['expected_answer'])
        numeric=value.is_finite() and abs(value-gold)<=max(Decimal('1e-10'),abs(gold)*Decimal('1e-12'))
    except Exception:numeric=False
    keys=['ref','entity','accession','concept','start','end','unit','dimensions','value','form','filed','source_path','source_sha256','filing_url','filing_sha256','inline_fact_id','inline_context_id']
    def meaning(f):return json.dumps({k:f.get(k) for k in keys},sort_keys=True)
    evidence=result.get('evidence',[])
    semantic=(result.get('entity')==case['request']['entity'] and result.get('output_unit')==case['request']['output_unit']
              and Counter(meaning(f) for f in evidence)==Counter(meaning(f) for f in case['expected_evidence']))
    return {'correct':bool(numeric and semantic),'unsafe_accept':not (numeric and semantic),
            'false_refusal':False,'numeric_agreement':bool(numeric),'semantic_agreement':bool(semantic)}


def aggregate(scored):
    by_policy=defaultdict(list);by_fault=defaultdict(lambda:defaultdict(list))
    for row in scored:
        for policy,result in row['policies'].items():
            j=row['scores'][policy];record={**j,'answered':not result['refused'],'expected_action':row['expected_action']}
            by_policy[policy].append(record);by_fault[row['fault']][policy].append(record)
    def counts(records):
        n=len(records);answerable=sum(r['expected_action']=='answer' for r in records);refusal_required=n-answerable
        return {'cases':n,'answer_required':answerable,'refusal_required':refusal_required,
                'answered':sum(r['answered'] for r in records),'correct':sum(r['correct'] for r in records),
                'unsafe_accepts':sum(r['unsafe_accept'] for r in records),'false_refusals':sum(r['false_refusal'] for r in records),
                'correct_answers':sum(r['correct'] and r['expected_action']=='answer' for r in records),
                'correct_refusals':sum(r['correct'] and r['expected_action']=='refuse' for r in records)}
    return {'policies':{p:counts(rs) for p,rs in sorted(by_policy.items())},
            'by_fault':{f:{p:counts(rs) for p,rs in sorted(ps.items())} for f,ps in sorted(by_fault.items())}}
