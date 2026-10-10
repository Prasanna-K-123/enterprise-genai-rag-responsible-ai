# Separate controlled-language parser: post-hoc development

The frozen v1 experiment is unchanged. This **separate deterministic version** addresses concrete errors discovered in its full public-test census. It has no LLM, no fresh held-out model experiment and no validated model-improvement claim.

## Defined request contract

`src.controlled_contract_v2.controlled_contract_v2(record)` accepts only a few complete question templates for a table-row average, two-year amount change/decrease, or percent growth/decrease. The question's **complete measure phrase** must equal one unique source row, rather than merely contain a row phrase. Generic `total`, `balance`, `amount` and `value` measures are refused. Unsupported aliases, extra instructions, narrative-only evidence, composite calculations and date/column qualifiers are outside the grammar.

- Hyphenated average ranges expand to every year, with a bound of two to ten years. Every period must have exactly one source cell.
- “Average equity” in a change question is a measure name; the arithmetic operation comes from the complete question template.
- Monetary conversions require a recognized source-table caption and a compatible currency dimension. A requested output unit is never used to infer the source scale. Bare-year columns are required; mixed scale, quarter, footnote or restatement headings are refused.
- Percent growth/decrease with a nonpositive base is refused until an explicit interpretation policy exists.
- The original bounded AST executor still checks the calculation, source references and dimensions. The source context and its digest remain attached.

This is a syntactic contract with deliberately sparse coverage. It inherits v1's dollar-symbol convention and numerical transcription limitations. It does not establish issuer/subsidiary equivalence, every dollar currency, source authenticity, financial reporting-basis comparability or general language understanding. It is not a general financial QA service.

## Actual regression checks

Eleven tests cover observed failures and additional controls: the APD three-year mean; a UNP change in average equity and its caption scale; STT generic-total and GPN after-tax measure mismatches; SNA balance-versus-expense ambiguity; missing source scale; negative-base growth; explicit reversed dates; extra instructions; duplicate measures; mixed unit columns; and isolation from answer/program/gold annotations. Several controls share one test. Full repository suite: **85 tests pass** locally.

## Development census, not fresh performance

The same already inspected public split is replayed in full: **24 answered / 1,123 refused out of 1,147** (2.09% coverage), **19 display-reference matches** and **14 execution-reference matches**. Display-reference precision is 19/24 = 79.17%, with descriptive Wilson interval [59.53%, 90.76%]. Different syntax support and post-hoc development prevent treating this as a validated improvement over v1. Reference-matching also has the convention and annotation limits in [REFERENCE_DIAGNOSTICS.md](REFERENCE_DIAGNOSTICS.md).

All decisions, selected cells, provenance, references and refusals are retained in [development_census.json](../reference/controlled_contract_v2/development_census.json), with source-code and dataset hashes. Its five display-reference disagreements are APD/2016/page_40.pdf-2, IPG/2017/page_92.pdf-2, ZBH/2007/page_67.pdf-1, LMT/2014/page_77.pdf-1 and UNP/2007/page_25.pdf-3. They remain counted as misses; no automatic claim that all five published references are wrong follows.

```bash
python -m pytest -q
python benchmark_controlled_contract_v2.py --replay --download
```

Replay verifies all saved decisions and current source hashes against the pinned published test data. It does not generate a model response, establish new held-out accuracy or overwrite the v1 outputs. A future broader reliability claim needs a separately registered, appropriate evaluation.
