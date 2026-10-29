import os
import pytest
from app import core

@pytest.fixture(autouse=True)
def isolate_api_test_database(tmp_path, monkeypatch):
    """Prevent API smoke tests from redirecting the database used by other tests."""
    monkeypatch.setattr(core, 'DB', tmp_path / 'api_test.sqlite')
    monkeypatch.setenv('NEXUS_WRITE_TOKEN', 'test-only-token')
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health():assert client.get('/api/health').status_code==200
def test_metrics():assert client.get('/api/metrics').status_code==200
def test_unconfigured_ai():assert client.get('/api/ai/status').json()['available'] is False
def test_unknown_case():assert client.get('/api/cases/NOPE').status_code==404
def test_blocked_write():assert client.patch('/api/cases/NOPE',json={'status':'open','reason':'test reason'}).status_code==403
def test_limit_validation():assert client.get('/api/skus?limit=2000').status_code==422
