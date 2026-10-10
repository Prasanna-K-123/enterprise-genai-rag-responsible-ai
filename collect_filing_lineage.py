"""Collect three official SEC sources for explicit historical reconciliation.

Sequential public-data GETs; no API key, new financial prediction or refresh of
the historical register. Supply your own descriptive User-Agent/contact.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import urllib.request
from src.filing_lineage import ROOT, URL


def main():
    p=argparse.ArgumentParser();p.add_argument('--user-agent',required=True);p.add_argument('--directory',type=Path,default=ROOT/'data/sec_refresh');a=p.parse_args()
    if len(a.user_agent.strip())<10:raise ValueError('Supply a descriptive User-Agent with contact details')
    a.directory.mkdir(parents=True,exist_ok=False)
    register=list(csv.DictReader((ROOT/'reference/financial_tools/source_register.csv').open()))
    urls=[URL]+sorted({r['source_url'] for r in register if r['source_type']=='sec_filing_table'})
    observations=[]
    for url in urls:
        if url!=URL and not url.startswith('https://www.sec.gov/Archives/edgar/data/815097/'):
            raise ValueError('Unexpected source origin or issuer')
        req=urllib.request.Request(url,headers={'User-Agent':a.user_agent,'Accept-Encoding':'identity'})
        with urllib.request.urlopen(req,timeout=60) as response:raw=response.read()
        target=a.directory/url.rsplit('/',1)[-1];target.write_bytes(raw)
        observations.append(dict(url=url,file=target.name,size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        print('SOURCE_CAPTURED',target.name,len(raw),flush=True)
    (a.directory/'capture_manifest.json').write_text(json.dumps(observations,indent=2)+'\n')


if __name__=='__main__':main()
