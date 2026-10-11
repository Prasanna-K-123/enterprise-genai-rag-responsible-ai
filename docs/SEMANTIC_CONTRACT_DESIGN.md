# Registered explicit financial-answer semantics challenge

The completed 128- and 64-question neural studies, their scoring conventions,
failures and post-hoc v2 census remain immutable. This is a separate finite
engineering comparison, motivated by those failures. No new LLM is run.

## Task and legitimate source boundary

The system accepts an explicit request with issuer CIK, exact filing accession,
operation, complete ordered concept/start/end selectors and output unit. It
does not claim to infer those fields correctly from arbitrary prose. The
supported operations are lookup, sum, unweighted annual mean, subtraction,
growth relative to operand zero, and a ratio. Growth/ratio require a positive
denominator; absent/ambiguous contexts, currency, periods and operations refuse.
Annual duration is explicitly bounded at 350–380 days. Means require one
observation in every consecutive calendar end-year in their specified range.

Two issuers are fixed: Apple CIK0000320193 and Microsoft CIK0000789019. Four
us-gaap concepts are fixed in the source collector, with observation end-years
2023–2025. Choose the latest common 10-K accession filed by 2026-10-11 that
contains all twelve unambiguous annual USD concept-period contexts per issuer.
Filing FY is never substituted for observation dates. No source or seed is
silently replaced if this selection fails.

Before collection/scoring, lock all code, case construction, scorer and this
protocol in Git. An Apple companyfacts connection probe read only the byte
count and CIK; its fact values were not inspected. This suite uses newly
captured source contexts, but is **not an untouched natural-language holdout**.
It is a deliberately constructed conformance/fault-injection challenge; the
expected semantic outcomes and development fixtures are known by design.
Public benchmark or filing exposure in model pretraining cannot be ruled out;
no model-pretraining independence or new neural performance is asserted.

Each selected value must reconcile with a source inline-XBRL numeric node,
issuer context, exact observation dates, consolidated dimensions, USD unit and
scale. Retain full original companyconcept JSON, capture hashes, selected
original API records, and exact context/unit/numeric XML nodes. Full filing
HTML stays outside Git. This is consistency across two representations of the
same disclosure, not an independent accounting audit or a cryptographic source
authenticity certificate. The engine operates on this curated, verified capture;
its in-memory digest detects changed packets, not a maliciously replaced whole
repository and receipt.

## Equal proposal budget and strong non-LLM alternative

Construct **172 seed requests**, across the two issuers, all three years, all
four measures, free-cash-flow arithmetic, operating margin, three-year revenue
sum/mean, two revenue differences and two growth intervals. Currency outputs
cover USD, thousands, millions and billions; dimensionless outputs cover ratio
and percent. This is defined financial arithmetic, not issuer GAAP definitions
of every derived metric or a forecast.

For each seed, a correct symbolic program is constructed independently of the
runtime engine. Apply the fixed faults in `semantic_case_builder.py`. Exactly
**3,498 cases / 25 strata** are expected: **368 answer-required** (clean,
wrong copied number that execution can repair, commuted sums, equivalent growth
forms) and **3,130 refusal-required** (wrong company/measure/period/output scale,
missing references, incorrect formula, double-percent conversion, omitted
range member, wrong growth base, changed source value/currency/duration/
accession, ambiguous context and invalid/missing request fields). No faulty
case is removed because an ablation correctly refuses it.

Three policies receive the same request, source packet and constructed proposal:

1. **Reported:** use the proposed numeric answer and attached references.
2. **Addressed:** safely execute the cited source numbers and declared unit.
3. **Semantic:** additionally verify the capture digest, complete request,
   exact entity/concept/period/accession bindings, dimensions, requested unit
   and operation/formula. Equivalent growth and addition order are accepted.

These are engineering ablations, **not independently generated or trained
models**, and the proposals are not fresh neural outputs. Separately, the
deterministic planner reconstructs programs from all172 supported requests,
showing why an LLM is unnecessary for this explicit interface. It is scored
in its own stratum, not unfairly forced to validate deliberately bad proposals.

## Independent scoring, limits and stopping rule

The case builder imports neither the executor nor its scorer. It derives gold
values from retained original API records with exact Fraction arithmetic; the
runtime uses bounded Decimal arithmetic and a safe AST. The separate scorer
imports none of those modules. Answer agreement requires the requested issuer,
unit and **complete source meaning/provenance**, as well as numerical agreement
at max(1e-10 absolute,1e-12 relative). A scalar match with the wrong company,
concept, dates or source does not count. Oracle labels never enter the policy
input; poisoning tests check that boundary. Refusal-required cases require
refusal, and are separately reported from correct supported answers.

Report every case, decision, refusal reason and fault stratum; all-question
correct decisions, correct answers, correct refusals, unsafe acceptances and
false refusals. No population confidence intervals: many variants share only
24 source contexts. A zero observed escape rate is a finite-suite result, not
proof of complete safety or unknown-fault coverage. This internal independent
implementation is not external human review, candidate mastery or adoption.

After locking, perform one capture and one complete evaluation, with no
result-tuned change. Capture/technical failures may receive separately logged
pre-evaluation amendments; preserve the prior protocol/code and registration.
Any change after outcomes is development and needs a separately registered
future evaluation. Replay must verify every raw-source hash, selected context,
XML reconciliation, input, full decision, score, planner answer and artifact
hash. Source values, model weights and old evaluation references never enter
this private career checkpoint as duplicate repositories.

Prior art: [FinQA](https://aclanthology.org/2021.emnlp-main.300/) introduced
financial numerical reasoning programs; [TAT-QA](https://aclanthology.org/2021.acl-long.254/)
combines table/text extraction with symbolic arithmetic. This portfolio does
not claim to invent symbolic financial QA. The [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
distinguishes filing/observation periods and warns that calendar frame alignment
can differ from fiscal periods. Exact source contexts are used here.

Exactly seven flagship families; Stage One remains open, Stage Two deferred,
all new applications and outreach on hold. AI assistance is disclosed.
