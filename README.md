# Enterprise GenAI RAG Assistant — Retrieval, Evaluation & Responsible AI

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
