import copy
import json
import math
from benchmark_grounded_answers import bind_proposal, display_correct, execution_correct, model_input, prompt, reference_number, score
from src.grounded_program import clean_context
from tests.test_grounded_program import record, plan


def test_display_rounding_and_explicit_percent_conversion():
    assert display_correct(1214.666666,'number',reference_number('1215'))
    assert not display_correct(1214.4,'number',reference_number('1215'))
    assert display_correct(.117125984,'ratio',reference_number('11.7%'))
    assert not display_correct(.117125984,'number',reference_number('11.7%'))
    assert not display_correct(11.7,'percent',reference_number('11.7'))
    assert reference_number('yes') is None
    assert math.isclose(reference_number('(12.50%)')['value'],-12.5)


def test_upstream_scalar_execution_equality_is_not_loose_display_scoring():
    assert execution_correct(.117125984,.11713)
    assert not execution_correct(.117125984,11.7)
    assert not execution_correct(1214.66666,1215)
    assert not execution_correct(None,0)
    assert not execution_correct(float('nan'),0)


def test_prompt_and_compact_view_ignore_reference_labels():
    r=record();p=prompt(clean_context(r));v=model_input(clean_context(r))
    r['qa'].update(answer='SECRET',program='SECRET',exe_ans=4444,gold_inds={'SECRET':1},model_input=['SECRET'])
    assert prompt(clean_context(r))==p and model_input(clean_context(r))==v
    assert 'SECRET' not in p


def test_matched_output_policies_keep_refusals_in_denominator():
    c=clean_context(record());good=plan(c);bad=plan(c,'(r1c1-r1c3)/r1c3',answer=33.333333)
    for p in [good,bad]:p['refs']=[b['ref'] for b in p.pop('bindings')]
    rows=[]
    for i,proposal in enumerate([good,bad,{}]):
        cc=copy.deepcopy(c);cc['id']=f'ACME/2014/page_{i}.pdf-1'
        rows.append(dict(id=cc['id'],input=cc,proposal=proposal,reference={'answer':'20%','exe_ans':.2},latency_seconds=1,usage={}))
    summary,detail=score(rows)
    assert summary['examples']==3
    assert summary['policies']['contract']['answered']==1
    assert summary['policies']['contract']['execution_hit_rate_all_questions']==1/3
    assert summary['policies']['contract']['display_precision_answered']==1
    assert summary['policies']['addressed']['answered']==2
    assert detail[1]['policies']['contract']['reason']=='period_mismatch'


def test_source_metadata_is_attached_by_engine_not_generated():
    c=clean_context(record());p=plan(c);refs=[b['ref'] for b in p.pop('bindings')];p['refs']=refs
    bound=bind_proposal(p,c)
    assert bound['bindings'][0]=={'ref':'r1c1','row':'revenue','column':'2014'}
    import pytest
    p['refs']=['invented']
    with pytest.raises(ValueError,match='unknown_fact'):bind_proposal(p,c)
