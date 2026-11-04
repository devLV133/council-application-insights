import csv
import shutil
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from insights import ROOT, build_database, export, rows, summary


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / 'raw'
        shutil.copytree(ROOT / 'data/raw', self.folder)

    def tearDown(self):
        self.temp.cleanup()

    def database(self, **kwargs):
        db = build_database(self.folder, date(2026, 11, 4), **kwargs)
        self.addCleanup(db.close)
        return db

    def change(self, table, fn):
        path = self.folder / f'{table}.csv'
        with path.open(newline='') as f:
            reader = csv.DictReader(f)
            fields, data = reader.fieldnames, list(reader)
        fn(data)
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

    def test_seed_control_totals(self):
        s = summary(self.database())
        self.assertEqual((s['applications'], s['known_annual_cost_gbp']), (12, 735000))
        self.assertEqual((s['quality_issues'], s['apps_with_quality_issues']), (9, 6))
        self.assertEqual((s['unowned_apps'], s['unsupported_apps']), (2, 2))

    def test_relationship_fanout_does_not_duplicate_cost(self):
        before = summary(self.database())
        self.change('application_services', lambda r: r.append({'app_id':'A02','service_id':'S02'}))
        after = summary(self.database())
        self.assertEqual(before['known_annual_cost_gbp'], after['known_annual_cost_gbp'])
        self.assertEqual(after['applications'], 12)

    def test_support_end_is_inclusive(self):
        self.change('technologies', lambda r: r[2].update(support_end='2026-11-04'))
        p = {r['app_id']:r for r in rows(self.database(), 'portfolio')}
        self.assertEqual(p['A03']['unsupported_technology'], 0)
        self.assertEqual(p['A05']['unsupported_technology'], 1)

    def test_unknown_support_is_not_supported_or_expired(self):
        t = {r['technology_id']:r for r in rows(self.database(),'technology_exposure')}
        self.assertEqual(t['T06']['support_status'], 'Unknown')
        p = {r['app_id']:r for r in rows(self.database(),'portfolio')}
        self.assertEqual((p['A11']['unknown_support'],p['A11']['unsupported_technology']), (1,0))

    def test_stale_cutoff_exact_and_one_day_over(self):
        cutoff = date(2026,11,4)-timedelta(days=180)
        self.change('applications', lambda r:r[0].update(last_reviewed=cutoff.isoformat()))
        self.assertEqual(rows(self.database(),'portfolio')[0]['stale_review'],0)
        self.change('applications', lambda r:r[0].update(last_reviewed=(cutoff-timedelta(days=1)).isoformat()))
        self.assertEqual(rows(self.database(),'portfolio')[0]['stale_review'],1)

    def test_future_date_is_flagged(self):
        self.change('applications', lambda r:r[0].update(last_reviewed='2026-11-05'))
        self.assertEqual(rows(self.database(),'portfolio')[0]['future_review'],1)

    def test_zero_cost_is_known(self):
        self.change('applications', lambda r:r[9].update(annual_cost_gbp='0'))
        self.assertEqual(summary(self.database())['missing_cost_apps'],0)

    def test_missing_review_not_silently_stale(self):
        p = {r['app_id']:r for r in rows(self.database(),'portfolio')}
        self.assertEqual((p['A10']['missing_review'],p['A10']['stale_review']), (1,0))

    def test_duplicate_key_rejected(self):
        self.change('applications', lambda r:r.append(r[0].copy()))
        with self.assertRaises(sqlite3.IntegrityError): self.database()

    def test_orphan_relationship_rejected(self):
        self.change('application_services', lambda r:r[0].update(app_id='UNKNOWN'))
        with self.assertRaises(sqlite3.IntegrityError): self.database()

    def test_invalid_date_rejected(self):
        self.change('applications', lambda r:r[0].update(last_reviewed='2026-02-30'))
        with self.assertRaises(ValueError): self.database()

    def test_duplicate_mapping_rejected(self):
        self.change('application_services', lambda r:r.append(r[0].copy()))
        with self.assertRaises(sqlite3.IntegrityError): self.database()

    def test_self_dependency_rejected(self):
        self.change('dependencies', lambda r:r[0].update(depends_on_app_id=r[0]['app_id']))
        with self.assertRaises(sqlite3.IntegrityError): self.database()

    def test_negative_nan_or_malformed_cost_rejected(self):
        for value in ['-1','NaN','12.123','oops']:
            with self.subTest(value=value):
                self.change('applications', lambda r:r[0].update(annual_cost_gbp=value))
                with self.assertRaises(ValueError): self.database()

    def test_missing_technology_flag(self):
        self.change('application_technologies', lambda r:r.__setitem__(slice(None),[x for x in r if x['app_id']!='A12']))
        self.assertEqual(rows(self.database(),'portfolio')[-1]['missing_technology'],1)

    def test_export_is_reproducible(self):
        db = self.database()
        a,b = Path(self.temp.name)/'a',Path(self.temp.name)/'b'
        export(db,a); export(db,b)
        self.assertEqual({p.name:p.read_bytes() for p in a.iterdir()},
                         {p.name:p.read_bytes() for p in b.iterdir()})

    def test_service_counts_are_distinct_and_cost_not_allocated(self):
        s = {r['service_id']:r for r in rows(self.database(),'service_exposure')}
        self.assertEqual(s['S03']['unsupported_apps'],1)
        self.assertEqual(s['S01']['unsupported_apps'],1)
        self.assertNotIn('annual_cost_gbp', s['S01'])


if __name__ == '__main__': unittest.main()
