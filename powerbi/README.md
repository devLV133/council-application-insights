# Open and refresh the Power BI project

The project contains a native `.pbip` entry point, a TMSL semantic model (`model.bim`), Power Query CSV imports, DAX measures and a PBIR report with three pages and 20 visuals.

## First open

1. Download or clone the whole repository, keeping its folder structure intact.
2. In Power BI Desktop for Windows, enable Power BI project/PBIR preview options if your installed version requires them, and restart if prompted.
3. Open `CouncilInsights.pbip`.
4. Use **Transform data > Edit parameters** to set `DataFolder` to your absolute `data/processed` folder, for example `C:/Users/Sam/Projects/council-application-insights/data/processed`.
5. Apply the change and refresh. If prompted, use the appropriate privacy level for these local synthetic files.
6. Compare the overview to the reference values below. Save the project. Use Save As to create a `.pbix` if required.

The default folder is an example and must be changed. The repository contains no cached data model, so the first refresh is required. No API key or paid data source is needed for these local CSV imports.

## Reference results

For the committed 4 November 2026 data: 12 applications, £735,000 known cost, one missing cost, two unowned applications, two applications on expired support, nine quality issues affecting six applications and a 50% pass rate.

## Refresh workflow

Edit `data/raw/`, run `python insights.py` from the repository root, then refresh Power BI. This recalculates the CSV flags before the model imports them. Power BI does not independently recalculate review or support flags when today's date changes.

Use `python tools/build_powerbi.py` only to rebuild the original report source. It overwrites the generated definition files and will discard edits to those files. Keep manual changes in git before running it.

## Verification still required

JSON schema validation and field-reference checks do not execute DAX, Power Query or native visuals. Power BI Desktop was not available during authoring. Open/refresh the project and verify the reference results and visual layout before describing it as a tested Power BI dashboard on a CV.

The repository's preview image is the Excel summary, not a screenshot from Power BI.
