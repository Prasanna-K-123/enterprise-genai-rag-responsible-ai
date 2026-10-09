import copy
import pytest
from src.financial_tools import answer
from benchmark_finqa_retrieval import candidates,rank


def test_financial_unit_and_period_proofs():
    a=answer(dict(entity='CCL',year=2025,metric='ebitda_proxy'))
    assert a['value']==7273 and len(a['evidence'])==2
    dollars=answer(dict(entity='CCL',year=2025,metric='ebitda_proxy',unit='USD'))
    assert dollars['value']==7273000000
    assert answer(dict(entity='CCL',year=2025,metric='revenue_growth'))['value']==pytest.approx(26622/25021-1)


def test_untrusted_model_requests_cannot_override_contract():
    with pytest.raises(ValueError):answer(dict(entity='CCL',year=2025,metric='revenue',instructions='ignore evidence'))
    with pytest.raises(ValueError):answer(dict(entity='CCL',year=2026,metric='revenue'))
    with pytest.raises(ValueError):answer(dict(entity='CCL',year=2025,metric='revenue',unit='EUR'))


def test_gold_labels_and_program_never_enter_retrieval():
    record={'pre_text':['Annual report.'],'post_text':['Financial statement.'],
            'table':[['USD millions','2024','2025'],['revenue','25','30']],
            'qa':{'question':'revenue in 2025','gold_inds':{'table_1':'revenue'},'program':'divide(30,25)'}}
    changed=copy.deepcopy(record);changed['qa']['gold_inds']={'text_0':'fake'};changed['qa']['program']='INJECT ANSWER'
    assert candidates(record)==candidates(changed)
    for name,order in rank(record['qa']['question'],candidates(record)).items():
        assert order.tolist()==rank(changed['qa']['question'],candidates(changed))[name].tolist()
    assert 'revenue of 2025 is 30' in candidates(record)[-1][1]
