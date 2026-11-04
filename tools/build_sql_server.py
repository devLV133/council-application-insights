"""Generate an inspectable, non-destructive SQL Server demo setup script."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from insights import ROOT, TABLES, read_sources


def literal(v):
    return 'NULL' if v is None else "N'" + str(v).replace("'", "''") + "'"


def build():
    sources = read_sources(ROOT / 'data/raw')
    text = ["""-- SQL Server 2019+ demo. Run in a NEW, EMPTY database in SSMS or Azure Data Studio.
-- This script creates unqualified tables in your default schema, normally dbo.
-- Never run it against an operational database. It contains no DROP statements.
-- On rerun, existing-table checks stop execution rather than replacing data.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
"""]
    for table in [*TABLES, 'report_context']:
        text.append(f"IF OBJECT_ID(N'dbo.{table}', N'U') IS NOT NULL\n    THROW 50001, 'Use a new empty demo database.', 1;\n")
    text.append((ROOT/'sql/schema.sql').read_text())
    for table, cols in TABLES.items():
        if sources[table]:
            values = ',\n'.join('(' + ','.join(literal(row[c]) for c in cols) + ')' for row in sources[table])
            text.append(f"INSERT INTO {table} ({','.join(cols)}) VALUES\n{values};\n")
    as_of = date(2026,11,4)
    text.append(f"INSERT INTO report_context VALUES (1,'{as_of}','{as_of-timedelta(days=180)}',180);\nCOMMIT;\nGO\n")
    for view in (ROOT/'sql/views.sql').read_text().split(';'):
        if view.strip(): text.append(view.strip()+';\nGO\n')
    text.append("SELECT COUNT(*) AS applications, SUM(annual_cost_gbp) AS known_annual_cost_gbp FROM portfolio;\nSELECT * FROM quality_issues ORDER BY app_id, issue;\nSELECT * FROM service_exposure ORDER BY service_id;\n")
    (ROOT/'sql/sql_server_setup.sql').write_text('\n'.join(text), encoding='utf-8')


if __name__ == '__main__': build()
