from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _by_name(d):
    return {c['name']: c for c in d['checks']}


def test_readiness_data_free_is_honest(empty_db, monkeypatch):
    monkeypatch.delenv('NEXUS_LLM_URL', raising=False)
    monkeypatch.delenv('NEXUS_LLM_MODEL', raising=False)
    d = client.get('/api/readiness').json()
    c = _by_name(d)
    assert d['data_state'] == 'data_not_connected' and d['overall'] == 'degraded'
    assert c['process_alive']['ok'] and c['database_connected']['ok'] and c['schema_ready']['ok']
    assert not c['datasets_ingested']['ok'] and c['datasets_ingested']['code'] == 'DATA_NOT_CONNECTED'
    assert not c['sales_mart_ready']['ok']
    assert not c['metrics_certified']['ok']
    assert c['llm_configured']['code'] == 'LLM_NOT_CONFIGURED'
    assert d['security']['branch_scoped_authorization'] is True


def test_readiness_synthetic_is_ready_but_never_certified(synthetic_db):
    d = client.get('/api/readiness').json()
    c = _by_name(d)
    assert d['overall'] == 'ready' and d['data_state'] == 'populated'
    assert c['sales_mart_ready']['ok']
    assert not c['metrics_certified']['ok']  # certification needs stakeholder approval


def test_readiness_requires_admin_when_auth_enabled(empty_db, monkeypatch):
    monkeypatch.setenv('NEXUS_AUTH_ENABLED', '1')
    assert client.get('/api/readiness').status_code == 401


def test_readiness_does_not_leak_paths(empty_db):
    body = client.get('/api/readiness').text
    assert str(empty_db.parent) not in body


def test_ollama_probe_uses_configured_port_not_hardcoded(monkeypatch):
    from app import copilot
    seen = []

    class R:
        def __enter__(s): return s
        def __exit__(s, *a): pass
        def read(s, n): return b'{"models":[{"name":"qwen2.5:3b"}]}'
    monkeypatch.setattr(copilot.urllib.request, 'urlopen', lambda u, timeout=0: seen.append(u) or R())
    monkeypatch.setenv('NEXUS_LLM_URL', 'http://localhost:22434/v1/chat/completions')
    monkeypatch.setenv('NEXUS_LLM_MODEL', 'qwen2.5:3b')
    s = copilot.status_snapshot()
    assert seen == ['http://localhost:22434/api/tags'] and s['available'] is True and s['mode'] == 'grounded-llm'
