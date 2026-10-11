import copy
from decimal import Decimal
import pytest
from semantic_case_builder import exact_answer,seeds,cases,input_only,CONCEPTS
from semantic_independent_score import judge
from src.semantic_contract import sha
from benchmark_semantic_contract import evaluate


def synthetic_capture():
    issuers=[];facts=[]
    for entity in ['0000320193','0000789019']:
        issuer={'entity':entity,'accession':entity+'-25-000001','selected':[]}
        for concept in CONCEPTS:
            for year in [2023,2024,2025]:
                value=(year-2020)*1000000+(CONCEPTS.index(concept)+1)*1000+int(entity)
                ref='f_'+entity+'_'+str(CONCEPTS.index(concept))+'_'+str(year)
                fact={'ref':ref,'entity':entity,'accession':issuer['accession'],'concept':'us-gaap:'+concept,
                      'start':str(year)+'-01-01','end':str(year)+'-12-31','unit':'USD','dimensions':[],
                      'value':str(value),'form':'10-K','filed':'2025-11-01','source_path':concept+'.json',
                      'source_sha256':'1'*64,'filing_url':'https://example.invalid/fixture','filing_sha256':'2'*64,
                      'inline_fact_id':ref,'inline_context_id':ref}
                facts.append(fact);issuer['selected'].append({'ref':ref,'companyconcept_record':{'val':value,'start':fact['start'],'end':fact['end']}})
        issuers.append(issuer)
    return {'issuers':issuers,'facts':facts,'facts_sha256':sha(facts)}


def test_independent_fraction_oracle_known_values():
    assert exact_answer('growth',['100','120'],'percent')=='20'
    assert exact_answer('subtract',['300','200'],'USDm')=='0.0001'
    assert exact_answer('ratio',['20','100'],'ratio')=='0.2'
    assert Decimal(exact_answer('mean',['1','2','6'],'USD'))==3


def test_complete_answer_scoring_rejects_wrong_meaning_with_same_number():
    seed=seeds(synthetic_capture())[0]
    out={'refused':False,'answer':seed['expected_answer'],'entity':seed['request']['entity'],
         'output_unit':seed['request']['output_unit'],'evidence':copy.deepcopy(seed['expected_evidence'])}
    assert judge(seed,out)['correct']
    for field in ['entity','concept','start','end','unit','accession']:
        wrong=copy.deepcopy(out);wrong['evidence'][0][field]='wrong'
        verdict=judge(seed,wrong);assert verdict['numeric_agreement'] and not verdict['correct']


def test_oracle_fields_do_not_enter_inference_or_validation_input():
    c=cases(synthetic_capture())[0];clean=input_only(c)
    for key in ['expected_answer','expected_evidence','expected_action','fault']:
        c[key]='poison'
    assert input_only(c)==clean


def test_registered_fault_suite_on_development_fixtures():
    capture=synthetic_capture();challenge,records,planner,metrics=evaluate(capture)
    assert len(challenge)==3498 and len({c['id'] for c in challenge})==3498
    strict=metrics['policies']['semantic']
    assert strict['answer_required']==368 and strict['refusal_required']==3130
    assert strict['correct']==3498 and strict['unsafe_accepts']==strict['false_refusals']==0
    assert metrics['planner_supported_requests']['correct_complete_answers']==172
    assert metrics['policies']['addressed']['unsafe_accepts']>0
    assert metrics['policies']['reported']['unsafe_accepts']>0
