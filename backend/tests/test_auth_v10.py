import os, pytest
from app import auth
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
@pytest.fixture(autouse=True)
def _auth_env(monkeypatch):   # scoped per test: never leaks auth into other test files
    monkeypatch.setenv('NEXUS_AUTH_ENABLED','1'); monkeypatch.setenv('NEXUS_AUTH_SECRET','test-secret')
    monkeypatch.setenv('NEXUS_USERS','exec:pw-exec:viewer;root:'+auth.hash_secret('pw-root')+':admin')
def tok(u,p):return c.post('/api/auth/login',json={'username':u,'password':p})
def test_status_open_and_required():
    assert c.get('/api/auth/status').json()=={'required':True}
    assert c.get('/api/health').status_code==200
def test_protected_without_token():
    assert c.get('/api/overview').status_code==401
def test_bad_credentials():
    assert tok('exec','wrong').status_code==401 and tok('ghost','x').status_code==401
def test_viewer_flow_and_admin_only_diagnostics():
    t=tok('exec','pw-exec').json()['token']; h={'Authorization':'Bearer '+t}
    assert c.get('/api/overview',headers=h).status_code==200
    assert c.get('/api/cv/status',headers=h).status_code==403      # server-side, not just hidden in UI
    assert c.get('/api/product/readiness',headers=h).status_code==403
    a={'Authorization':'Bearer '+tok('root','pw-root').json()['token']}
    assert c.get('/api/cv/status',headers=a).status_code==200
def test_tampered_and_expired_tokens(monkeypatch):
    t=tok('exec','pw-exec').json()['token']
    assert c.get('/api/overview',headers={'Authorization':'Bearer '+t[:-2]+'xx'}).status_code==401
    monkeypatch.setenv('NEXUS_AUTH_TTL_MIN','-1'); old=tok('exec','pw-exec').json()['token']; monkeypatch.setenv('NEXUS_AUTH_TTL_MIN','480')
    assert c.get('/api/overview',headers={'Authorization':'Bearer '+old}).status_code==401
def test_query_token_for_downloads():
    t=tok('exec','pw-exec').json()['token']
    c.cookies.clear()
    assert c.get('/api/reports/summary?access_token='+t).status_code==401
