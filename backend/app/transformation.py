"""V6 source-backed investigation features. No CV or synthetic financial claims."""
import json, math, statistics
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from .core import db, now

router=APIRouter(prefix='/api/transform',tags=['Evidence intelligence'])

def read(sql, args=()):
    con=db()
    try:return [dict(r) for r in con.execute(sql,args).fetchall()]
    finally:con.close()

def need_mart():
    if not read("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_mart'"):
        raise HTTPException(503,'Run scripts/build_sales_mart.py first')

@router.get('/passports')
def passports():
    records=read('SELECT * FROM metrics ORDER BY key')
    return {'passports':[dict(id=m['key'],name=m['key'].replace('_',' ').title(),value=m['value'],unit=m['unit'],formula=m['definition'],sources=[s.strip() for s in m['source'].split(';')],trust=m['trust'],updated_at=m['updated_at'],limitations=['A calculated number is not automatically a reconciled business fact.'] if m['trust']!='verified' else [],related_cases=[c['id'] for c in read('SELECT id,evidence_json FROM cases') if m['key'] in json.loads(c['evidence_json'])]) for m in records], 'trust_definitions':{'verified':'Validated record count or supported key consistency, not a business audit.','warning':'Computed but reconciliation or coverage requires review.','unverified':'Definition, unit, or linkage not independently reconciled.','blocked':'Unsafe to interpret as comparable until source definitions are resolved.'}}

@router.get('/anomalies')
def anomalies(limit:int=Query(40,ge=1,le=150),min_history:int=Query(6,ge=4,le=24)):
    need_mart()
    data=read('SELECT month,branch_id,ROUND(SUM(net),2) revenue, SUM(units) units FROM sales_mart GROUP BY month,branch_id ORDER BY branch_id,month')
    grouped=defaultdict(list)
    for x in data:grouped[x['branch_id']].append(x)
    findings=[]
    for branch,series in grouped.items():
        for i in range(min_history,len(series)):
            baseline=series[max(0,i-12):i]
            # Avoid comparisons with disjoint periods and zero-sales cells.
            if any((int(series[j]['month'][:4])*12+int(series[j]['month'][5:]))-(int(series[j-1]['month'][:4])*12+int(series[j-1]['month'][5:]))!=1 for j in range(i-len(baseline)+1,i+1)):
                continue
            reference=[float(x['revenue']) for x in baseline]
            median=statistics.median(reference)
            mad=statistics.median([abs(x-median) for x in reference])
            actual=float(series[i]['revenue'])
            if mad<1 or median<=0:continue
            score=.6745*(actual-median)/mad
            if abs(score)<3.5:continue
            period=series[i]['month']
            findings.append({'id':f'ANOM-{branch}-{period}-NET', 'entity_type':'branch','entity_id':branch,
              'period':period,'metric':'monthly_net_sales','actual':round(actual,2),
              'expected':round(median,2),'reference_mad':round(mad,2),'deviation_score':round(score,2),
              'method':'rolling 12-observation median/MAD; consecutive months only',
              'severity':'high' if abs(score)>=6 else 'medium','trust':'warning',
              'source':'sales_mart <= sales_order_items.csv','direction':'increase' if score>0 else 'decrease',
              'interpretation':'Statistical outlier; not proof of fraud, causal change or financial loss.',
              'case_id':f'INV-{branch}-{period}-NET'})
    findings.sort(key=lambda x:abs(x['deviation_score']),reverse=True)
    existing={x['id'] for x in read('SELECT id FROM cases')}
    result=findings[:limit]
    for x in result:x['has_case']=x['case_id'] in existing
    return {'signals':result,'scanned_branch_months':len(data),'total_detected':len(findings),
      'parameters':{'min_history':min_history,'threshold_abs_robust_z':3.5},
      'limitations':['Sales mart does not prove complete month coverage or seasonal comparability.', 'Rolling MAD may flag legitimate promotions; analysts must investigate.', 'Results are read-only until an investigation is opened.']}

class OpenAnomaly(BaseModel):
    anomaly_id:str=Field(min_length=12,max_length=130)
    owner:str=Field(default='analyst',min_length=2,max_length=80)

@router.post('/anomalies/open')
def open_anomaly_auth(body:OpenAnomaly,request:__import__('fastapi').Request,x_nexus_token:str|None=__import__('fastapi').Header(None)):
    from . import auth
    auth.require_write(request,x_nexus_token)
    matches=[x for x in anomalies(limit=150)['signals'] if x['id']==body.anomaly_id]
    if not matches:raise HTTPException(404,'Anomaly not in current bounded detection results')
    item=matches[0];cid=item['case_id'];con=db()
    try:
        if not con.execute('SELECT id FROM cases WHERE id=?',(cid,)).fetchone():
            title=f"Review {item['metric']} outlier · {item['entity_id']} · {item['period']}"
            con.execute('INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?)',(cid,title,item['severity'],'open',json.dumps([f"{item['actual']} vs rolling median {item['expected']}" ]),json.dumps(['Promotion, seasonality, incomplete reporting or genuine shift']),json.dumps([item['metric'],item['source'],item['id']]),now(),now()))
            con.execute('INSERT INTO events(case_id,kind,detail,actor,created_at) VALUES (?,?,?,?,?)',(cid,'anomaly','Created from '+item['id'],body.owner,now()))
        con.commit()
    finally:con.close()
    return {'case_id':cid,'created_or_existing':True,'anomaly_id':item['id']}

@router.get('/graph/sku/{sku_id}')
def sku_graph(sku_id:str):
    sku=read('SELECT sku_id,units,revenue,margin FROM sku_sales WHERE sku_id=?',(sku_id,))
    if not sku:raise HTTPException(404,'Unknown SKU')
    nodes=[{'id':'sku:'+sku_id,'type':'sku','label':sku_id}]
    edges=[]
    sold=read('SELECT sku_id,units,line_cost FROM sku_purchases WHERE sku_id=?',(sku_id,))
    for typ,source,value in [('sales','sales_order_items.csv',sku[0]['revenue'])]+([('procurement','purchase_order_items.csv',sold[0]['line_cost'])] if sold else []):
        node_id='source:'+source
        nodes.append({'id':node_id,'type':'dataset','label':source,'amount':value})
        edges.append({'source':'sku:'+sku_id,'target':node_id,'relation':typ,'trust':'warning' if typ=='sales' else 'unverified'})
    return {'nodes':nodes,'edges':edges,'limitations':['No unverified SKU-to-product or SKU-to-branch joins were invented.','This is a bounded evidence graph, not an exhaustive order graph.']}

@router.get('/revenue-xray')
def revenue_xray(current:str=Query(...,pattern=r'^\d{4}-\d{2}$'),previous:str=Query(...,pattern=r'^\d{4}-\d{2}$'),branch:str|None=None,channel:str|None=None):
    need_mart()
    if current==previous:raise HTTPException(422,'Choose different months')
    clauses=['month IN (?,?)'];args=[current,previous]
    if branch:clauses.append('branch_id=?');args.append(branch)
    if channel:clauses.append('channel=?');args.append(channel)
    where=' AND '.join(clauses)
    def agg(column):
        sql=f'SELECT month,ROUND(SUM({column}),2) value,COUNT(*) cells FROM sales_mart WHERE {where} GROUP BY month'
        return {x['month']:x for x in read(sql,args)}
    result={}
    for name,column in [('revenue','net'),('gross','gross'),('discount','discount'),('units','units'),('reported_margin','line_margin')]:
        values=agg(column)
        if name=='revenue' and (current not in values or previous not in values):raise HTTPException(404,'No comparable cells for requested months and filters')
        a=values.get(current,{}).get('value',0);b=values.get(previous,{}).get('value',0)
        result[name]={'current':a,'previous':b,'delta':round(a-b,2),'change_pct':round((a-b)*100/b,2) if b else None}
    contributions=[]
    for x in read(f'''SELECT branch_id label,ROUND(SUM(CASE WHEN month=? THEN net ELSE 0 END),2) a,ROUND(SUM(CASE WHEN month=? THEN net ELSE 0 END),2) b FROM sales_mart WHERE {where} GROUP BY branch_id''',[current,previous]+args):
        contributions.append({'label':x['label'],'delta':round(x['a']-x['b'],2),'current':x['a'],'previous':x['b']})
    contributions.sort(key=lambda x:abs(x['delta']),reverse=True)
    return {'current':current,'previous':previous,'filters':{'branch':branch,'channel':channel},'metrics':result,
       'branch_contributions':contributions[:20],
       'branch_reconciles':abs(sum(x['delta'] for x in contributions)-result['revenue']['delta'])<.06,
       'trust':'warning','source':'sales_mart','limitations':['Orders in aggregate cells are not additive unique order counts.','Observed changes do not establish causality.','Month coverage and reported margin require validation.']}
