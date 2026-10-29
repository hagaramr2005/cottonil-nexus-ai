import pytest
from app import auth
from fastapi.testclient import TestClient
from app.main import app


def test_production_rejects_unsafe_configuration(monkeypatch):
    monkeypatch.setenv('NEXUS_ENV', 'production')
    monkeypatch.delenv('NEXUS_AUTH_ENABLED', raising=False)
    with pytest.raises(RuntimeError, match='Unsafe production configuration'):
        auth.validate_production_config()


def configure(monkeypatch):
    monkeypatch.setenv('NEXUS_ENV', 'production')
    monkeypatch.setenv('NEXUS_AUTH_ENABLED', '1')
    monkeypatch.setenv('NEXUS_AUTH_SECRET', 'a'*64)
    monkeypatch.setenv('NEXUS_AUTH_TTL_MIN', '30')
    monkeypatch.setenv('NEXUS_WRITE_TOKEN', 'b'*48)
    monkeypatch.setenv('NEXUS_CORS', 'https://retail.example.com')
    monkeypatch.setenv('NEXUS_USERS', 'alice:'+auth.hash_secret('password1')+':viewer;admin:'+auth.hash_secret('password2')+':admin')


def test_production_config_and_protected_get(monkeypatch):
    configure(monkeypatch)
    auth.validate_production_config()
    with TestClient(app,base_url='https://retail.example.com') as c:
        assert c.get('/api/overview').status_code == 401
        resp = c.post('/api/auth/login', json={'username':'alice','password':'password1'})
        assert resp.status_code == 200
        assert resp.json()['token'] == ''
        assert c.get('/api/overview').status_code == 200
        assert c.get('/api/overview').headers['Cache-Control'] == 'no-store'
        assert c.get('/api/overview', headers={'Authorization':'Bearer invalid'}).status_code == 401


def test_production_viewer_cannot_write(monkeypatch):
    configure(monkeypatch)
    with TestClient(app,base_url='https://retail.example.com') as c:
        data = c.post('/api/auth/login',json={'username':'alice','password':'password1'}).json()
        assert data['token'] == ''
        response = c.post('/api/analyst/ask',json={'question':'net sales'})
        assert response.status_code == 200
        assert c.patch('/api/cases/NEX-001',json={'status':'resolved','reason':'not allowed'}).status_code == 403


def test_rejects_weak_password_hashes(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv('NEXUS_USERS', 'admin:plaintext:admin')
    with pytest.raises(RuntimeError, match='PBKDF2'):
        auth.validate_production_config()
