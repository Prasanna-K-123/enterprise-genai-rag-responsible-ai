# Third-party data and attribution

## FinQA

The FinQA retrieval benchmark uses the upstream development dataset and includes four source-linked example records. The upstream repository is [czyssrs/FinQA](https://github.com/czyssrs/FinQA), pinned to commit `0f16e2867befa6840783e58be38c9efb9229d742` for this evidence release.

The upstream MIT license, including Copyright (c) 2021 Zhiyu Chen, is reproduced unchanged in [LICENSES/FinQA-MIT.txt](LICENSES/FinQA-MIT.txt). This notice attributes the upstream dataset; it does not assert ownership of the financial filings quoted in those records, endorsement by the authors, or a license for this portfolio's original code.

See [the benchmark source](benchmark_finqa_retrieval.py) and [result provenance](results/finqa_retrieval/summary.json) for the exact dataset identity and evaluation scope. FinQA is evaluated as within-report evidence retrieval here, not as an end-to-end question-answering benchmark.

## Original RAG study

The original RAG study below the evidence release in the README uses separate public Accenture reports. Its corpus and evaluation results are distinct from FinQA; the portfolio is not affiliated with or endorsed by Accenture. Source references and limitations remain in the project documentation.
