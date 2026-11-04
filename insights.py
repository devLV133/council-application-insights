"""Reproducible council portfolio analysis. Python 3.11+, standard library only."""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TABLES = {
    'owners': ['owner_id', 'owner_team'],
    'applications': ['app_id', 'application', 'owner_id', 'annual_cost_gbp', 'last_reviewed'],
    'services': ['service_id', 'service', 'criticality'],
    'technologies': ['technology_id', 'technology', 'support_end'],
    'application_services': ['app_id', 'service_id'],
    'application_technologies': ['app_id', 'technology_id'],
    'dependencies': ['app_id', 'depends_on_app_id'],
}
EXPORTS = ['portfolio', 'quality_issues', 'dependency_detail', 'service_exposure',
           'technology_exposure', 'report_context']
REQUIRED = {'owner_id', 'owner_team', 'app_id', 'application', 'service_id', 'service',
            'criticality', 'technology_id', 'technology', 'depends_on_app_id'}


def read_sources(folder: Path) -> dict[str, list[dict]]:
    result = {}
    for table, columns in TABLES.items():
        with (folder / f'{table}.csv').open(newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != columns:
                raise ValueError(f'{table}: expected columns {columns}')
            records = []
            for line, raw in enumerate(reader, 2):
                if None in raw or any(v is None for v in raw.values()):
                    raise ValueError(f'{table}:{line}: wrong number of fields')
                row = {k: v.strip() or None for k, v in raw.items()}
                for k, v in row.items():
                    optional_owner = table == 'applications' and k == 'owner_id'
                    if k in REQUIRED and v is None and not optional_owner:
                        raise ValueError(f'{table}:{line}: missing {k}')
                    if k in {'last_reviewed', 'support_end'} and v is not None:
                        if date.fromisoformat(v).isoformat() != v:
                            raise ValueError(f'{table}:{line}: use YYYY-MM-DD for {k}')
                    if k == 'annual_cost_gbp' and v is not None:
                        try:
                            amount = Decimal(v)
                            if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal('.01')):
                                raise ValueError(f'{table}:{line}: cost must be non-negative with at most 2 decimals')
                        except InvalidOperation as exc:
                            raise ValueError(f'{table}:{line}: invalid cost') from exc
                records.append(row)
            result[table] = records
    return result


def build_database(folder: Path, as_of: date, stale_days: int = 180) -> sqlite3.Connection:
    if stale_days < 1:
        raise ValueError('stale_days must be positive')
    sources = read_sources(folder)
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        db.executescript((ROOT / 'sql/schema.sql').read_text())
        with db:
            for table, columns in TABLES.items():
                db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for _ in columns)})",
                               [[row[c] for c in columns] for row in sources[table]])
            db.execute('INSERT INTO report_context VALUES (1,?,?,?)',
                       (as_of.isoformat(), (as_of-timedelta(days=stale_days)).isoformat(), stale_days))
        db.executescript((ROOT / 'sql/views.sql').read_text())
    except Exception:
        db.close()
        raise
    return db


def rows(db, table):
    if table not in EXPORTS:
        raise ValueError('Unknown export')
    return [dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY 1,2')]


def summary(db):
    p = rows(db, 'portfolio')
    q = rows(db, 'quality_issues')
    ctx = rows(db, 'report_context')[0]
    affected = len({r['app_id'] for r in q})
    known_cost = sum((Decimal(str(r['annual_cost_gbp'])) for r in p if r['annual_cost_gbp'] is not None), Decimal(0))
    return {
        'as_of_date': ctx['as_of_date'], 'stale_days': ctx['stale_days'],
        'applications': len(p), 'known_annual_cost_gbp': float(known_cost),
        'missing_cost_apps': sum(r['missing_cost'] for r in p),
        'unowned_apps': sum(r['missing_owner'] for r in p),
        'stale_reviews': sum(r['stale_review'] for r in p),
        'unsupported_apps': sum(r['unsupported_technology'] for r in p),
        'unknown_support_apps': sum(r['unknown_support'] for r in p),
        'quality_issues': len(q), 'apps_with_quality_issues': affected,
        'quality_pass_rate': (len(p)-affected)/len(p) if p else None,
        'direct_dependencies': len(rows(db, 'dependency_detail')),
    }


def export(db, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    for table in EXPORTS:
        cursor = db.execute(f'SELECT * FROM {table} ORDER BY 1,2')
        with (output / f'{table}.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow([c[0] for c in cursor.description])
            writer.writerows(cursor.fetchall())
    stats = summary(db)
    (output / 'summary.json').write_text(json.dumps(stats, indent=2) + '\n')
    # A typed input for the Excel builder, distinct from editable workbook formulas.
    payload = {t: rows(db, t) for t in EXPORTS}
    payload['summary'] = stats
    (output / 'workbook_data.json').write_text(json.dumps(payload, indent=2) + '\n')
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--out', type=Path, default=ROOT / 'data/processed')
    parser.add_argument('--as-of', type=date.fromisoformat, default=date(2026, 11, 4))
    parser.add_argument('--stale-days', type=int, default=180)
    args = parser.parse_args()
    try:
        db = build_database(args.data, args.as_of, args.stale_days)
        try:
            result = export(db, args.out)
        finally:
            db.close()
    except (ValueError, sqlite3.IntegrityError, OSError) as exc:
        parser.exit(2, f'Input rejected: {exc}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
