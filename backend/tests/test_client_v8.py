import os,sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import core
from app.main import app

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(core,'DB',tmp_path/'v8.db')
    con=core.db()
    con.execute("INSERT INTO metrics VALUES (?,?,?,?,?,?,?)",('net_sales',1200,'EGP','Recorded sales','sales_order_items.csv','warning','2026-01-01'))
    con.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?)",('INV-1','Review unexplained sales','high','open','["Recorded gap"]','["Missing report"]','["sales_order_items.csv"]','2026-01-01','2026-01-01'))
    con.execute("INSERT INTO sku_sales VALUES (?,?,?,?,?)",('SKU-1',10,300,12,4))
    con.commit();con.close()
    return TestClient(app)

def test_recommendations_grounded(client):
    r=client.get('/api/client/recommendations?lang=ar');assert r.status_code==200
    items=r.json()['recommendations'];assert len(items)==2
    assert items[0]['case_id']=='INV-1' and items[0]['estimated_benefit'] is None
    assert items[1]['type']=='data_quality'

def test_context_case_and_sku(client):
    p={'question':'What needs investigation?','page':'cases','case_id':'INV-1','lang':'ar'}
    r=client.post('/api/client/ask',json=p);assert r.status_code==200
    assert r.json()['supported'] and r.json()['facts'][0]['hypotheses_not_facts']==['Missing report']
    p={'question':'Tell me about this SKU','page':'sku','sku_id':'SKU-1'}
    r=client.post('/api/client/ask',json=p);assert r.status_code==200
    assert r.json()['facts'][0]['values']['revenue']==300

def test_bad_inputs(client):
    assert client.post('/api/client/ask',json={'question':'hello','page':'notreal'}).status_code==422
    assert client.post('/api/client/ask',json={'question':'hello','case_id':'absent'}).status_code==404
    assert client.get('/api/client/recommendations?lang=invalid').status_code==422

def test_unsupported_is_explicit(client):
    r=client.post('/api/client/ask',json={'question':'predict arbitrary outcome','page':'settings'})
    assert r.json()['supported'] is False
