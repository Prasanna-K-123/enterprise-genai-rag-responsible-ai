# Complete-answer controls for explicit financial requests

The new release is a working, reproducible **typed financial calculator and
program validator**, with a registered constructed fault study. It makes
company, concept, observation dates, accession, currency, output scale and
arithmetic meaning part of the answer contract. It does not turn the earlier
unreliable neural systems into dependable free-form question answering.

## What a reviewer can run

```bash
python -m pip install -r requirements-controls.txt
python -m pytest -q
python benchmark_semantic_contract.py --mode replay
python answer_semantic.py reference/semantic_contract/examples/apple_fcf_2025.json
python answer_semantic.py reference/semantic_contract/examples/microsoft_revenue_growth.json
```

The request files are complete explicit selectors. The CLI loads and verifies
the pinned source capture, reconstructs a symbolic program without an LLM,
and returns a number, unit, calculation and every source context. It refuses
unsupported or incomplete requests. It accepts no externally supplied source
packet or model program. There is no claim of general prose/alias parsing,
forecasting, automated investment advice or service deployment.

## Frozen design and source facts

Registration commit **c40bc357c9a92d87618ab86a16e20f2371f08601**, tree
`29a2d0f3fd7849fd12d7539f0df0fe394215da6e`, preceded the new collection and
evaluation. All twelve registered paths match remote Git blobs. No source,
scorer, operation, test or fault-construction change followed registration.
[Protocol](../reference/semantic_contract/PROTOCOL.json) and
[full design](SEMANTIC_CONTRACT_DESIGN.md) are retained.

Apple accession **0000320193-25-000079** and Microsoft accession
**0000950170-25-100235** were selected by the locked latest-common-accession
rule. Four concepts × three annual observation end-years × two issuers give
**24 exact contexts**. All reconcile between original SEC companyconcept USD
records and selected inline-XBRL fact/context/unit nodes. Observation dates
come from the source, not a filing FY label. The original concept histories,
submissions, selected source records and XML fragments are published.

Full filing capture SHA256: Apple
`b0dbcbbd800fd1c819007d63d884a1f8b9a5994486d0b2974a4b5b8a6e6eb80e`,
Microsoft
`9aee86c47d2e3fffc438c671493b709d0e0ba3960917cd5831d145b916eb2c7e`.
[Capture and exact per-source receipts](../reference/semantic_contract/sources/CAPTURE.json).
Full HTML is not redistributed. Both representations describe the same
disclosures; reconciliation is not an independent financial audit.

## Complete comparison

The **172 explicit seed requests** produce **3,498 constructed cases / 25
strata**. There are **368 answer-required** cases and **3,130 refusal-required**
cases. Every case remains in its registered denominator.

| Shared-proposal policy | Correct complete answers / 368 | Correct required refusals / 3,130 | Invalid or wrong answers accepted | False refusals of answer-required cases |
|---|---:|---:|---:|---:|
| Use reported numeral |197|200|3,101|0|
| Source-addressed arithmetic |368|200|2,930|0|
| Full explicit semantic contract |368|3,130|0|0|

The strict contract answers 368 and refuses 3,130; it does not achieve this
result by refusing every input. The separately scored **deterministic planner
answers all 172 supported seed requests correctly**, with complete provenance.
It is the practical interface for this supported task; a neural proposal is
unnecessary. The planner is not required to validate a deliberately faulty
proposal in the shared-proposal table.

The retained fault strata include wrong company, measure and observation
period; wrong output scale, missing addresses, wrong formulas, missing range
members, wrong growth denominator, double-percent conversion, altered source
values/currencies/durations/accessions, ambiguous contexts, and unsupported or
missing request fields. Commuted additions and two equivalent growth formulas
remain accepted. Copying errors in the numeric answer can be repaired by safe
execution. The in-memory capture digest also rejects altered packets before
semantic evaluation; it is a trusted-capture boundary, not a signature or a
source-authenticity system.

One constructed copied-number error of +1.125 USD is within the **predeclared
relative numerical tolerance** on a three-year revenue sum exceeding one
trillion USD, and therefore counts as a reported-answer match. It remains
visible; the scorer was not tightened after seeing it. Source meaning is
checked separately and must still agree. No exact-bit numeric equality claim
follows from this tolerance.

## Why these are conformance results

Programs and their reported numerals are **constructed from known source
arithmetic**, then deliberately perturbed. They are not newly generated LLM
answers. The expected-action, expected-answer and expected-evidence scoring
fields are stripped from policy inputs; the original candidate numeral is
intentionally part of the proposal being tested. Label-field poisoning tests
check that separation. This is not evidence of an LLM answering unseen
financial questions, and cannot be compared numerically with FinQA accuracy.

The constructor computes source-based gold with exact **Fraction** arithmetic;
the runtime executes a bounded **Decimal/AST** implementation. A third scorer
imports neither implementation and checks complete source meaning as well as
numbers. This separation catches a right number with the wrong issuer,
measure, dates, currency or accession. It is an internal automated check,
not external practitioner review or independent candidate mastery.

Many cases reuse the same 24 contexts, and the faults were chosen deliberately.
No population confidence intervals, unknown-fault escape rate, global-best
claim or universal reliability conclusion is justified. Unknown source formats,
broader period granularity, prose intent, reporting-basis comparisons, malicious
replacement of the entire trusted capture and real-user usage remain open.

## Verification and preserved evidence

Local **114 tests pass**, including all prior tests and new adversarial source,
unit, formula, complete-range, injection and scorer-meaning checks. Full replay
verifies every captured source byte hash, selected API record, XML fragment,
constructed input, decision, score, planner answer and deterministic compressed
artifact. Replay is explicit arithmetic, not neural inference regeneration.

Registration CI 38133791207/job114453361020 passes 114 tests but **skips source/
stored-result equality**, because the new capture and outputs were not yet
committed. It must not be reported as a completed-result replay. The legacy
registration run 38133791200/job114453361041 separately replays all existing
financial evidence, including both completed neural studies and the post-hoc
controlled-language census.

The original 883-question retrieval study, 39 registered CCL source rows, 33
calculator reconciliations, 7 refusals, 128-question Qwen3-4B audit, 64-question
Qwen3-8B audit,full-test v1 census and post-hoc 24/1,147 v2 coverage remain
unchanged. Their adverse results and scoring limitations remain visible.

AI-assisted independent portfolio work; not Apple/Microsoft endorsement,
production deployment, external review, adoption or financial advice. Exactly
seven project families remain. Stage One open, Stage Two deferred, applications
and outreach on hold.
