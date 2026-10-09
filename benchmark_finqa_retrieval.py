"""Reproducible financial evidence retrieval baseline on the FinQA dev split.

Ranks sentences and table rows within each supplied report. Gold answer,
program and evidence labels never enter candidate construction or scoring.
This is retrieval evaluation, not end-to-end financial QA accuracy.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,re,urllib.request
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT=Path(__file__).resolve().parent
SOURCE_COMMIT='0f16e2867befa6840783e58be38c9efb9229d742'
SOURCE_BLOB='970f239f591c782b17df420c0d343b780737f3da'
SOURCE_URL=f'https://raw.githubusercontent.com/czyssrs/FinQA/{SOURCE_COMMIT}/dataset/dev.json'


def tokens(text): return re.findall(r'[a-z0-9]+',str(text).lower())


def candidates(record):
    items=[(f'text_{i}',str(text)) for i,text in enumerate(record['pre_text']+record['post_text'])]
    table=record['table']
    if table:
        header=table[0]
        for i,row in enumerate(table):
            # Header/row pairs preserve year association and contain no labels.
            words=[str(header[0])] if header and header[0] else []
            for column,value in zip(header[1:],row[1:]):
                words.append(f'the {row[0]} of {column} is {value}')
            items.append((f'table_{i}',' ; '.join(words)))
    return items


def rank(query,items):
    documents=[text for _,text in items]
    vectorizer=TfidfVectorizer(tokenizer=tokens,token_pattern=None,lowercase=False)
    vectors=vectorizer.fit_transform(documents)
    tfidf=(vectors@vectorizer.transform([query]).T).toarray().ravel()
    counts=[Counter(tokens(text)) for text in documents]
    n=len(counts)
    lengths=np.array([sum(c.values()) for c in counts],dtype=float)
    mean_length=max(float(lengths.mean()),1)
    bm25=np.zeros(n)
    for term in set(tokens(query)):
        frequency=np.array([c.get(term,0) for c in counts],dtype=float)
        df=np.count_nonzero(frequency)
        idf=np.log(1+(n-df+.5)/(df+.5))
        denominator=frequency+1.5*(1-.75+.75*lengths/mean_length)
        bm25+=idf*frequency*2.5/np.maximum(denominator,1e-12)
    order_a=np.argsort(-tfidf,kind='stable')
    order_b=np.argsort(-bm25,kind='stable')
    ranks_a=np.empty(n,int); ranks_a[order_a]=np.arange(1,n+1)
    ranks_b=np.empty(n,int); ranks_b[order_b]=np.arange(1,n+1)
    fusion=1/(60+ranks_a)+1/(60+ranks_b)
    return dict(tfidf=order_a,bm25=order_b,rrf=np.argsort(-fusion,kind='stable'))


def evaluate(records):
    rows=[]
    for record in records:
        items=candidates(record)
        gold=set(record['qa']['gold_inds'])
        if not gold or not gold.issubset({key for key,_ in items}):
            raise ValueError(f'Invalid evidence mapping: {record.get("id")}')
        ranking=rank(record['qa']['question'],items)
        for model,order in ranking.items():
            ids=[items[i][0] for i in order]
            position=min(i+1 for i,key in enumerate(ids) if key in gold)
            rows.append(dict(id=record['id'],retriever=model,candidates=len(items),gold_rows=len(gold),
                             hit_at_1=int(position<=1),hit_at_3=int(position<=3),
                             recall_at_3=len(set(ids[:3])&gold)/len(gold),
                             all_evidence_at_3=int(gold.issubset(ids[:3])),
                             mrr_at_10=1/position if position<=10 else 0))
    return pd.DataFrame(rows)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=ROOT/'data/finqa_dev.json')
    parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    if args.download:
        args.data.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(SOURCE_URL,timeout=90) as response: raw=response.read()
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual!=SOURCE_BLOB: raise ValueError('Pinned FinQA Git blob identity mismatch')
        args.data.write_bytes(raw)
    raw=args.data.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=SOURCE_BLOB:
        raise ValueError('Use the exact pinned development split')
    records=json.loads(raw)
    result=evaluate(records)
    means=result.groupby('retriever')[['hit_at_1','hit_at_3','recall_at_3','all_evidence_at_3','mrr_at_10']].mean()
    # Paired examples, not an independent-proportions confidence interval.
    pivot=result.pivot(index='id',columns='retriever',values='all_evidence_at_3')
    difference=(pivot.rrf-pivot.bm25).to_numpy()
    rng=np.random.default_rng(20261009)
    bootstrap=[float(rng.choice(difference,len(difference),replace=True).mean()) for _ in range(2000)]
    summary=dict(split='FinQA published development split',examples=len(records),source_commit=SOURCE_COMMIT,
                 source_git_blob=SOURCE_BLOB,data_sha256=hashlib.sha256(raw).hexdigest(),
                 results=means.to_dict(orient='index'),
                 rrf_minus_bm25_all_evidence_at_3=float(difference.mean()),
                 paired_difference_ci95=np.quantile(bootstrap,[.025,.975]).tolist(),
                 scope='Within-report evidence retrieval only; no generated answer, program accuracy or out-of-sample market claim.',
                 no_parameter_search=True)
    out=ROOT/'results/finqa_retrieval';out.mkdir(parents=True,exist_ok=True)
    result.to_csv(out/'per_question.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # Small, inspectable dataset slice for offline integration tests/demos.
    (out/'example_records.json').write_text(json.dumps(records[:4],indent=2)+'\n')
    print('FINQA_REFERENCE_JSON='+json.dumps(summary))


if __name__=='__main__': main()
