"""Transparent ML baselines, deterministic evidence copilot, and governed decisions.
No hosted LLM or speculative outcome inference.
"""
import hashlib, json, math, os, statistics
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from .core import db, now

router=APIRouter(prefix='/api/decision-ai',tags=['ML and Decisions'])
DDL='''
CREATE TABLE IF NOT EXISTS ml_runs(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, model TEXT NOT NULL, target TEXT NOT NULL, fingerprint TEXT NOT NULL, train_end TEXT NOT NULL, test_start TEXT NOT NULL, test_end TEXT NOT NULL, mae REAL NOT NULL, wape REAL, baseline_mae REAL NOT NULL, selected TEXT NOT NULL, evaluation_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS governed_decisions(id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL, title TEXT NOT NULL, action TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL, evidence_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, measured_outcome TEXT, FOREIGN KEY(case_id) REFERENCES cases(id));
CREATE TABLE IF NOT EXISTS governed_decision_events(id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id INTEGER NOT NULL, actor TEXT NOT NULL, previous_status TEXT, next_status TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL);
'''

def query(sql,params=()):
 c=db()
 try:
  c.executescript(DDL)
  return [dict(r) for r in c.execute(sql,params).fetchall()]
 finally:c.close()

def authorize(request: __import__('fastapi').Request, x_nexus_token:str|None=Header(default=None)):
 from . import auth
 return auth.require_write(request,x_nexus_token)

def model_eval(points):
 """Hold out last 28 observations; compare 7-day seasonal naive to last-value naive."""
 if len(points)<70:raise HTTPException(422,'At least 70 dated observations required')
 dates=[date.fromisoformat(x['date']) for x in points]
 if any((b-a).days!=1 for a,b in zip(dates,dates[1:])):raise HTTPException(422,'Daily series is not contiguous; calendar reconstruction required')
 values=[float(p['revenue']) for p in points]
 if not all(math.isfinite(v) and v>=0 for v in values):raise HTTPException(422,'Invalid daily revenue values')
 start=len(values)-28
 actual=values[start:]
 seasonal=[values[i-7] for i in range(start,len(values))]
 naive=[values[i-1] for i in range(start,len(values))]
 mae=lambda predicted:sum(abs(a-p) for a,p in zip(actual,predicted))/len(actual)
 sm,nm=mae(seasonal),mae(naive)
 chosen='seasonal_naive_7d' if sm<=nm else 'last_observation_naive'
 pred=seasonal if sm<=nm else naive
 wape=100*sum(abs(a-p) for a,p in zip(actual,pred))/sum(abs(a) for a in actual) if sum(abs(a) for a in actual)>0 else None
 return {'chosen':chosen,'mae':round(min(sm,nm),4),'baseline_mae':round(nm,4),'seasonal_mae':round(sm,4),'wape':round(wape,4) if wape is not None else None,'train_end':points[start-1]['date'],'test_start':points[start]['date'],'test_end':points[-1]['date'],'holdout_days':28,'limitations':['Observed sales are not unconstrained demand','Evaluation is a single holdout; no causal or inventory claims','Sales source trust is warning pending reconciliation']}

@router.post('/ml/train',dependencies=[Depends(authorize)])
def train():
 points=query('SELECT date,revenue FROM daily_sales ORDER BY date')
 result=model_eval(points)
 fingerprint=hashlib.sha256(json.dumps(points,separators=(',',':')).encode()).hexdigest()
 c=db()
 try:
  c.executescript(DDL)
  cursor=c.execute('INSERT INTO ml_runs(created_at,model,target,fingerprint,train_end,test_start,test_end,mae,wape,baseline_mae,selected,evaluation_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
   (now(),'validated_naive_comparison','observed_daily_sales_EGP',fingerprint,result['train_end'],result['test_start'],result['test_end'],result['mae'],result['wape'],result['baseline_mae'],result['chosen'],json.dumps(result)))
  c.commit();run_id=cursor.lastrowid
 finally:c.close()
 return {'run_id':run_id,'status':'evaluated_not_deployed','evaluation':result,'dataset_fingerprint':fingerprint}

@router.get('/ml/runs')
def runs():return query('SELECT id,created_at,model,target,fingerprint,train_end,test_start,test_end,mae,wape,baseline_mae,selected FROM ml_runs ORDER BY id DESC LIMIT 50')

@router.get('/ml/forecast')
def forecast(days:int=7):
 if not 1<=days<=28:raise HTTPException(422,'days must be between 1 and 28')
 runs=query('SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1')
 if not runs:raise HTTPException(503,'No evaluated model. Run the explicitly authorized training endpoint.')
 points=query('SELECT date,revenue FROM daily_sales ORDER BY date')
 fingerprint=hashlib.sha256(json.dumps(points,separators=(',',':')).encode()).hexdigest()
 run=runs[0]
 if run['fingerprint']!=fingerprint:raise HTTPException(409,'Sales series changed since model evaluation; rerun training')
 ev=json.loads(run['evaluation_json'])
 vals=[float(p['revenue']) for p in points]
 last=date.fromisoformat(points[-1]['date']); predictions=[]
 for i in range(days):
  pred=vals[-7] if run['selected']=='seasonal_naive_7d' else vals[-1]
  vals.append(pred)
  predictions.append({'date':(last+timedelta(days=i+1)).isoformat(),'predicted_sales_EGP':round(pred,2)})
 return {'run_id':run['id'],'model':run['selected'],'status':'evaluated_not_deployed','predictions':predictions,'evaluation':ev,'uncertainty_intervals':'unavailable_not_calibrated','trust':'warning','source':'daily_sales derived from sales_order_items.csv'}

class Question(BaseModel):
 intent:str=Field(pattern='^(metrics|open_cases|decisions|model_status)$')
 language:str=Field(default='en',pattern='^(en|ar)$')

@router.post('/copilot/query')
def copilot(request:Question):
 """Allowlisted deterministic analytical tools: not a hosted LLM or semantic free text."""
 if request.intent=='metrics':
  evidence=query('SELECT key,value,unit,trust,definition,source,updated_at FROM metrics ORDER BY key')
  tool='metric_registry'
 elif request.intent=='open_cases':
  evidence=query("SELECT id,title,severity,status,updated_at FROM cases WHERE status NOT IN ('resolved','dismissed') ORDER BY severity,id")
  tool='case_registry'
 elif request.intent=='decisions':
  evidence=query('SELECT id,case_id,title,owner,status,updated_at FROM governed_decisions ORDER BY id DESC LIMIT 50')
  tool='decision_registry'
 else:
  evidence=runs();tool='evaluated_model_registry'
 msg={'metrics':'Metrics include source reliability classifications.','open_cases':'Open investigations require source reconciliation.','decisions':'These are human-governed actions, not automated business changes.','model_status':'Only evaluated model runs are listed; no model is claimed deployed.'}
 return {'mode':'deterministic_tool_assistant_not_llm','tool':tool,'answer':msg[request.intent],'evidence':evidence,'evidence_count':len(evidence),'source_reliability':'mixed_check_each_record','language':request.language,'limitations':['No causal claims','No automatic mutation','No natural-language orchestration without configured and validated LLM']}

class DecisionCreate(BaseModel):
 case_id:str
 title:str=Field(min_length=4,max_length=160)
 action:str=Field(min_length=8,max_length=2000)
 owner:str=Field(min_length=2,max_length=100)
 evidence_keys:list[str]=Field(min_length=1,max_length=15)
 actor:str=Field(min_length=2,max_length=100)

@router.post('/decisions',dependencies=[Depends(authorize)])
def create_decision(payload:DecisionCreate):
 c=db()
 try:
  c.executescript(DDL)
  if not c.execute('SELECT 1 FROM cases WHERE id=?',(payload.case_id,)).fetchone():raise HTTPException(404,'Case not found')
  available={r[0] for r in c.execute('SELECT key FROM metrics')}
  if not set(payload.evidence_keys)<=available:raise HTTPException(422,'Unknown evidence metric key')
  stamp=now()
  cursor=c.execute('INSERT INTO governed_decisions(case_id,title,action,owner,status,evidence_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(payload.case_id,payload.title,payload.action,payload.owner,'proposed',json.dumps(payload.evidence_keys),stamp,stamp))
  ident=cursor.lastrowid
  c.execute('INSERT INTO governed_decision_events(decision_id,actor,previous_status,next_status,reason,created_at) VALUES(?,?,?,?,?,?)',(ident,payload.actor,None,'proposed','Created with validated metric references',stamp))
  c.commit()
 finally:c.close()
 return {'id':ident,'status':'proposed'}

TRANSITIONS={'proposed':{'reviewed','rejected','cancelled'},'reviewed':{'approved','rejected','cancelled'},'approved':{'in_progress','cancelled'},'in_progress':{'implemented','cancelled'},'implemented':{'measured'},'measured':{'closed'},'closed':set(),'rejected':set(),'cancelled':set()}
class Transition(BaseModel):
 status:str
 actor:str=Field(min_length=2,max_length=100)
 reason:str=Field(min_length=4,max_length=2000)
 measured_outcome:str|None=None

@router.patch('/decisions/{decision_id}',dependencies=[Depends(authorize)])
def transition(decision_id:int,payload:Transition):
 c=db()
 try:
  c.executescript(DDL)
  old=c.execute('SELECT status FROM governed_decisions WHERE id=?',(decision_id,)).fetchone()
  if not old:raise HTTPException(404,'Decision not found')
  if payload.status not in TRANSITIONS[old[0]]:raise HTTPException(409,f'Invalid transition from {old[0]} to {payload.status}')
  if payload.status=='measured' and not payload.measured_outcome:raise HTTPException(422,'Measurement and baseline evidence description required')
  stamp=now()
  c.execute('UPDATE governed_decisions SET status=?,updated_at=?,measured_outcome=COALESCE(?,measured_outcome) WHERE id=?',(payload.status,stamp,payload.measured_outcome,decision_id))
  c.execute('INSERT INTO governed_decision_events(decision_id,actor,previous_status,next_status,reason,created_at) VALUES(?,?,?,?,?,?)',(decision_id,payload.actor,old[0],payload.status,payload.reason,stamp));c.commit()
 finally:c.close()
 return {'id':decision_id,'status':payload.status}

@router.get('/decisions')
def decisions():return query('SELECT * FROM governed_decisions ORDER BY id DESC LIMIT 100')
@router.get('/decisions/{decision_id}/history')
def history(decision_id:int):return query('SELECT * FROM governed_decision_events WHERE decision_id=? ORDER BY id',(decision_id,))
