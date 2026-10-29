from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_readiness_is_transparent():
    response=client.get('/api/product/readiness')
    assert response.status_code==200
    obj=response.json()
    assert obj['readiness']=='needs_validation'
    assert isinstance(obj['data']['datasets'],int)
    assert 'warnings' in obj
    assert obj['capabilities']['client_model_center_exposed'] is False

def test_readiness_does_not_report_llm_operating():
    response=client.get('/api/product/readiness')
    assert 'llm_provider_configured' in response.json()['capabilities']
