# Evidence review: Financial AI Evidence Systems

Independent portfolio research. Updated 2026-10-09. Development and documentation include AI assistance; the committed executable code, data provenance and test outputs establish the work products. No institutional endorsement or third-party authorship review is claimed.

## Research purpose

Applied AI, retrieval evaluation and reliable numerical tools.

## Published evidence

883 FinQA development questions; 3 retrievers; 33 numerical reconciliations and 7 unsupported-request controls.

## Interpretation boundary

FinQA evaluation measures within-report retrieval, not end-to-end answer accuracy. The original small-model RAG study remains separately documented.

## Review standard

Check the source data and split before interpreting a score. Compare the strongest result with a simple baseline. Inspect failed diagnostics and uncertainty. Reproduce the calculations from the documented environment; distinguish measured findings from simulated or assumed scenarios. The tests cover specific documented invariants and do not establish complete production correctness.

## Next research extension

Evaluate a separately frozen end-to-end financial QA set with answer correctness, numerical execution, semantic citation entailment, abstention and latency/cost. The current 883-question benchmark is a real retrieval baseline, not a completed large-scale generative evaluation.
