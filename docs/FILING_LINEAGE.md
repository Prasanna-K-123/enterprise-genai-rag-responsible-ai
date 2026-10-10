# Exact filing lineage for the bounded historical calculator

All **39 register rows**, representing **33 distinct concept/period/accession contexts**, were reconciled against SEC companyfacts and inline XBRL in two filings on October 10, 2026. The September 2 historical figures are unchanged. This verifies extraction and context consistency across two representations of the same issuer disclosures; it is **not an independent financial audit or general NLP accuracy claim**.

The [receipt](../reference/financial_tools/lineage_receipt.json) retains each original register row, exact unit, concept, accession, observation start/end dates, the matching API facts, inline fact/context IDs, scales, signs, source URLs and capture hashes. It includes all 27 originally API-collected rows plus supplementary XBRL checks on the 12 table-collected rows. Depreciation/amortization and interest expense are matched to their explicit `DepreciationAndAmortization` and `InterestExpenseNonoperating` concepts, not found by searching for the expected value.

The two HTML bodies currently served **do not have the same byte hashes** as the previous registered captures. Both hashes remain separate and the mismatch is explicit. The numerical/context reconciliations match; byte identity with the earlier captures is not claimed. Full source bodies are downloaded at runtime and are not redistributed.

The issuer is identified by **CIK 815097**. The current API entity name is recorded as observed; the calculator's existing `CCL` namespace is unchanged. A comparative 2023 observation can carry filing `fy=2025`. The engine uses observation dates, not that filing label, to answer fiscal-2023 queries. Point-in-time balances and six-month YTD flows retain different contexts; they are not substituted for annual operands.

The calculator now refuses a register fact without its matching receipt. Returned evidence includes the resolved concept, observation start, API capture hash, freshly reconciled filing hash, and row digest. The supported entity, historical years, metrics and numerical results remain the same. The 33 numerical reconciliations and seven unsupported-request controls still pass.

```bash
pip install -r requirements-controls.txt
python -m src.filing_lineage
python benchmark_financial_controls.py
python -m pytest -q
```

For an independent live extraction check, collect the three sources with your own descriptive User-Agent, then produce a new receipt without replacing the historical capture:

```bash
python collect_filing_lineage.py --user-agent 'Your Project contact@example.com'
python -m src.filing_lineage --build data/sec_refresh --output data/live_lineage_receipt.json
```

The live receipt can have different API/HTML capture hashes as published data changes. It must still match the registered values at the exact historical contexts to pass. No new market data, forward forecast, restatement-free backtest, or model reasoning accuracy follows from this check.

The SEC [API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) describes companyfacts as structured, unit-specific XBRL disclosures for entire filing entities. Our inline parser supports the numerical USD formats needed for this fixed corpus, excludes segment/typed-dimension facts, and does not claim universal iXBRL conformance.
