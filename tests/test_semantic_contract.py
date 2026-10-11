import copy
from decimal import Decimal
import pytest
from src.semantic_contract import answer,execute,propose,sha
from src.semantic_sources import inline_nodes,select_accession,CONCEPTS


def fixture():
    facts=[]
    for year,value in [(2023,'100000000'),(2024,'120000000'),(2025,'180000000')]:
        facts.append({'ref':'rev'+str(year),'entity':'0000320193','accession':'0000320193-25-000001',
                      'concept':'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
                      'start':str(year)+'-01-01','end':str(year)+'-12-31','unit':'USD',
                      'dimensions':[],'value':value,'form':'10-K'})
    request={'entity':'0000320193','accession':'0000320193-25-000001','operation':'growth',
             'operands':[{k:f[k] for k in ['concept','start','end']} for f in facts[:2]],'output_unit':'percent'}
    return request,facts


def test_exact_period_growth_and_explicit_percent_rendering():
    request,facts=fixture();out=answer(request,facts,evidence_sha256=sha(facts))
    assert not out['refused'] and Decimal(out['answer'])==20
    assert [f['end'] for f in out['evidence']]==['2023-12-31','2024-12-31']
    request['operands'].reverse();out=answer(request,facts,evidence_sha256=sha(facts))
    assert Decimal(out['answer'])==Decimal('-16.66666666666666666666666666666666666667')


@pytest.mark.parametrize('unit,expected',[('USD','100000000'),('USDk','100000'),('USDm','100'),('USDbn','.1')])
def test_source_scale_never_inferred_from_output_unit(unit,expected):
    request,facts=fixture();request.update(operation='lookup',operands=request['operands'][:1],output_unit=unit)
    assert Decimal(answer(request,facts,evidence_sha256=sha(facts))['answer'])==Decimal(expected)


def test_mean_includes_every_observation_year_and_commutation():
    request,facts=fixture();request.update(operation='mean',operands=[{k:f[k] for k in ['concept','start','end']} for f in facts],output_unit='USDm')
    proposal=propose(request,facts);proposal['expression']='(rev2025+rev2023+rev2024)/3'
    out=execute(proposal,request,facts,evidence_sha256=sha(facts))
    assert Decimal(out['answer'])==Decimal('133.3333333333333333333333333333333333333')
    proposal['expression']='(rev2023+rev2025)/2';proposal['refs']=['rev2023','rev2025']
    with pytest.raises(ValueError):execute(proposal,request,facts,evidence_sha256=sha(facts))
    request['operands']=[request['operands'][0],request['operands'][2]]
    assert answer(request,facts,evidence_sha256=sha(facts))['refused']


@pytest.mark.parametrize('field,value',[('entity','0000789019'),('accession','0000320193-24-000001'),('output_unit','ratio')])
def test_wrong_request_binding_refused(field,value):
    request,facts=fixture();p=propose(request,facts)
    if field=='accession':request[field]=value
    else:p[field]=value
    with pytest.raises(ValueError):execute(p,request,facts,evidence_sha256=sha(facts))


@pytest.mark.parametrize('expression',['(rev2024-rev2023)/rev2024','((rev2024-rev2023)/rev2023)*100','__import__("os").getcwd()','rev2023**2','[rev2023][0]','rev2023/rev2023+1','float("nan")'])
def test_wrong_formulas_and_code_injection_refused(expression):
    request,facts=fixture();p=propose(request,facts);p['expression']=expression
    with pytest.raises(ValueError):execute(p,request,facts,evidence_sha256=sha(facts))


def test_equivalent_growth_form_and_numeric_repair():
    request,facts=fixture();p=propose(request,facts);p.update(expression='rev2024/rev2023-1',answer='999')
    out=execute(p,request,facts,evidence_sha256=sha(facts))
    assert Decimal(out['answer'])==20 and not out['reported_numeric_agreement']


@pytest.mark.parametrize('field,value',[('unit','EUR'),('dimensions',['segment']),('form','10-Q'),('start','2023-07-01'),('value','NaN')])
def test_changed_capture_and_context_fail_closed(field,value):
    request,facts=fixture();seal=sha(facts);p=propose(request,facts);facts[0][field]=value
    with pytest.raises(ValueError,match='changed_source_capture'):execute(p,request,facts,evidence_sha256=seal)
    if field!='start':assert answer(request,facts,evidence_sha256=sha(facts))['refused']


def test_missing_duplicate_nonpositive_and_unverified_source():
    request,facts=fixture();p=propose(request,facts)
    with pytest.raises(ValueError,match='unverified'):execute(p,request,facts)
    duplicate=copy.deepcopy(facts[0]);duplicate['ref']='duplicate';facts.append(duplicate)
    assert answer(request,facts,evidence_sha256=sha(facts))['refused']
    facts.pop();facts[0]['value']='0';assert answer(request,facts,evidence_sha256=sha(facts))['refused']
    facts[0]['value']='-1';assert answer(request,facts,evidence_sha256=sha(facts))['refused']


def test_inline_currency_entity_period_and_numeric_normalization():
    xml=b'''<root xmlns:x="http://www.xbrl.org/2003/instance" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><x:context id="c"><x:entity><x:identifier scheme="http://www.sec.gov/CIK">0000320193</x:identifier></x:entity><x:period><x:startDate>2023-01-01</x:startDate><x:endDate>2023-12-31</x:endDate></x:period></x:context><x:unit id="u"><x:measure>iso4217:USD</x:measure></x:unit><ix:nonFraction id="n" name="us-gaap:OperatingIncomeLoss" contextRef="c" unitRef="u" format="ixt:num-dot-decimal" scale="6" decimals="-6" sign="-">1,234</ix:nonFraction></root>'''
    facts=inline_nodes(xml,'0000320193');assert len(facts)==1 and Decimal(facts[0]['value'])==-1234000000
    assert inline_nodes(xml,'0000789019')==[]
    assert inline_nodes(xml.replace(b'iso4217:USD',b'iso4217:EUR'),'0000320193')==[]


def test_latest_common_accession_uses_observation_dates_not_filing_fy():
    histories={c:{'units':{'USD':[{'form':'10-K','filed':'2025-11-01','start':str(y)+'-01-01','end':str(y)+'-12-31','fy':2025,'accn':'0000320193-25-000001','val':y} for y in [2023,2024,2025]]}} for c in CONCEPTS}
    accession,selected=select_accession(histories)
    assert accession=='0000320193-25-000001' and selected[(CONCEPTS[0],2023)]['end']=='2023-12-31'
    histories[CONCEPTS[0]]['units']['USD'].append({**histories[CONCEPTS[0]]['units']['USD'][0],'val':999})
    with pytest.raises(ValueError):select_accession(histories)
