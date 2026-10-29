"""Evidence-first observe -> detect -> recommend -> decide -> measure workflows.

No automatic business mutations; statistical findings are not claims of causality.
"""
import json
import math
import statistics
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from .core import db, now
from .decision_ai import DDL, authorize

router = APIRouter(prefix='/api/decision-loop', tags=['Evidence-backed decision loop'])
EXTRA = '''
CREATE TABLE IF NOT EXISTS evidence_insights (
 id INTEGER PRIMARY KEY AUTOINCREMENT, fingerprint TEXT NOT NULL UNIQUE,
 observed_date TEXT NOT NULL, detection_method TEXT NOT NULL,
 score REAL NOT NULL, observed_value REAL NOT NULL, expected_value REAL NOT NULL,
 evidence_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decision_measurements (
 id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id INTEGER NOT NULL,
 metric_key TEXT NOT NULL, baseline_start TEXT NOT NULL, baseline_end TEXT NOT NULL,
 after_start TEXT NOT NULL, after_end TEXT NOT NULL,
 baseline_mean REAL NOT NULL, after_mean REAL NOT NULL,
 delta_absolute REAL NOT NULL, delta_percent REAL,
 sample_days INTEGER NOT NULL, evidence_json TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(decision_id) REFERENCES governed_decisions(id));
'''

def initialize(c):
 c.executescript(DDL + EXTRA)

def detect_sales_anomalies(points, threshold=3.5):
 """Historical leave-one-out same-weekday MAD, minimum 8 comparator days.

 Only compares past days to earlier observations, avoiding look-ahead.
 """
 if not 2 <= threshold <= 10: raise ValueError('Unsupported detection threshold')
 result=[]
 history={i:[] for i in range(7)}
 previous=None
 for p in points:
  day=date.fromisoformat(p['date']);value=float(p['revenue'])
  if not math.isfinite(value) or value<0:raise ValueError('Invalid source revenue')
  if previous and day<=previous:raise ValueError('Dates must be strictly increasing')
  previous=day
  weekday=day.weekday(); samples=history[weekday]
  # At most 12 prior same-weekday observations: comparison stays local to season.
  baseline=samples[-12:]
  if len(baseline)>=8:
   median=statistics.median(baseline)
   mad=statistics.median(abs(x-median) for x in baseline)
   # Constant baseline: do not divide by zero; flag non-zero deviation only.
   denominator=max(1.4826*mad, max(median*.01, 1.0))
   score=abs(value-median)/denominator
   if score>=threshold:
    result.append({'date':day.isoformat(),'observed_sales_EGP':round(value,2),
      'expected_weekday_median_EGP':round(median,2),'robust_score':round(score,4),
      'direction':'above' if value>median else 'below','comparison_days':len(baseline),
      'method':'trailing_same_weekday_median_MAD',
      'limitations':['Statistical outlier, not a confirmed operational incident',
                     'Baseline is from preceding same-weekday sales only',
                     'Source sales reliability is warning pending reconciliation']})
  samples.append(value)
 return result

@router.post('/scan', dependencies=[Depends(authorize)])
def scan(threshold:float=3.5):
 c=db()
 try:
  initialize(c)
  points=[dict(r) for r in c.execute('SELECT date,revenue FROM daily_sales ORDER BY date')]
  if len(points)<70:raise HTTPException(422,'At least 70 historical observations required')
  from hashlib import sha256
  found=detect_sales_anomalies(points,threshold)
  added=0
  for record in found:
   fingerprint=sha256(f"{record['date']}:{record['method']}:{threshold}".encode()).hexdigest()
   cur=c.execute('INSERT OR IGNORE INTO evidence_insights(fingerprint,observed_date,detection_method,score,observed_value,expected_value,evidence_json,created_at) VALUES (?,?,?,?,?,?,?,?)',
    (fingerprint,record['date'],record['method'],record['robust_score'],record['observed_sales_EGP'],record['expected_weekday_median_EGP'],json.dumps(record),now()))
   added+=cur.rowcount
  c.commit()
  return {'method':'trailing_same_weekday_median_MAD','threshold':threshold,'observations_checked':len(points),'anomalies_detected':len(found),'new_insights_saved':added,'source_trust':'warning','status':'statistical_findings_not_confirmed_causes'}
 finally:c.close()

@router.get('/insights')
def insights(limit:int=20):
 if not 1<=limit<=100:raise HTTPException(422,'limit out of range')
 c=db()
 try:
  initialize(c)
  records=[dict(r) for r in c.execute('SELECT * FROM evidence_insights ORDER BY observed_date DESC,id DESC LIMIT ?',(limit,))]
  for r in records:
   r['evidence']=json.loads(r.pop('evidence_json'))
   r['recommendation']={'action':'Investigate the observed daily sales deviation and verify transaction quality before intervening',
    'requires_human_approval':True,'estimated_impact':'unknown','priority':'review',
    'basis':'Statistical anomaly plus reported source limitations'}
  return {'insights':records,'count':len(records),'trust':'warning'}
 finally:c.close()

class InsightDecision(BaseModel):
 insight_id:int=Field(gt=0)
 case_id:str=Field(min_length=1)
 owner:str=Field(min_length=2,max_length=100)
 actor:str=Field(min_length=2,max_length=100)

@router.post('/decisions/from-insight',dependencies=[Depends(authorize)])
def from_insight(payload:InsightDecision):
 c=db()
 try:
  initialize(c)
  insight=c.execute('SELECT * FROM evidence_insights WHERE id=?',(payload.insight_id,)).fetchone()
  if insight is None:raise HTTPException(404,'Insight not found')
  if c.execute('SELECT 1 FROM cases WHERE id=?',(payload.case_id,)).fetchone() is None:raise HTTPException(404,'Case not found')
  evidence=json.loads(insight['evidence_json'])
  stamp=now(); title=f"Investigate sales anomaly on {insight['observed_date']}"
  cur=c.execute('INSERT INTO governed_decisions(case_id,title,action,owner,status,evidence_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',
   (payload.case_id,title,'Verify sales source transactions and compare against preceding weekdays; request approval before intervention',payload.owner,'proposed',json.dumps({'insight_id':payload.insight_id,'finding':evidence,'source_trust':'warning'}),stamp,stamp))
  decision_id=cur.lastrowid
  c.execute('INSERT INTO governed_decision_events(decision_id,actor,previous_status,next_status,reason,created_at) VALUES(?,?,?,?,?,?)',
    (decision_id,payload.actor,None,'proposed',f'Created from evidence insight #{payload.insight_id}',stamp))
  c.commit();return {'decision_id':decision_id,'status':'proposed','insight_id':payload.insight_id,'approval_required':True}
 finally:c.close()

class Measurement(BaseModel):
 metric_key:str=Field(default='net_sales',pattern='^net_sales$')
 baseline_start:date
 baseline_end:date
 after_start:date
 after_end:date

@router.post('/decisions/{decision_id}/measure',dependencies=[Depends(authorize)])
def measure(decision_id:int,request:Measurement):
 if not (request.baseline_start<=request.baseline_end<request.after_start<=request.after_end):
  raise HTTPException(422,'Windows must be ordered and non-overlapping')
 if (request.baseline_end-request.baseline_start).days>90 or (request.after_end-request.after_start).days>90:
  raise HTTPException(422,'Maximum window is 91 days')
 c=db()
 try:
  initialize(c)
  dec=c.execute('SELECT status FROM governed_decisions WHERE id=?',(decision_id,)).fetchone()
  if dec is None:raise HTTPException(404,'Decision not found')
  if dec['status'] not in ('implemented','measured','closed'):raise HTTPException(409,'Decision must be implemented before measuring')
  def daily(start,end):
   return [dict(r) for r in c.execute('SELECT date,revenue FROM daily_sales WHERE date BETWEEN ? AND ? ORDER BY date',(str(start),str(end)))]
  before=daily(request.baseline_start,request.baseline_end);after=daily(request.after_start,request.after_end)
  expected_before=(request.baseline_end-request.baseline_start).days+1
  expected_after=(request.after_end-request.after_start).days+1
  if len(before)!=expected_before or len(after)!=expected_after:raise HTTPException(422,'Incomplete daily data in one or both windows')
  a=statistics.mean(x['revenue'] for x in before);b=statistics.mean(x['revenue'] for x in after)
  pct=(b-a)/a*100 if a else None
  evidence={'method':'descriptive_pre_post_daily_mean','trust':'warning','causality':'not_established',
    'limitations':['No control group or seasonality correction','A change does not prove the decision caused it','Source sales not fully reconciled']}
  cur=c.execute('INSERT INTO decision_measurements(decision_id,metric_key,baseline_start,baseline_end,after_start,after_end,baseline_mean,after_mean,delta_absolute,delta_percent,sample_days,evidence_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
   (decision_id,request.metric_key,str(request.baseline_start),str(request.baseline_end),str(request.after_start),str(request.after_end),a,b,b-a,pct,len(before)+len(after),json.dumps(evidence),now()))
  c.commit()
  return {'measurement_id':cur.lastrowid,'decision_id':decision_id,'baseline_daily_mean_EGP':round(a,2),
   'after_daily_mean_EGP':round(b,2),'change_EGP_per_day':round(b-a,2),'change_percent':round(pct,2) if pct is not None else None,
   'baseline_days':len(before),'after_days':len(after),**evidence}
 finally:c.close()

@router.get('/decisions/{decision_id}/measurements')
def measurements(decision_id:int):
 c=db()
 try:
  initialize(c)
  out=[dict(r) for r in c.execute('SELECT * FROM decision_measurements WHERE decision_id=? ORDER BY id',(decision_id,))]
  for r in out:r['evidence']=json.loads(r.pop('evidence_json'))
  return out
 finally:c.close()
