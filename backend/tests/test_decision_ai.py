import pytest
from datetime import date,timedelta
from fastapi.testclient import TestClient
from app import core
from app.main import app
from app.decision_ai import model_eval

@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(core,'DB',tmp_path/'isolated.sqlite')
 monkeypatch.setenv('NEXUS_WRITE_TOKEN','test-token')
 with core.db() as c:
  for i in range(91):
   d=(date(2026,1,1)+timedelta(days=i)).isoformat()
   c.execute('INSERT INTO daily_sales VALUES(?,?,?,?,?)',(d,float(100+i%7*15),2,3,1))
  c.execute("INSERT INTO cases VALUES ('NEX-001','Audit','high','open','[]','[]','[]','now','now')")
  c.execute("INSERT INTO metrics VALUES ('net_sales',100,'EGP','test','test source','warning','now')")
  c.commit()
 return TestClient(app)

def test_train_forecast_and_registry(client):
 assert client.post('/api/decision-ai/ml/train').status_code==403
 r=client.post('/api/decision-ai/ml/train',headers={'x-nexus-token':'test-token'})
 assert r.status_code==200,r.text
 assert r.json()['evaluation']['mae']==0
 assert len(client.get('/api/decision-ai/ml/runs').json())==1
 f=client.get('/api/decision-ai/ml/forecast?days=9')
 assert f.status_code==200,f.text
 assert len(f.json()['predictions'])==9
 assert f.json()['uncertainty_intervals']=='unavailable_not_calibrated'

def test_copilot_allowlist(client):
 r=client.post('/api/decision-ai/copilot/query',json={'intent':'metrics'})
 assert r.status_code==200
 assert r.json()['evidence'][0]['trust']=='warning'
 assert client.post('/api/decision-ai/copilot/query',json={'intent':'run_shell'}).status_code==422

def test_decisions_require_evidence_and_valid_approval(client):
 data={'case_id':'NEX-001','title':'Reconcile sales','action':'Inspect sales order unit references','owner':'Analyst','actor':'Reviewer','evidence_keys':['net_sales']}
 headers={'x-nexus-token':'test-token'}
 assert client.post('/api/decision-ai/decisions',json=data).status_code==403
 bad={**data,'evidence_keys':['fictional']}
 assert client.post('/api/decision-ai/decisions',headers=headers,json=bad).status_code==422
 r=client.post('/api/decision-ai/decisions',headers=headers,json=data)
 assert r.status_code==200,r.text
 ident=r.json()['id']
 assert client.patch(f'/api/decision-ai/decisions/{ident}',headers=headers,json={'status':'implemented','actor':'Reviewer','reason':'skip approval'}).status_code==409
 for status in ['reviewed','approved','in_progress','implemented']:
  r=client.patch(f'/api/decision-ai/decisions/{ident}',headers=headers,json={'status':status,'actor':'Reviewer','reason':'Evidence reviewed'})
  assert r.status_code==200,r.text
 assert client.patch(f'/api/decision-ai/decisions/{ident}',headers=headers,json={'status':'measured','actor':'Reviewer','reason':'Reviewed'}).status_code==422
 r=client.patch(f'/api/decision-ai/decisions/{ident}',headers=headers,json={'status':'measured','actor':'Reviewer','reason':'Reviewed','measured_outcome':'Observation vs prior window: no attribution claimed'})
 assert r.status_code==200,r.text
 assert len(client.get(f'/api/decision-ai/decisions/{ident}/history').json())==6

def test_reject_short_series():
 with pytest.raises(Exception):model_eval([{'date':'2026-01-01','revenue':2}])
