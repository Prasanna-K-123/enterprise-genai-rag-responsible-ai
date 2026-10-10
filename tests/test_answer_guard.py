import copy
import pytest
from benchmark_answers import clean_input, display_correct, numeric_reference, strict_correct
from src.answer_guard import source_numbers, verify


def test_supported_arithmetic_is_computed_instead_of_trusting_model_value():
    r=verify({'answer':999,'expression':'(120-100)/100*100','sources':['table_1']},{'table_1':'revenue 120; prior revenue 100'})
    assert r['answer']==20


@pytest.mark.parametrize('expr',['__import__("os").system("id")','[1][0]','2**999','True+1','sum([1])','1/0','1/0.00000000000001','(1+2)*999999'])
def test_code_and_unbounded_or_unsupported_arithmetic_refuse(expr):
    with pytest.raises((ValueError,SyntaxError)):
        verify({'answer':0,'expression':expr,'sources':['t']},{'t':'1 2'})


def test_accounting_sign_and_comma_provenance():
    assert source_numbers('$1,200.5; loss (30.2)')=={1200.5,-30.2}
    assert verify({'answer':0,'expression':'-30.2/1200.5','sources':['t']},{'t':'$1,200.5; loss (30.2)'})['answer']==-30.2/1200.5
    with pytest.raises(ValueError):
        verify({'answer':0,'expression':'30.2/1200.5','sources':['t']},{'t':'$1,200.5; loss (30.2)'})


def test_missing_or_nonretrieved_citations_refuse():
    for sources in [[],['made_up'],['t','t']]:
        with pytest.raises(ValueError):verify({'answer':1,'expression':'1','sources':sources},{'t':'1'})


def test_refusal_schema_and_extra_executable_fields():
    assert verify({'answer':None,'expression':None,'sources':[]},{})['refused']
    with pytest.raises(ValueError):verify({'answer':1,'expression':None,'sources':[]},{})
    with pytest.raises(ValueError):verify({'answer':1,'expression':'1','sources':['t'],'python':'x'},{'t':'1'})


def test_gold_and_program_poisoning_cannot_change_inference_input():
    r={'pre_text':['revenue was 120'], 'post_text':[], 'table':[['item','2025'],['revenue','120']], 'qa':{'question':'what is revenue?','answer':'120','exe_ans':120,'program':'1','gold_inds':{'table_1':'120'},'model_input':'leaked'}}
    poisoned=copy.deepcopy(r);poisoned['qa'].update(answer='999999',exe_ans=999999,program='__import__("os")',gold_inds={'fake':'999999'},model_input='999999')
    assert clean_input(r)==clean_input(poisoned)
    assert set(clean_input(r))=={'question','sources'}


def test_display_and_execution_metrics_have_explicit_different_scales():
    assert numeric_reference('24.69%')==24.69
    assert display_correct(24.69136,24.69)
    assert not display_correct(.2469136,24.69)
    assert strict_correct(.24691,.24691)
    assert numeric_reference('yes') is None
