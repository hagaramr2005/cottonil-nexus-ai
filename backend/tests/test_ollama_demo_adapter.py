"""Protocol-only tests for the optional local Ollama integration (no live model)."""
import io
import json
from urllib.request import Request

from app import copilot


def test_local_ollama_status_requires_exact_installed_tag(monkeypatch):
    monkeypatch.setenv('NEXUS_LLM_URL', 'http://127.0.0.1:11434/v1/chat/completions')
    monkeypatch.setenv('NEXUS_LLM_MODEL', 'qwen3:4b-instruct')
    def stub(url, timeout=0):
        assert url == 'http://127.0.0.1:11434/api/tags'
        return io.BytesIO(json.dumps({'models': [{'name': 'qwen3:4b-instruct'}]}).encode())
    monkeypatch.setattr(copilot.urllib.request, 'urlopen', stub)
    status = copilot.status_snapshot()
    assert status['configured'] and status['available'] is True
    assert status['model'] == 'qwen3:4b-instruct'


def test_compatible_ollama_chat_payload_is_evidence_only(monkeypatch):
    monkeypatch.setenv('NEXUS_LLM_URL', 'http://127.0.0.1:11434/v1/chat/completions')
    monkeypatch.setenv('NEXUS_LLM_MODEL', 'qwen3:4b-instruct')
    monkeypatch.delenv('NEXUS_LLM_API_KEY', raising=False)
    evidence = {'type': 'metrics', 'cases': [], 'metrics': [{'key': 'net_sales', 'value': 1234}], 'sources': ['synthetic'], 'limitations': []}
    def stub(req, timeout=0):
        assert isinstance(req, Request)
        assert req.full_url == 'http://127.0.0.1:11434/v1/chat/completions'
        payload = json.loads(req.data)
        assert payload['model'] == 'qwen3:4b-instruct'
        assert payload['messages'][0]['role'] == 'system'
        assert payload['messages'][1]['role'] == 'user'
        assert '1234' in payload['messages'][1]['content']
        assert 'Authorization' not in req.headers
        return io.BytesIO(json.dumps({'choices': [{'message': {'content': 'Recorded sales: 1234 EGP (synthetic).'}}]}).encode())
    monkeypatch.setattr(copilot.urllib.request, 'urlopen', stub)
    reply, reason = copilot.llm_explain('What are sales?', evidence, 'en', [])
    assert reason is None and reply.startswith('Recorded sales: 1234')
