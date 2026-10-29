from datetime import date,timedelta
import pytest
from fastapi.testclient import TestClient
from app import core
from app.main import app
from app.decision_loop import detect_sales_anomalies

@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(core,'DB',tmp_path/'loop.sqlite')
 monkeypatch.setenv('NEXUS_WRITE_TOKEN','test-token')
 with core.db() as c:
  for i in range(112):
   day=(date(2026,1,1)+timedelta(days=i)).isoformat()
   value=9999.0 if i==105 else float(100+i%7*5)
   c.execute('INSERT INTO daily_sales VALUES(?,?,?,?,?)',(day,value,2,3,1))
  c.execute("INSERT INTO cases VALUES('NEX-001','Source investigation','high','open','[]','[]','[]','now','now')")
  c.commit()
 return TestClient(app)

def test_detection_no_future_leakage():
 points=[{'date':str(date(2026,1,1)+timedelta(days=i)),'revenue':9999. if i==105 else 100.} for i in range(112)]
 findings=detect_sales_anomalies(points)
 assert any(x['date']==points[105]['date'] for x in findings)
 assert all(x['comparison_days']<=12 for x in findings)

def test_scan_is_idempotent_and_requires_auth(client):
 path='/api/decision-loop/scan'
 assert client.post(path).status_code==403
 headers={'x-nexus-token':'test-token'}
 first=client.post(path,headers=headers)
 assert first.status_code==200,first.text
 assert first.json()['anomalies_detected']>=1
 second=client.post(path,headers=headers)
 assert second.json()['new_insights_saved']==0
 assert len(client.get('/api/decision-loop/insights').json()['insights'])>=1

def test_insight_to_approved_decision_to_measurement(client):
 headers={'x-nexus-token':'test-token'}
 client.post('/api/decision-loop/scan',headers=headers)
 insight=client.get('/api/decision-loop/insights').json()['insights'][0]
 result=client.post('/api/decision-loop/decisions/from-insight',headers=headers,json={
  'insight_id':insight['id'],'case_id':'NEX-001','owner':'Reviewer','actor':'Reviewer'})
 assert result.status_code==200,result.text
 decision=result.json()['decision_id']
 payload={'baseline_start':'2026-01-15','baseline_end':'2026-01-21','after_start':'2026-01-22','after_end':'2026-01-28'}
 endpoint=f'/api/decision-loop/decisions/{decision}/measure'
 assert client.post(endpoint,headers=headers,json=payload).status_code==409
 for status in ['reviewed','approved','in_progress','implemented']:
  r=client.patch(f'/api/decision-ai/decisions/{decision}',headers=headers,json={'status':status,'actor':'Reviewer','reason':'Reviewed source evidence'})
  assert r.status_code==200,r.text
 measured=client.post(endpoint,headers=headers,json=payload)
 assert measured.status_code==200,measured.text
 assert measured.json()['causality']=='not_established'
 assert len(client.get(f'/api/decision-loop/decisions/{decision}/measurements').json())==1


def test_reject_missing_days_and_reverse_windows(client):
 headers={'x-nexus-token':'test-token'}
 client.post('/api/decision-loop/scan',headers=headers)
 insight=client.get('/api/decision-loop/insights').json()['insights'][0]
 dec=client.post('/api/decision-loop/decisions/from-insight',headers=headers,json={'insight_id':insight['id'],'case_id':'NEX-001','owner':'Reviewer','actor':'Reviewer'}).json()['decision_id']
 for status in ['reviewed','approved','in_progress','implemented']:
  client.patch(f'/api/decision-ai/decisions/{dec}',headers=headers,json={'status':status,'actor':'Reviewer','reason':'Reviewed evidence'})
 url=f'/api/decision-loop/decisions/{dec}/measure'
 assert client.post(url,headers=headers,json={'baseline_start':'2026-01-25','baseline_end':'2026-01-28','after_start':'2026-01-21','after_end':'2026-01-23'}).status_code==422
 assert client.post(url,headers=headers,json={'baseline_start':'2025-12-25','baseline_end':'2026-01-02','after_start':'2026-01-03','after_end':'2026-01-06'}).status_code==422
