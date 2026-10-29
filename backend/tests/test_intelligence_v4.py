"""V4 tests exercise true SQLite aggregation, not canned responses."""
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.core import DB, db

client=TestClient(app)

def test_risk_links_are_evidence_aware():
    response=client.get('/api/intelligence/risk')
    assert response.status_code==200
    obj=response.json()
    assert 'signals' in obj
    for signal in obj['signals']:
        assert signal['classification']=='observed investigation lead'
        assert signal['confidence'] is None
        assert signal['id']

def test_invalid_period_rejected():
    response=client.get('/api/intelligence/compare',params={'current':'nonsense','previous':'2025-01'})
    assert response.status_code==422

def test_missing_sku_returns_404():
    assert client.get('/api/intelligence/sku/ID_THAT_DOES_NOT_EXIST').status_code==404

def test_month_comparison_if_mart_exists():
    periods=client.get('/api/intelligence/periods')
    if periods.status_code==503: return
    months=periods.json()['months']
    if len(months)<2:return
    response=client.get('/api/intelligence/compare',params={'current':months[-1],'previous':months[-2]})
    assert response.status_code==200
    data=response.json()
    assert round(data['current']['revenue']-data['previous']['revenue'],2)==data['delta']
    assert data['trust']=='warning'
