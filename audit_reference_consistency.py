"""Post-hoc reference diagnostics; never changes the locked study's scores.

Checks only whether a published scalar execution result agrees with the
published display number at its shown rounding precision, with a separate
percent-fraction convention. A flag is not a financial adjudication.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import urllib.request

from benchmark_grounded_answers import DATASET_COMMIT, ROOT, TEST_SHA256, finite, reference_number


def diagnose(raw):
    assert hashlib.sha256(raw).hexdigest() == TEST_SHA256, 'Pinned dataset mismatch'
    rows = []
    for record in json.loads(raw):
        qa = record['qa']
        displayed = reference_number(qa['answer'])
        execution = qa['exe_ans']
        kind = 'non_numeric_reference'
        if displayed is not None and finite(execution):
            tolerance = displayed['half_last_displayed_digit'] + 1e-9 * max(1, abs(displayed['value']))
            if abs(execution - displayed['value']) <= tolerance:
                kind = 'execution_matches_display_scale'
            elif displayed['percent'] and abs(execution * 100 - displayed['value']) <= tolerance:
                kind = 'execution_matches_percent_fraction'
            else:
                kind = 'neither_within_display_rounding'
        rows.append(dict(id=record['id'], answer=qa['answer'], exe_ans=execution,
                         kind=kind, reference_program=qa['program'], steps=qa['steps']))
    summary = dict(
        status='POST_HOC_REFERENCE_DIAGNOSTIC_NOT_A_RESCORING',
        examples=len(rows), categories=dict(Counter(row['kind'] for row in rows)),
        dataset_sha256=TEST_SHA256,
        scope='Published display answers and execution values can use different percentage conventions or disagree. These flags do not establish every reference is wrong, adjudicate financial semantics, exclude tasks, or change the frozen primary scores.')
    return dict(summary=summary, per_question=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/finqa_test.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'reference/grounded_answer_audit/reference_consistency_audit.json')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--download', action='store_true', help='Fetch pinned public references in memory; no raw dataset is committed')
    args = parser.parse_args()
    raw = urllib.request.urlopen(f'https://raw.githubusercontent.com/czyssrs/FinQA/{DATASET_COMMIT}/dataset/test.json', timeout=60).read() if args.download else args.dataset.read_bytes()
    diagnostic = diagnose(raw)
    if args.verify:
        assert diagnostic == json.loads(args.output.read_text()), 'Reference diagnostic changed'
        print('REFERENCE_DIAGNOSTIC_REPLAY_PASS (not adjudication or rescoring)')
    else:
        if args.output.exists():
            raise RuntimeError('Diagnostic already exists; use --verify rather than overwrite')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(diagnostic, indent=2) + '\n')
    print(json.dumps(diagnostic['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
