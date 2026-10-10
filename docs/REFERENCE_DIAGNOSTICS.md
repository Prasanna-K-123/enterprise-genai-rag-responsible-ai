# Published-reference and prototype-failure diagnostics

This is **post-hoc diagnosis, not a rescoring rule**. The locked financial-answer pilot retains every selected question and its original metrics. No flagged case is excluded, repaired in place, retried or used to tune the frozen code.

## Public annotations use different scalar conventions

On all 1,147 pinned public FinQA test records, comparing the published `exe_ans` to the displayed answer at half the last shown digit gives:

| Relationship | Records |
|---|---:|
| Matches the displayed number directly | 411 |
| Matches after rendering an explicit percentage fraction × 100 | 575 |
| Neither comparison matches within displayed rounding | 116 |
| Display or execution reference is not a parseable finite scalar | 45 |

The diagnostic gives direct-scale agreement precedence. It checks only displayed scalar agreement and an explicit percent-fraction convention. Some flagged cases reflect truncation, ambiguous wording or transcription; the 116 flags do **not** establish 116 erroneous financial answers. The complete decisions, programs and annotated steps are in [reference_consistency_audit.json](../reference/grounded_answer_audit/reference_consistency_audit.json).

The study's primary metric undoes an explicit percent rendering and compares rounded execution values to `exe_ans`. Published programs sometimes retain a `multiply(..., const_100)` step; others return a fraction. Consequently that fixed metric can penalize a financially plausible percent answer under a different published convention. It remains reported exactly as frozen and is called **execution-reference agreement**, not official FinQA accuracy or adjudicated financial correctness.

## Concrete failures and disagreements

These cases were inspected from the full deterministic census; this is a small, purposeful diagnostic selection, not an exhaustive financial adjudication of all accepted or refused answers.

| Case | Observed evidence | Interpretation |
|---|---|---|
| `APD/2016/page_40.pdf-2` | Operating income 895.2, 808.4, 762.6 for 2016–2014; question asks 2014–2016 average. Prototype uses endpoints only and returns 828.9 rather than 822.0667. | **Own period-parser error.** A hyphenated range is not expanded. The displayed 822.06 also truncates the arithmetic result. |
| `UNP/2011/page_33.pdf-3` | Question asks change in **average equity**; 18,171 − 17,282 = 889. Prototype classifies the word “average” as the operation and also misses the `millions except percentages` caption. | **Own formula and scale errors.** A measure name is not an arithmetic instruction. |
| `STT/2006/page_95.pdf-1` | Question asks total assets in unconsolidated conduits; narrative gives 25.25 and 17.90 billion. Prototype instead binds table row `total` containing comprehensive-loss totals −224 and −231 million. | **Own measure-binding error.** A verbatim generic row phrase does not establish semantic identity. |
| `GPN/2010/page_87.pdf-2` | Question asks **after-tax** compensation cost. Prototype uses 18.1 and 14.6 gross cost, omitting tax benefits 6.3 and 5.2. | **Own modifier/composite-reasoning error.** The bounded phrase matcher accepted an insufficient measure. |
| `SNA/2007/page_49.pdf-4` | Dividends 1.11 vs 1.08; annotated first step says `add` but its result is 0.03. Published program adds them and produces execution 2.02778. Correct subtraction-based change is about 2.7778%; displayed reference is 2.7%. | **Specific program/step inconsistency**, plus displayed truncation. Prototype misses both frozen references; the metrics are unchanged. |
| `DVN/2018/page_35.pdf-2` | 156 vs 15 yields 940%; published execution is 940 after multiplying by 100. Prototype displays 940% but its unrendered execution is 9.4. | **Convention mismatch** under the fixed primary metric; display criterion matches. This does not establish all semantics are correct. |
| `UNP/2007/page_25.pdf-3` | Question asks 2005→2007; source free cash flow is 234→487. Published program instead subtracts 2006's 516 from 2007's 487. Prototype also misses the `millions of dollars` caption. | **Period-reference disagreement and own unit error coexist.** Do not attribute this solely to either side. |
| `C/2008/page_44.pdf-2` | −291→438. Prototype divides the change by −291; published program uses +291. | **Negative-base interpretation differs.** Percentage-growth language needs an explicit policy or abstention; a formula check alone is insufficient. |

## Reproduction

After materializing the exact pinned public test JSON (SHA256 in the protocol):

```bash
python audit_reference_consistency.py --verify
```

The script verifies the complete saved diagnostic. It never edits the frozen score, labels or output files. It is outside the pre-evaluation code lock because it was developed after observing the deterministic census.

The eight retained training preflight outputs and both two-record interrupted pilots are under `development_grounding/` and `development_grounding_pilot_*_interrupted/`. Their status files describe the interface changes. Complete executable snapshots of those early prompt versions were not retained, so they are not claimed as exactly regenerable neural experiments or held-out performance evidence. The final pilot's locked code, protocol, inputs and actual raw outputs have a separate complete replay path.

General generated financial answers remain unreliable. The separately reconciled historical SEC calculator takes explicit entity/period/metric requests and has a different, tightly bounded scope; its 39-row lineage checks do not validate this free-form question parser.
