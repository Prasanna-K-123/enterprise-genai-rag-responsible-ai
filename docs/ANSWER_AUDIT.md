# Complete-answer financial QA challenge

This is a completed **negative reliability study**, not a production answering service, SOTA claim, private leaderboard submission or practitioner certification. It extends the 883-question development retrieval benchmark with actual generated answers.

## Frozen design and inference boundary

Before downloading/loading the public test split, [PROTOCOL.json](../reference/answer_audit/PROTOCOL.json) froze a **128-question** subset: the first 128 IDs after sorting SHA256(`20261010-full-answer-v1|` + ID). All selected questions were run, including unsupported/categorical tasks and refusals. No prompt/model/threshold revision based on test outputs was made. The protocol's custom display-score wording is interpreted below with its important rounding/scale limits; it is not an official FinQA score.

Pinned FinQA commit `0f16e2867befa6840783e58be38c9efb9229d742`, test Git blob `59958c7c3bb3b21f4dff6bc912a0fe0ae710aee0`; corpus SHA256 `831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc`. Author/source attribution and MIT notice are retained in `THIRD_PARTY_NOTICES.md` and `LICENSES/FinQA-MIT.txt`.

Inference receives **question plus three TF-IDF-ranked raw report rows**, preserving table headers. `program`, `program_re`, gold answers, `gold_inds`, `model_input`, annotations and stored upstream retrieval outputs do not enter the generation input. Label/program-poisoning tests verify that changing those fields cannot change the constructed inference input. References are attached only by the scorer after model inference.

Generator: official [Qwen/Qwen3-4B-GGUF](https://huggingface.co/Qwen/Qwen3-4B-GGUF), revision `bc640142c66e1fdd12af0bd68f40445458f3869b`, `Qwen3-4B-Q4_K_M.gguf`, SHA256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`. Local `llama-cpp-python 0.3.16`, CPU-only, six threads, 8,192 context, greedy temperature 0, seed 20261010, 512-token cap, explicit non-thinking prompt and a JSON grammar. Output schema: numeric answer, arithmetic expression and source IDs. Exact prompt/code hashes and task IDs are in [generation_metadata.json](../reference/answer_audit/generation_metadata.json). Model training contamination of this public task is unknown. Weights are fetched from the original publisher rather than redistributed.

## Matched generation budget, two output policies

1. **Direct:** use the model's reported numeric answer.
2. **Arithmetic guard:** execute its expression through a bounded AST supporting only literals, +, -, *, /; reject arbitrary code, nonfinite/extreme values, excessive complexity, missing/repeated/unretrieved citations and unsupported numeric literals. Conventional constants are an explicit whitelist.

Both policies use **the same one generation per question**, not two independently trained models. The guard checks syntactic safety and numeric occurrence in cited rows. It does not prove that a cited number is the right entity, fiscal year, denominator, unit or financial meaning. It does not infer a percentage conversion or compute an omitted average. A correct-looking citation is insufficient.

## Complete results

| Measure | Direct numeric output | Arithmetic guard |
|---|---:|---:|
| Questions attempted |128|128|
| Answered |111|96|
| Coverage |86.72%|75.00%|
| Custom display-scale matches,122 numeric references |15|22|
| Rounded-five-decimal match to numeric `exe_ans`, all 128 tasks |9|26|
| Answered with every labelled gold row cited |76|68|

All gold rows were retrieved for **87/128** questions. The guard refused 17 model refusals plus 15 invalid proposals (10 unsupported numeric operands, 3 disallowed AST structures, 1 invalid syntax, 1 inconsistent refusal). Source coverage is not full semantic entailment.

The custom display diagnostic removes commas/currency symbols and recognizes single numeric reference strings; 122/128 references are recognized. Tolerance is `math.isclose(rel_tol=1e-5,abs_tol=0.0100001)`. This deliberately fixed diagnostic does **not correctly reproduce every reference's coarser display-rounding convention**, and a percentage display may be 100 times a reference program's fraction. It must not be advertised as human-reviewed answer correctness or official execution accuracy. 82/122 numeric references differ between their display value and stored execution value under this diagnostic; many reflect legitimate scale/rounding conventions, not wrong annotations.

The direct-to-guard change in this custom diagnostic is **+5.74 percentage points**, paired 2000-question-bootstrap interval **[-0.82,13.11]pp**; it includes zero. The resampling treats questions as exchangeable and does not establish report-cluster or future-report uncertainty. No dependable-answer or general superiority claim follows.

The five-decimal execution-value match is a separate transparent numeric comparison to `exe_ans`; it does not run the upstream program-equivalence evaluator and is not an official leaderboard result. Unsupported categorical tasks remain in its128 denominator. Comparing requested percent display with fraction-valued execution references creates an important interpretation limit for this comparison too.

## Inspectable failures

- `AWK/2017/page_148.pdf-2`: model reports 11.76 but expression `(1135-1016)/1016` executes to 0.1171259843. Numeric arithmetic is supported; requested percentage display is not rendered correctly. Reference display 11.7%, execution 0.11713. This illustrates the need for explicit typed quantities and a rendering contract.
- `C/2008/page_65.pdf-3`: correct row citation still selects 618.3 and 542.9 from the wrong loan column; the reference uses different totals. Occurrence in the correct row does not establish the correct business measure.
- `LMT/2016/page_49.pdf-4`: model copies 1282 for a three-year average rather than computing `(1018+1282+1344)/3`. The source contains all operands, but the semantics are wrong. Reference display 1215 is a rounded form of execution 1214.66667; this also demonstrates why the fixed display tolerance is not a universal correctness score.

These are the **first three selected records**, not hand-picked successes. [Every raw output, retrieved input and scoring reference](../reference/answer_audit/outputs.jsonl) and [every guard/scoring decision](../reference/answer_audit/scored_outputs.json) remain public. The complete negative study stays frozen; a future unit/period-aware model must use a newly frozen evaluation and preserve this development record.

## Runtime and cost

Median generation **5.51s**, 95th percentile **9.52s**, total **757.66s**; 54,318 prompt and 4,040 completion tokens. CPU runtime shared the environment with other work; these are measured local observations, not a service latency guarantee. No paid API was used: cash API spend $0, with compute/electricity cost unvalued.

## Reproduce and validate

```bash
python -m pip install -r requirements-controls.txt
python -m pytest -q
python benchmark_answers.py --replay
```

CI replays the **real frozen outputs**, re-executes guards and recomputes the full score table/hash. It does **not** re-run language generation or certify identical decoding across hardware. Local full suite: 17 passed, including code-injection/bounded arithmetic, accounting signs, unknown citations, exact schema and reference-leakage controls.

To reproduce generation separately, install `llama-cpp-python==0.3.16`, fetch the pinned original model and verify its hash, then run `benchmark_answers.py --download --model <local-model-path>` from a clean reference directory with the frozen outputs backed up. The script refuses to overwrite an existing generation record. Runtime and generation may vary by hardware/backend; exact replay of the existing artifact is the CI contract.

## Product boundary

The recruiter demo exposes **a bounded historical financial calculator** with explicit company/year/metric/unit inputs and reproducible statement values. Experimental FinQA free-form outputs are displayed only as a failure/research inspector. The successful 33 numeric reconciliations and seven refusal controls of the separate calculator do not establish arbitrary natural-language financial QA. This portfolio used AI assistance. External review and real-user adoption have not been obtained.
