"""Explicit financial request -> verified capture -> complete answer/refusal.

Example request files are in reference/semantic_contract/examples/. The CLI
accepts no untrusted facts or generated program. It recompiles the explicit
request using the verified captured evidence. Aliases/NLP are outside scope.
"""
import argparse
import json
from pathlib import Path
from src.semantic_contract import answer
from src.semantic_sources import verify


def main():
    p=argparse.ArgumentParser();p.add_argument('request',type=Path);args=p.parse_args()
    try:
        receipt=verify(Path(__file__).resolve().parent/'reference/semantic_contract/sources')
        result=answer(json.loads(args.request.read_text()),receipt['facts'],evidence_sha256=receipt['facts_sha256'])
    except (ValueError,TypeError,KeyError) as error:result={'refused':True,'reason':str(error)}
    print(json.dumps(result,indent=2));return 2 if result['refused'] else 0


if __name__=='__main__':raise SystemExit(main())
