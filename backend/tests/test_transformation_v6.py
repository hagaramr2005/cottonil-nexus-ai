"""Reproducible API checks using a temporary source-like mart, no Cottonil data alteration."""
import os,sys,tempfile,sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core import db
from app import transformation

def test_passport_empty_safe():
    with tempfile.TemporaryDirectory() as d:
        old=transformation.db
        def temp_db():
            c=sqlite3.connect(str(Path(d)/'pass.sqlite'));c.row_factory=sqlite3.Row
            c.executescript('CREATE TABLE IF NOT EXISTS metrics(key TEXT,value REAL,unit TEXT,definition TEXT,source TEXT,trust TEXT,updated_at TEXT);CREATE TABLE IF NOT EXISTS cases(id TEXT,evidence_json TEXT);')
            return c
        transformation.db=temp_db
        try:
            resp=TestClient(app).get('/api/transform/passports')
            assert resp.status_code==200
            assert resp.json()['trust_definitions']['blocked']
        finally:transformation.db=old

def test_monthly_revenue_reconciles():
    with tempfile.TemporaryDirectory() as d:
        old=transformation.db
        def temp_db():
            c=sqlite3.connect(str(Path(d)/'mart.sqlite'));c.row_factory=sqlite3.Row
            c.executescript('CREATE TABLE IF NOT EXISTS sales_mart(month TEXT,branch_id TEXT,channel TEXT,net REAL,gross REAL,discount REAL,units REAL,line_margin REAL);')
            if not c.execute('SELECT 1 FROM sales_mart').fetchone():
                c.executemany('INSERT INTO sales_mart VALUES(?,?,?,?,?,?,?,?)', [('2026-01','B1','store',100,110,10,2,30),('2026-02','B1','store',150,170,20,3,40),('2026-01','B2','web',75,80,5,1,15),('2026-02','B2','web',55,60,5,1,10)])
            return c
        transformation.db=temp_db
        try:
            r=TestClient(app).get('/api/transform/revenue-xray?current=2026-02&previous=2026-01')
            assert r.status_code==200,r.text
            result=r.json()
            assert result['metrics']['revenue']['delta']==30
            assert result['branch_reconciles']
            assert len(result['branch_contributions'])==2
        finally:transformation.db=old
