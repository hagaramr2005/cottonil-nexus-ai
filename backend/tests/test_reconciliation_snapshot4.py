"""Synthetic integrity tests: NO company data, no fabricated cases from quiet inputs."""
import csv
from app import core
from synthetic_fixture import write_fixture
from fastapi.testclient import TestClient
from app.main import app


def patch_rows(path,changes):
    with path.open(newline='') as fp:
        reader=csv.DictReader(fp); fields=reader.fieldnames; rows=list(reader)
    for row in rows:
        row.update(changes)
    with path.open('w',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def test_case_ids_absent_without_observed_issues(tmp_path,monkeypatch):
    raw=tmp_path/'raw';write_fixture(raw)
    patch_rows(raw/'purchase_order_items.csv',{'quantity':'1'})
    patch_rows(raw/'marketing_campaigns.csv',{'orders_attributed':'1'})
    patch_rows(raw/'branches.csv',{'opening_date':'01/01/2020'})
    monkeypatch.setattr(core,'DB',tmp_path/'quiet.sqlite');monkeypatch.setattr(core,'RAW',raw)
    result=core.ingest()
    assert result['cases_created']==0
    with TestClient(app) as c:
        assert c.get('/api/cases').json()==[]
        status=c.get('/api/reconciliation/status').json()
        assert len(status['case_rules'])==3
        assert all(not x['supported'] for x in status['case_rules'])
        assert len(status['source_datasets'])==6
        assert all(len(x['sha256'])==64 for x in status['source_datasets'])


def test_missing_source_suppresses_metrics(tmp_path,monkeypatch):
    raw=tmp_path/'raw';write_fixture(raw)
    (raw/'purchase_order_items.csv').unlink()
    (raw/'marketing_campaigns.csv').unlink()
    monkeypatch.setattr(core,'DB',tmp_path/'missing.sqlite');monkeypatch.setattr(core,'RAW',raw)
    core.ingest()
    with TestClient(app) as c:
        keys={x['key'] for x in c.get('/api/metrics').json()}
        assert 'purchased_units' not in keys
        assert 'purchase_sales_ratio' not in keys
        assert 'marketing_attributed_orders' not in keys
        status=c.get('/api/reconciliation/status').json()
        assert not next(x for x in status['case_rules'] if x['case_id']=='NEX-001')['supported']


def test_reingest_drops_obsolete_source_and_aggregates(tmp_path,monkeypatch):
    raw=tmp_path/'raw';write_fixture(raw)
    monkeypatch.setattr(core,'DB',tmp_path/'reingest.sqlite');monkeypatch.setattr(core,'RAW',raw)
    core.ingest()
    assert len(core.db().execute('SELECT date FROM daily_sales').fetchall())==12
    (raw/'purchase_order_items.csv').unlink()
    (raw/'marketing_campaigns.csv').unlink()
    # Source update: preserve only the first January order and line.
    for file_name in ('sales_orders.csv','sales_order_items.csv'):
        path=raw/file_name
        with path.open(newline='') as f:
            reader=csv.DictReader(f);names=reader.fieldnames;first=next(reader)
        with path.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=names);writer.writeheader();writer.writerow(first)
    core.ingest()
    con=core.db()
    try:
        assert con.execute('SELECT COUNT(*) FROM daily_sales').fetchone()[0]==1
        assert con.execute("SELECT COUNT(*) FROM datasets WHERE name='purchase_order_items.csv'").fetchone()[0]==0
        assert con.execute("SELECT COUNT(*) FROM source_samples WHERE table_name='marketing_campaigns.csv'").fetchone()[0]==0
        assert con.execute("SELECT COUNT(*) FROM metrics WHERE key='purchase_sales_ratio'").fetchone()[0]==0
        assert con.execute("SELECT COUNT(*) FROM cases WHERE id='NEX-001'").fetchone()[0]==0
    finally:con.close()
