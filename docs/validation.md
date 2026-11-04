# Validation record

Checked on 4 November 2026.

| Area | What was checked | Result / boundary |
|---|---|---|
| Python and SQLite | 17 automated tests covering source constraints, missing values, date boundaries, cost aggregation and repeatable exports | Passed locally on Python 3.12 |
| Source-to-report controls | 12 applications; £735,000 known cost; 9 quality issues; 6 affected applications; 2 expired-support applications | Reconciled to the synthetic source records |
| Excel | Summary formulas agree with SQL; changing a blank cost to zero decreases the missing-cost count; formulas restored before export | Passed in the workbook authoring engine |
| Excel layout | Rendered all 4 worksheets, including both sides of the application inventory | Reviewed for readable labels and values |
| Excel file | Exported native `.xlsx` containing formulas and a native chart | Microsoft Excel itself was not available for an independent application test |
| Power BI source | 29 JSON files validated against Microsoft's published schemas; report columns and measures resolve to the model | Passed |
| Power BI Desktop | Open, Power Query refresh, DAX execution, interactive behaviour and final visual layout | Not run; requires Power BI Desktop for Windows |
| SQL Server | Generated setup, typed schema, seed rows and reporting views | Not executed against SQL Server; only the shared logic has been exercised in SQLite |
| GitHub Actions | Workflow supplied for Python 3.11, 3.12 and 3.13 | See the Actions tab for live results |

## Reproduce

```bash
python -m unittest discover -s tests -v
python insights.py
python tools/build_sql_server.py
python tools/build_powerbi.py
python -m pip install -r requirements-dev.txt
python tools/check_powerbi.py
```

The schema checker retrieves Microsoft schema files from the official `microsoft/json-schemas` repository and caches them in the OS temporary directory. A schema identifier uses `schema.embedded.json` while the published filename uses `schema-embedded.json`; the checker maps that filename without changing the schema contents.

The Excel builder is `tools/build_workbook.mjs`. It requires the authoring environment's `@oai/artifact-tool` package. The committed workbook can be opened without that package. Its formulas are independent of the Python runtime once exported, while relationship inputs remain a dated SQL snapshot.

## Remaining manual checks

1. Open and refresh the PBIP in Power BI Desktop with the local data folder parameter.
2. Confirm the reference totals, check all three pages and adjust any native formatting needed.
3. Run `sql/sql_server_setup.sql` in a new empty SQL Server database and compare the view results.
4. Open the Excel workbook in Microsoft Excel and confirm the summary and chart after recalculation.

Do not describe these pending native-application checks as completed.
