"""Registered finite financial-answer contract challenge; no neural generation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
from collections import Counter
from src.semantic_contract import execute,answer,sha
from src.semantic_sources import capture,verify
from semantic_case_builder import cases,seeds,input_only,changed_facts
from semantic_independent_score import judge,aggregate

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reference/semantic_contract'
LOCKED=['src/semantic_contract.py','src/semantic_sources.py','semantic_case_builder.py',
        'semantic_independent_score.py','benchmark_semantic_contract.py','answer_semantic.py',
        'tests/test_semantic_contract.py','tests/test_semantic_challenge.py','requirements-controls.txt']


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def packed(value):return gzip.compress((json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode(),mtime=0)


def check_lock():
    protocol=json.loads((OUT/'PROTOCOL.json').read_text())
    for path,expected in protocol['locked_sha256'].items():
        if digest(ROOT/path)!=expected:raise ValueError('registered_code_drift:'+path)
    return protocol


def evaluate(capture_record):
    challenge=cases(capture_record);records=[];facts=capture_record['facts'];seal=capture_record['facts_sha256']
    for case in challenge:
        clean=input_only(case);altered=changed_facts(clean,facts);policies={}
        for policy in ['reported','addressed','semantic']:
            try:result=execute(clean['proposal'],clean['request'],altered,policy=policy,evidence_sha256=seal)
            except (ValueError,TypeError,KeyError,ArithmeticError) as error:result={'refused':True,'reason':str(error),'policy':policy}
            policies[policy]=result
        records.append({'id':case['id'],'fault':case['fault'],'expected_action':case['expected_action'],
                        'input_sha256':sha(clean),'policies':policies,
                        'scores':{p:judge(case,r) for p,r in policies.items()}})
    planner=[]
    for seed in seeds(capture_record):
        result=answer(input_only(seed)['request'],facts,evidence_sha256=seal)
        planner.append({'seed_id':seed['seed_id'],'result':result,'score':judge(seed,result)})
    metrics=aggregate(records);metrics['planner_supported_requests']={'requests':len(planner),'answered':sum(not r['result']['refused'] for r in planner),'correct_complete_answers':sum(r['score']['correct'] for r in planner)}
    metrics['source']={'issuers':len(capture_record['issuers']),'annual_contexts':len(facts),'facts_sha256':seal}
    metrics['counts']={'challenge_cases':len(challenge),'seed_requests':len(planner),'fault_types':len(set(c['fault'] for c in challenge)),
                      'cases_by_fault':dict(sorted(Counter(c['fault'] for c in challenge).items()))}
    metrics['scope']='Constructed explicit-request/proposal fault suite; complete-answer checks against Fraction-derived source labels. No neural generation, held-out natural-language accuracy, external review or population confidence interval.'
    return challenge,records,planner,metrics


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['capture','run','replay'],required=True);parser.add_argument('--cache',type=Path);args=parser.parse_args()
    check_lock()
    if args.mode=='capture':
        if not args.cache:parser.error('--cache required for non-redistributed full HTML')
        record=capture(OUT/'sources',args.cache);print(json.dumps({'captured_contexts':len(record['facts']),'facts_sha256':record['facts_sha256']}));return
    if not (OUT/'sources/CAPTURE.json').exists():
        if args.mode=='replay':print('SEMANTIC_REFERENCE_CHECK_SKIPPED=source/results not committed');return
        raise ValueError('capture_missing')
    record=verify(OUT/'sources');challenge,results,planner,metrics=evaluate(record)
    objects={'cases.json.gz':challenge,'scored_outputs.json.gz':results,'planner_outputs.json.gz':planner}
    if args.mode=='run':
        if (OUT/'SUMMARY.json').exists():raise ValueError('frozen_results_exist')
        for name,obj in objects.items():(OUT/name).write_bytes(packed(obj))
        summary={'metrics':metrics,'artifact_sha256':{name:digest(OUT/name) for name in objects},'protocol_sha256':digest(OUT/'PROTOCOL.json'),
                 'capture_sha256':digest(OUT/'sources/CAPTURE.json'),'runtime':{'python':platform.python_version(),'inference':'none','api_cash_spend':0,'compute_cost':'not valued'}}
        (OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    summary=json.loads((OUT/'SUMMARY.json').read_text())
    if summary['metrics']!=metrics or summary['protocol_sha256']!=digest(OUT/'PROTOCOL.json') or summary['capture_sha256']!=digest(OUT/'sources/CAPTURE.json'):raise ValueError('summary_replay_mismatch')
    for name,obj in objects.items():
        if digest(OUT/name)!=summary['artifact_sha256'][name] or (OUT/name).read_bytes()!=packed(obj):raise ValueError('full_artifact_replay_mismatch:'+name)
    print('SEMANTIC_REPLAY_JSON='+json.dumps({'frozen_reference_equal':True,'metrics':metrics},sort_keys=True))


if __name__=='__main__':main()
