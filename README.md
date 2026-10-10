# Financial AI Evidence Systems — Retrieval, Numerical Controls & RAG

## Exact financial-source lineage — October 10, 2026

The historical explicit-request calculator now requires reconciled provenance: **39 registered rows / 33 distinct concept-period contexts** match official SEC companyfacts and inline XBRL from two issuer filings. Observation dates, units, concepts and accessions are checked; filing fiscal-year labels are not substituted for observation years. Both current filing HTML hashes differ from prior captures and remain separately recorded. [Source receipt, parser scope and independent collection instructions](docs/FILING_LINEAGE.md).

This verifies consistency across two representations of the same disclosures. It is not an independent financial audit, a new forecast or validation of free-form generated answers.

## Source-addressed programs and their limits

A separately frozen Qwen3-8B pilot compares direct answers, source-addressed arithmetic, bounded phrase/year/unit contracts and a non-LLM baseline on **64 page-disjoint public questions**. Full supplied report context is available; this is a policy experiment rather than retrieval evaluation. [Protocol and evaluation](docs/GROUNDED_ANSWER_AUDIT.md) · [Concrete parser failures and public-reference diagnostics](docs/REFERENCE_DIAGNOSTICS.md). All 64 actual outputs are retained: source-addressed execution matches 16/64 scalar execution references versus 2/64 for direct answers; the strict v1 policy matches only 1/64 and answers 2/64. These are fixed-scorer reference matches, not verified financial accuracy.

The separate deterministic full-test census answers only 78/1,147 questions and matches 44 displayed numbers. Exact source addresses and formula checks still accept wrong measures and misread some period/unit instructions. A [separate controlled-language parser](docs/CONTROLLED_CONTRACT_V2.md) addresses diagnosed range/formula errors and refuses insufficient measure/unit contexts; its evaluation is post-hoc development. General financial answers remain unreliable. The preserved 128-question audit below is unchanged.

## Complete-answer challenge — October 10, 2026

Actual Qwen3-4B Q4_K_M outputs are frozen for **128 public-test questions** selected before inference. The audit compares a model's reported answer with bounded arithmetic execution and source-number checks using the same generation budget. Both policies are unreliable on this task; evidence-row retrieval and numeric occurrence do not prove correct units, periods or semantic entailment. **Experimental free-form answers are not served as dependable results.** [Read the protocol, full outputs, score definitions and failure analysis](docs/ANSWER_AUDIT.md). The separate historical financial calculator retains its explicit entity/year/metric/unit contract.

## Evidence release — 2026-10-09

[883-question FinQA results](results/finqa_retrieval/summary.json) · [Per-question comparisons](results/finqa_retrieval/per_question.csv) · [Numerical controls](results/financial_controls.json) · [CI reproduction](https://github.com/Prasanna-K-123/enterprise-genai-rag-responsible-ai/actions/runs/37966606959) · [Data attribution](THIRD_PARTY_NOTICES.md)

Three retrievers were evaluated on the pinned published development split. TF-IDF recovered all labelled evidence in top three for 61.38%, BM25 for 57.98%, and RRF for 58.89%. The paired RRF-minus-BM25 95% interval is [-0.57, +2.27] percentage points. No hybrid-superiority or end-to-end QA accuracy claim follows. The numerical tool layer separately passes 33 reconciliations and 7 unsupported-request controls.

CPU evidence reproduction: `pip install -r requirements-controls.txt`, `python -m pytest -q`, `python benchmark_financial_controls.py`, and `python benchmark_finqa_retrieval.py --download`. The original 3B-model RAG study below has a different corpus and small evaluation set.

[Research scope and next extension](docs/EVIDENCE_REVIEW.md)

---

Independent portfolio project built over two public Accenture 2025 reports. This repository is **not affiliated with or endorsed by Accenture**.

## Objective

Build an enterprise-style retrieval-augmented generation (RAG) assistant that can:

- retrieve relevant evidence from long-form business documents;
- combine semantic and lexical retrieval;
- answer only from retrieved evidence;
- attach claim-level source references;
- refuse unsupported or adversarial questions;
- evaluate retrieval and generation behavior quantitatively;
- preserve known failure modes instead of tuning them away.

## Corpus

The pipeline downloads and parses two official public reports:

- Accenture Technology Vision 2025
- Accenture 360° Value Report 2025

Final corpus audit:

- **136 pages**
- **365,655 extracted characters**
- **536 overlapping chunks**
- average chunk length: **793 characters**

The source PDFs are downloaded at runtime and are not redistributed in this repository.

## Architecture

```text
Public PDF reports
      ↓
Page-level text extraction (pypdf)
      ↓
Overlapping text chunks
      ↓
Dense embeddings: all-MiniLM-L6-v2
      ↓
Dense ranking + BM25 lexical ranking
      ↓
Reciprocal Rank Fusion (RRF)
      ↓
Top-k evidence
      ↓
Qwen2.5-3B-Instruct
      ↓
Structured claim + source-ID output
      ↓
Python validation + deterministic citation rendering
      ↓
Answer or evidence-based refusal
```

## Retrieval results

A frozen 10-question labelled benchmark was used for the final dense-vs-hybrid comparison.

| Retriever | Hit@1 | Hit@3 | Hit@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Dense embeddings only | 60% | 80% | 90% | 0.725 |
| Hybrid dense + BM25 + RRF | **90%** | **100%** | **100%** | **0.950** |

The hybrid retriever improved **Hit@1 by 30 percentage points** on the same frozen benchmark.

## End-to-end RAG evaluation

The final frozen evaluation used **15 questions**:

- 10 answerable from the corpus;
- 5 unsupported/adversarial questions.

Measured results:

| Metric | Result |
|---|---:|
| Supported-question answer rate | 80% |
| False-refusal rate | 20% |
| Unsupported/adversarial refusal rate | 100% |
| Structured-output validity | 100% |
| Claim citation coverage | 100% |
| Expected-page citation hit among answered supported questions | 100% |
| Invalid generated source-ID rate | 0% |
| Overall correct system behavior | 86.7% |

These metrics test retrieval, refusal behavior, structure, and citation mechanics. They do **not** by themselves prove that every generated claim is semantically entailed by its citation.

## Manual grounding audit

The final answered supported questions produced **13 unique claims**.

Manual claim-level review:

- **11/13 fully supported**
- **2/13 partially supported**
- **0/13 completely unsupported/hallucinated**

The most important semantic error was a query about the “main layers” of a cognitive digital brain: the generator returned *levels of scale* (individuals, businesses, industries, governments) instead of the architecture layers described elsewhere on the page (Knowledge, Models, Agents, Architecture).

A second partial-support case involved a sustainability-committee claim that extended beyond the text visible in the cited chunk, exposing a chunk-boundary/citation-granularity limitation.

## Responsible AI controls

The system includes:

- evidence-only generation instructions;
- a retrieval-confidence refusal gate;
- an LLM evidence check for questions that pass retrieval but remain unsupported;
- structured JSON-style claim/source output;
- source-ID validation;
- deterministic citation rendering in Python;
- adversarial prompts that explicitly ask the model to ignore the supplied evidence;
- explicit reporting of false refusals and semantic grounding errors.

The design intentionally favors **conservative abstention over unsupported answers**, which produced a measurable trade-off: 100% refusal on the five unsupported/adversarial questions, but a 20% false-refusal rate on answerable questions.

## Error analysis

Two answerable questions were refused in the final run:

1. a question about emissions/cost impact of generative AI;
2. a question about fiscal-2025 generative-AI revenue and bookings.

Both had relevant evidence in the corpus. This indicates a **generation/evidence-acceptance failure rather than a retrieval failure**.

The project therefore separates evaluation into:

- retrieval quality;
- answer/refusal behavior;
- citation mechanics;
- manual semantic grounding.

## Tech stack

- Python
- Pandas / NumPy
- pypdf
- Sentence Transformers
- `sentence-transformers/all-MiniLM-L6-v2`
- BM25 (`rank-bm25`)
- Reciprocal Rank Fusion
- Hugging Face Transformers
- `Qwen/Qwen2.5-3B-Instruct`
- Google Colab / T4 GPU

## Repository structure

```text
.
├── README.md
├── enterprise_genai_rag_responsible_ai.ipynb
├── requirements.txt
├── src/
│   └── rag_pipeline.py
└── results/
    ├── final_metrics.csv
    ├── manual_grounding_review.csv
    └── manual_claim_summary.csv
```

## Reproduce

1. Open `enterprise_genai_rag_responsible_ai.ipynb` in Google Colab.
2. Use a T4 GPU for the generation stage if available.
3. Run the cells from top to bottom. The notebook clones this repository, installs dependencies, and executes the reproducible pipeline in `src/rag_pipeline.py`.
4. The pipeline downloads the two public reports, builds the corpus, evaluates dense and hybrid retrieval, loads the 3B generator, and runs the frozen evaluation.
5. Review generated outputs manually before making any claim about semantic grounding.

Because models and package versions can evolve, small numerical or wording differences are possible on future reruns.

## What this project demonstrates

- document ingestion and chunking;
- dense semantic retrieval;
- lexical retrieval with BM25;
- rank fusion;
- retrieval evaluation with Hit@k and MRR;
- local open-model generation;
- structured output validation;
- refusal/abstention design;
- prompt-injection resistance tests;
- claim-level citation mechanics;
- manual grounding review;
- error analysis and Responsible AI trade-offs.
