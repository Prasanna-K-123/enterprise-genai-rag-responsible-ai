# Source-addressed financial programs: bounded contracts and a model-policy pilot

This extension addresses a concrete failure in the preserved [128-question negative audit](ANSWER_AUDIT.md): a number can occur in a cited row while belonging to the wrong column, period or calculation. Source occurrence is insufficient. The original audit and its outputs are retained unchanged.

## What the implementation checks

The model proposes a numeric answer, arithmetic expression, output unit and source references. References resolve to **exact table cells or narrative numeral spans**. The engine attaches the original labels and locations; the model does not invent the provenance. Constrained decoding limits reference-list entries and the entity namespace to the supplied report. The expression still has to use all and only those valid references.

Execution allows bounded arithmetic, finite source numbers and conventional constants. Source normalization handles explicit percentages, currency captions, accounting negatives and reconciled duplicated-negative transcriptions. Bare dashes are not zero. Narrative currency scales require explicit local scale language; a table currency caption does not turn unrelated narrative counts into money.

The stricter policy additionally requires a recognized **syntactic question contract**:

- Exactly one source row phrase appears verbatim in the question after punctuation normalization. Aliases and multiple matching measures are refused.
- Each operand has one explicit year, the selected years match the requested years, and each year is used once.
- Supported shapes are an unweighted average, a two-year difference, or percentage growth/decrease with the correct base-period denominator. Explicit reversed `from … to …` direction is preserved.
- Requested units and arithmetic dimensions must agree. Composite, weighted, compound, conditional and quarterly questions are outside this contract.

These checks do **not** establish general natural-language entailment, source authenticity, company-name/subsidiary equivalence, all period granularities, or correct treatment of every financial transcription. Unknown reported units remain unknown. The engine is a bounded research prototype, not a general financial-question answering service.

## Comparison and data boundaries

The protocol, prompt, parser, scorer, tests, model hash and sample-selection algorithm are locked before opening the new evaluation. Training-only preflight exposed oversized repeated paragraph labels and invented copied bindings. The two interrupted training pilots are preserved, and source binding was moved into the engine. Eight fixed training questions were used for final generation-interface preflight; subsequent unit-parser fixes are visible in the locked code and targeted tests. Training outputs are not held-out evidence.

The model is the official **Qwen3-8B Q4_K_M** at the pinned revision/hash in [PROTOCOL.json](../reference/grounded_answer_audit/PROTOCOL.json). It runs locally on CPU through llama-cpp-python 0.3.16. An OpenBLAS 0.3.26 backend was built and made available; operator-level backend dispatch is not separately verified. Non-thinking decoding uses temperature 0.2, top-p 0.8, top-k 20, no presence penalty, seed 20261010 and a 512-token cap. These copying-task settings are disclosed rather than represented as the manufacturer's universal optimum.

FinQA is pinned at `0f16e2867befa6840783e58be38c9efb9229d742`. The neural pilot excludes **every report-page group** represented in the earlier 128 questions. The remaining IDs are sorted by SHA256(`20261010-grounding-v1|` + ID), with the first **64** fixed for evaluation. This is page separation, not company-year separation. Public benchmark exposure in pretraining cannot be excluded.

All 64 questions stay in the denominator, including unsupported tasks, malformed/truncated generations, model refusals and context overflows. Inference receives the question and complete raw supplied report context with source-derived facts; reference answers and programs are absent. This isolates output policies on a shared proposal, **not retrieval quality**:

| Policy | Output rule |
|---|---|
| Direct | Model-reported numeric answer |
| Addressed | Execute the same proposal with exact source references and normalization |
| Contract | Same proposal, additionally enforce the bounded phrase/year/formula/unit contract |
| Deterministic | Construct a program without an LLM from that same explicit contract |

The first three are not independently generated models. The new model, context and sample differ from the old study, so differences between their headline scores cannot isolate a causal improvement from model size or validation.

The same deterministic baseline also receives a **separate census of the complete public test split**, including prior-study pages. That census has no neural context-window budget and is not an untouched held-out model test. Its coverage and every refusal are published.

## Metrics and reproducibility

The primary scalar metric rounds a proposed execution value to five decimal places and compares it to the published `exe_ans`, following the numerical equality in the pinned FinQA evaluator. Explicit percentage rendering is undone first. We do not claim official program-equivalence accuracy, private-leaderboard evaluation, or automatic equivalence of all currency display conventions.

Display agreement uses half the last displayed digit of a parseable reference, with explicit percent/ratio conversion and only a floating-point epsilon. Both all-question and numeric-reference denominators are shown. A coarse rounded annotation is a numeric-agreement criterion, not proof of semantic correctness. Coverage and answered precision must be read together; high precision with sparse answers cannot establish dependable general QA.

The [post-hoc reference diagnostic](REFERENCE_DIAGNOSTICS.md) documents mixed percentage execution conventions and specific program/annotation inconsistencies, together with genuine prototype parser and measure-binding errors. It does not alter the predeclared scorer or remove questions. All reported rates should be read as **published-reference agreement**, not adjudicated semantic correctness.

Paired 95% bootstrap intervals resample report pages (2,000 draws, fixed seed). They are conditional on this fixed local model and sampled public questions. Dependence across pages of the same company-year may remain, and a 64-question pilot has wide uncertainty. Wilson intervals for answered precision are descriptive and do not correct that dependence.

After generation, replay reconstructs each clean context and prompt, checks that the saved proposal matches the raw model text, repeats all decisions/scores, and optionally verifies all inputs/references against the pinned public dataset. Replay is **not neural inference regeneration**.

```bash
pip install -r requirements-controls.txt
python -m pytest -q
python benchmark_answers.py --replay
python benchmark_grounded_answers.py --mode replay --verify-dataset
```

Fresh generation requires the exact GGUF, the optional inference dependency `llama-cpp-python==0.3.16`, and the disclosed CPU backend. The frozen protocol rejects code drift. No failed example is retried or replaced; a technical interruption may continue only the untouched suffix while retaining earlier bytes.

## Prior work and attribution

This is an independent engineering/evaluation extension, not an original claim to have invented table QA or symbolic numerical reasoning. FinQA introduced financial report questions with reasoning programs; TAT-QA combines table/text evidence with symbolic operations. Both precede this project. See the official [FinQA paper](https://aclanthology.org/2021.emnlp-main.300/), [FinQA repository](https://github.com/czyssrs/FinQA), [TAT-QA paper](https://aclanthology.org/2021.acl-long.254/) and [Qwen model card](https://huggingface.co/Qwen/Qwen3-8B-GGUF).

FinQA attribution and its MIT notice remain in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and `LICENSES/FinQA-MIT.txt`. GGUF weights and full report PDFs are not redistributed. API cash expenditure is zero; CPU and electricity cost are not valued.

## Results

The full frozen study is complete: **64 questions / 59 report pages**, with **60 parseable display references** and **61 finite scalar execution references**. All questions, including unsupported types and refusals, remain in the primary denominator. No context overflow occurred. All 64 generations stopped normally; no question was retried or replaced.

| Policy | Answered / 64 | Display matches / 64 | Display matches / 60 numeric references | Execution matches / 64 (primary) | Execution matches / 61 scalar references | Display precision on answered numeric references |
|---|---:|---:|---:|---:|---:|---:|
| Direct model answer | 53/64 | 6/64 | 6/60 | 2/64 | 2/61 | 6/50 (12.0%) |
| Source-addressed execution | 44/64 | 17/64 | 17/60 | 16/64 | 16/61 | 17/41 (41.5%) |
| Strict v1 contract | 2/64 | 1/64 | 1/60 | 1/64 | 1/61 | 1/2 (50.0%) |
| Non-LLM v1 contract | 4/64 | 1/64 | 1/60 | 1/64 | 1/61 | 1/4 (25.0%) |

These are **reference-match counts**. Unsupported unit-bearing display strings can be unparseable even when the answer itself is numeric; the numeric-reference denominators are properties of this fixed scorer, not a semantic adjudication. The source-addressed policy raises agreement on the shared proposals, while retaining many wrong answers. The stricter v1 policy has only 3.13% coverage and accepts an incorrect endpoint-only average. Neither provides dependable general financial QA.

| Paired comparison | Display-match change, percentage points (95% page bootstrap) | Execution-match change, percentage points (95% page bootstrap) |
|---|---:|---:|
| addressed minus direct | +17.19 [+5.00, +29.69] | +21.88 [+11.29, +33.35] |
| contract minus addressed | -25.00 [-36.24, -14.70] | -23.44 [-34.38, -13.11] |
| contract minus direct | -7.81 [-16.13, +0.00] | -1.56 [-7.14, +3.23] |
| deterministic minus contract | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |

The deterministic-minus-strict interval is degenerate because their match indicator vectors are identical in this sample. It is not proof of population or semantic equivalence. Company-year overlap, public-data pretraining exposure and a small fixed-model pilot remain limitations.

Saved per-question latency: median **85.28s**, 95th percentile **149.53s**, summed **5921.71s**. Model input/output token totals are **196,337 / 2,876**. API cash expenditure is zero; CPU/electricity are not priced. These CPU measurements are not service latency guarantees.

Actual outputs SHA256: `75b081a88770c338194ffd94e04d150d0ffe8fb763b821bcdc082cdf7aec1457`. [Full outputs](../reference/grounded_answer_audit/outputs.jsonl) · [Summary](../reference/grounded_answer_audit/summary.json) · [Every policy decision](../reference/grounded_answer_audit/scored_outputs.json). Local replay passed with `--verify-dataset`, checking all input contexts, references, proposals, prompt hashes, full-census decisions and unchanged locked code against the pinned public source. It does not regenerate neural inference.

Concrete examples:

- `GS/2017/page_86.pdf-3`: the model reports an erroneous 170,843,000,000 USDm, but its selected subtraction yields 70,843 USDm under execution. The source-addressed and strict policies match both references. Its columns contain three-month/as-of qualifiers, illustrating that v1 year checks do not establish all reporting-period semantics.
- `APD/2016/page_40.pdf-2`: the model and v1 strict policy omit 2015 from a 2014–2016 average. The strict policy incorrectly accepts 828.9; the separate post-hoc v2 includes all three years.
- `STT/2006/page_95.pdf-1`: source-addressed narrative arithmetic matches the reference, but strict policy refuses ambiguous narrative periods; the v1 non-LLM policy instead binds the unrelated generic `total` table row.
- `GS/2015/page_188.pdf-3`: the model both multiplies its ratio by 100 and requests percent rendering, producing a double-scaled result under addressed execution.
- `BDX/2018/page_106.pdf-3`: the model sums unrelated rows with an unsupported deep expression; the deterministic v1 policy binds row `other`, not the requested total other income. Address occurrence and phrase inclusion cannot establish the intended measure.


The separate complete-public-test deterministic census covers **1,147 questions**: **78 answered / 1,069 refused** (6.80% coverage), **44 display-number matches** and **45 execution-reference matches**. Display-reference precision is 44/78 = 56.41% (descriptive Wilson 95% interval [45.36%, 66.86%]). Sparse coverage and accepted-answer errors rule out dependable general QA. The full census preserves every decision and refusal in [full_test_contract_baseline.json](../reference/grounded_answer_audit/full_test_contract_baseline.json).

A [separate controlled-language v2](CONTROLLED_CONTRACT_V2.md) fixes diagnosed range/formula errors and refuses insufficient measure/unit contexts. It was developed post-hoc and does not change this locked study or supply a new held-out performance result.
