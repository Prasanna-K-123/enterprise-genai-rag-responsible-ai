import copy
import json
import math
import pytest
from src.grounded_program import clean_context, deterministic_contract, execute, parse_scalar, question_contract


def record(question='What was the percentage change in revenue from 2013 to 2014?'):
    return dict(id='ACME/2014/page_10.pdf-1',qa={'question':question},pre_text=[],post_text=[],
                table=[['$ in millions','2014','2013','2012'],['revenue','120','100','90'],['expenses','80','75','70']])


def plan(ctx,expr='(r1c1-r1c2)/r1c2',unit='percent',answer=20):
    import ast
    refs=sorted({n.id for n in ast.walk(ast.parse(expr,mode='eval')) if isinstance(n,ast.Name)})
    return dict(answer=answer,expression=expr,output_unit=unit,entity=ctx['entity'],
                bindings=[{k:ctx['facts'][r][k] for k in ['ref','row','column']} for r in refs])


@pytest.mark.parametrize('raw,expected',[('$ 1,234.5',1234.5),('($ 20)',-20),('-32.0 ( 32.0 )',-32),('.5%',.005),('12.5 %',.125),('100 (a)',100)])
def test_financial_scalar_reconciliation(raw,expected):
    assert parse_scalar(raw)[0]==expected


@pytest.mark.parametrize('raw',['-30 (20)','-', 'n/a','2020-2021','1,2,3','20 30','__import__("os")'])
def test_ambiguous_scalar_is_not_a_number(raw):
    assert parse_scalar(raw) is None


def test_label_leakage_allowlist():
    r=record(); a=clean_context(r)
    r['qa'].update(answer='SECRET_GOLD',exe_ans=9999,program='SECRET_PROGRAM',gold_inds={'SECRET':'x'},model_input='SECRET_MODEL_INPUT')
    r.update(annotation='SECRET',retrieval_labels='SECRET')
    assert clean_context(r)==a and 'SECRET' not in json.dumps(a)


def test_exact_source_cell_execution_and_arithmetic_correction():
    c=clean_context(record()); p=plan(c,answer=999)
    output=execute(p,c,contract_policy=True)
    assert math.isclose(output['answer'],20) and not output['model_numeric_agreement']
    assert output['contract_checked'] and output['provenance'][0]['column']=='2014'


@pytest.mark.parametrize('mutation,reason',[
    (lambda p: p.update(entity='OTHER'),'entity_mismatch'),
    (lambda p: p['bindings'][0].update(column='2013'),'binding_mismatch'),
    (lambda p: p['bindings'][0].update(row='expenses'),'binding_mismatch'),
    (lambda p: p['bindings'].append(copy.deepcopy(p['bindings'][0])),'duplicate_binding'),
    (lambda p: p['bindings'].pop(),'unused_or_missing_binding'),
    (lambda p: p.update(expression='__import__("os").system("echo unsafe")'),'unused_or_missing_binding'),
])
def test_bad_source_metadata_rejected_by_both_policies(mutation,reason):
    c=clean_context(record()); p=plan(c); mutation(p)
    for policy in [False,True]:
        with pytest.raises(ValueError,match=reason): execute(p,c,contract_policy=policy)


@pytest.mark.parametrize('expr,reason',[
    ('(r1c1-r1c3)/r1c3','period_mismatch'),
    ('(r1c1-r1c2)/r1c1','formula_mismatch'),
    ('(r1c2-r1c1)/r1c2','formula_mismatch'),
    ('r1c1-r1c2','formula_mismatch'),
    ('(r1c1-r2c2)/r2c2','measure_mismatch'),
])
def test_same_proposal_ablation_and_contract_errors(expr,reason):
    c=clean_context(record()); p=plan(c,expr)
    assert not execute(p,c,contract_policy=False)['refused']
    with pytest.raises(ValueError,match=reason):execute(p,c,contract_policy=True)


def test_reverse_explicit_year_direction():
    c=clean_context(record('What was the percentage change in revenue from 2014 to 2013?'))
    p=plan(c,'(r1c2-r1c1)/r1c1')
    assert math.isclose(execute(p,c,contract_policy=True)['answer'],-100/6)
    with pytest.raises(ValueError,match='formula_mismatch'):execute(plan(c),c,contract_policy=True)


def test_average_all_periods_and_currency_scale():
    c=clean_context(record('What was the average revenue from 2012 through 2014, in billions?'))
    p=plan(c,'(r1c1+r1c2+r1c3)/3','USDbn')
    assert math.isclose(execute(p,c,contract_policy=True)['answer'],.10333333333333333)
    with pytest.raises(ValueError,match='period_mismatch'):execute(plan(c,'(r1c1+r1c2)/2','USDbn'),c,contract_policy=True)


def test_currency_rescaling_invariance():
    a=record('What was the change in revenue from 2013 to 2014, in billions?'); b=copy.deepcopy(a)
    b['table'][0][0]='$ in billions'
    b['table'][1][1:] = ['.12','.1','.09']
    ca,cb=clean_context(a),clean_context(b)
    ra=execute(plan(ca,'r1c1-r1c2','USDbn'),ca,contract_policy=True)
    rb=execute(plan(cb,'r1c1-r1c2','USDbn'),cb,contract_policy=True)
    assert math.isclose(ra['answer'],rb['answer'])


def test_same_year_wrong_measure_rejected_by_exact_phrase_contract():
    c=clean_context(record()); p=plan(c,'(r2c1-r2c2)/r2c2')
    assert not execute(p,c,contract_policy=False)['refused']
    with pytest.raises(ValueError,match='measure_phrase'): execute(p,c,contract_policy=True)


def test_question_with_multiple_matching_measures_is_not_certified():
    c=clean_context(record('Compared with expenses, what was the percentage change in revenue from 2013 to 2014?'))
    with pytest.raises(ValueError,match='measure_phrase'):execute(plan(c),c,contract_policy=True)


@pytest.mark.parametrize('question',[
    'What was the weighted average revenue from 2013 to 2014?',
    'What was the average annual percentage growth from 2013 to 2014?',
    'What was the percentage point change in margin from 2013 to 2014?',
    'What was the compound growth rate from 2013 to 2014?',
    'What share of costs was revenue in 2014?',
    'What was the percentage change in revenue from 2013 to 2014 if demand doubled?',
    'What was the quarterly change in revenue from 2013 to 2014?',
])
def test_unsupported_intents_are_not_certified(question):
    c=clean_context(record(question)); assert c['contract']['kind']=='unsupported'
    with pytest.raises(ValueError,match='unsupported_question_contract'):execute(plan(c),c,contract_policy=True)


def test_requested_unit_and_ambiguous_period_rejected():
    c=clean_context(record()); p=plan(c,unit='ratio')
    with pytest.raises(ValueError,match='requested_unit_mismatch'):execute(p,c,contract_policy=True)
    c['facts']['r1c1']['periods']=[2014,2013]
    with pytest.raises(ValueError,match='period_ambiguous'):execute(plan(c),c,contract_policy=True)


def test_cross_currency_and_zero_divisor_rejected():
    r=record(); r['table'][1][1]='€ 120'; c=clean_context(r)
    with pytest.raises(ValueError,match='unit_mismatch'):execute(plan(c),c,contract_policy=True)
    r=record();r['table'][1][2]='0';c=clean_context(r)
    with pytest.raises(ValueError,match='zero_divisor'):execute(plan(c),c,contract_policy=True)


def test_non_llm_baseline_uses_the_same_explicit_contract():
    c=clean_context(record())
    assert math.isclose(deterministic_contract(c)['answer'],20)
    assert deterministic_contract(c)['expression']=='(r1c1-r1c2)/r1c2'
    c=clean_context(record('What was the average revenue from 2012 through 2014, in billions?'))
    assert math.isclose(deterministic_contract(c)['answer'],.10333333333333333)
    c=clean_context(record('What was the percentage change in sales from 2013 to 2014?'))
    with pytest.raises(ValueError,match='measure_phrase'):deterministic_contract(c)


def test_narrative_explicit_suffix_units_and_no_caption_currency_leak():
    r=record();r['post_text']=['In 2014, revenue was $31.1 billion; 24 employees attended and the margin was .5%.']
    c=clean_context(r);values=list(c['facts'].values())
    money=next(f for f in values if f['raw'].strip().startswith('$31.1'))
    assert money['dimension']=='currency:USD' and money['value']*money['scale']==31.1e9
    employees=next(f for f in values if f['raw'].strip()=='24')
    assert employees['dimension'].startswith('report:')
    pct=next(f for f in values if f['raw'].strip()=='.5%')
    assert pct['value']==.005 and pct['dimension']=='ratio'
