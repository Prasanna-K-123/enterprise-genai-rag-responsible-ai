"""Post-hoc full-public-split development census; no neural generation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import urllib.request

from benchmark_grounded_answers import DATASET_COMMIT, ROOT, TEST_SHA256, digest, display_correct, execution_correct, reference_number, wilson
from src.controlled_contract_v2 import controlled_contract_v2

OUTPUT = ROOT / 'reference/controlled_contract_v2/development_census.json'


def census(raw):
    assert hashlib.sha256(raw).hexdigest() == TEST_SHA256, 'Pinned public dataset mismatch'
    rows = []
    for record in json.loads(raw):
        try:
            result = controlled_contract_v2(record)
        except (ValueError, TypeError, SyntaxError, KeyError, ZeroDivisionError, StopIteration) as error:
            result = dict(refused=True, reason=str(error))
        reference = reference_number(record['qa']['answer'])
        result['display_correct'] = display_correct(result.get('answer'), result.get('output_unit'), reference)
        result['execution_correct'] = execution_correct(result.get('execution_value'), record['qa']['exe_ans'])
        rows.append(dict(id=record['id'], question=record['qa']['question'], result=result,
                         reference={key:record['qa'][key] for key in ['answer', 'exe_ans']}))
    n = len(rows)
    answered = sum(not row['result']['refused'] for row in rows)
    numeric_answered = sum(not row['result']['refused'] and reference_number(row['reference']['answer']) is not None for row in rows)
    display_hits = sum(row['result']['display_correct'] for row in rows)
    execution_hits = sum(row['result']['execution_correct'] for row in rows)
    summary = dict(status='POST_HOC_DEVELOPMENT_CENSUS_NOT_FRESH_HELD_OUT_PERFORMANCE',
        examples=n, answered=answered, refused=n-answered, coverage=answered/n,
        display_hits=display_hits, execution_hits=execution_hits,
        display_reference_precision_answered=display_hits/numeric_answered if numeric_answered else None,
        display_reference_precision_ci95_wilson=wilson(display_hits, numeric_answered),
        refusal_reasons=dict(sorted(Counter(row['result']['reason'] for row in rows if row['result']['refused']).items())),
        dataset_commit=DATASET_COMMIT, dataset_sha256=TEST_SHA256,
        source_sha256={path:digest(ROOT/path) for path in ['benchmark_controlled_contract_v2.py', 'src/controlled_contract_v2.py', 'src/grounded_program.py', 'benchmark_grounded_answers.py']},
        scope='Version developed after inspecting the v1 full public-test census and selected failure cases. Complete-question grammar, whole-row identity, bounded year ranges and explicit source scales. Every public question retained. No LLM, untouched test, general semantic accuracy, official FinQA score or validated improvement claim.')
    return dict(summary=summary, per_question=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--replay', action='store_true')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/finqa_test.json')
    args = parser.parse_args()
    raw = urllib.request.urlopen(f'https://raw.githubusercontent.com/czyssrs/FinQA/{DATASET_COMMIT}/dataset/test.json', timeout=60).read() if args.download else args.dataset.read_bytes()
    result = census(raw)
    if args.replay:
        assert result == json.loads(OUTPUT.read_text()), 'Development census changed'
        print('V2_DEVELOPMENT_CENSUS_REPLAY_PASS (not fresh held-out performance)')
    else:
        if OUTPUT.exists():
            raise RuntimeError('Development census exists; use --replay rather than overwrite')
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
