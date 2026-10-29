"""New read-only storytelling tests using an isolated test DB."""
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.main import app
from app import storytelling


def test_storytelling_is_grounded_and_handles_missing_comparison():
    with TemporaryDirectory() as directory:
        target=Path(directory)/'example.sqlite'
        con=sqlite3.connect(target)
        con.executescript('''
          CREATE TABLE metrics(key TEXT,value REAL,unit TEXT,definition TEXT,source TEXT,trust TEXT);
          CREATE TABLE cases(id TEXT,title TEXT,severity TEXT,status TEXT);
          CREATE TABLE daily_sales(date TEXT,revenue REAL);
          INSERT INTO metrics VALUES('net_sales',150.25,'EGP','Sum net lines','sales_order_items.csv','warning');
          INSERT INTO metrics VALUES('purchase_sales_ratio',99.88,'ratio','Unreconciled source units','purchase_order_items.csv; sales_order_items.csv','blocked');
          INSERT INTO cases VALUES('NEX-001','Check quantities','high','open');
          INSERT INTO daily_sales VALUES('2026-01-01',100),('2026-01-02',125);
        ''')
        con.close()
        old=storytelling.db
        def fake_db():
            c=sqlite3.connect(target)
            c.row_factory=sqlite3.Row
            return c
        storytelling.db=fake_db
        try:
            c=TestClient(app)
            r=c.get('/api/story/metrics/net_sales?lang=ar')
            assert r.status_code==200
            assert r.json()['value']==150.25
            assert r.json()['comparison_available'] is False
            assert 'المبيعات' in r.json()['title']
            p=c.get('/api/story/metrics/purchase_sales_ratio').json()
            assert p['trust']=='blocked'
            assert 'not financial leakage' in p['what'].lower()
            assert c.get('/api/story/metrics/not_exist').status_code==404
            assert c.get('/api/story/metrics/net_sales?lang=fr').status_code==422
            chart=c.get('/api/story/chart/daily-sales').json()
            assert chart['difference']==25
            assert chart['mode']=='deterministic'
            briefing=c.get('/api/story/briefing?lang=ar').json()
            assert briefing['investigation_count']==1
            assert briefing['metrics'][0]['value']==150.25
        finally:storytelling.db=old


def test_chart_requires_two_dates():
    with TemporaryDirectory() as directory:
        target=Path(directory)/'example.sqlite'
        con=sqlite3.connect(target)
        con.execute('CREATE TABLE daily_sales(date TEXT,revenue REAL)')
        con.execute("INSERT INTO daily_sales VALUES('2026-02-01',200)")
        con.commit();con.close()
        old=storytelling.db
        def fake_db():
            c=sqlite3.connect(target);c.row_factory=sqlite3.Row;return c
        storytelling.db=fake_db
        try:
            response=TestClient(app).get('/api/story/chart/daily-sales')
            assert response.status_code==200
            assert response.json()['available'] is False
        finally:storytelling.db=old
