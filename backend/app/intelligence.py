"""Read-only, evidence-aware analytical routes over validated existing aggregates.

These routes do not assert causality or inventory cost reconciliation.
"""
from fastapi import APIRouter, HTTPException, Query
from .core import db

router = APIRouter(prefix='/api/intelligence', tags=['Intelligence V4'])

def query(sql, params=()):
    connection=db()
    try: return [dict(x) for x in connection.execute(sql,params).fetchall()]
    finally: connection.close()

@router.get('/risk')
def risk():
    metrics={m['key']:m for m in query('SELECT key,value,unit,trust,definition,source FROM metrics')}
    cases=query('SELECT id,title,severity,status,updated_at FROM cases ORDER BY id')
    signals=[]
    for case in cases:
        keys={'NEX-001':['purchase_sales_ratio','purchased_units','sold_units'],
              'NEX-002':['marketing_attributed_orders','sales_orders'],
              'NEX-003':['orders_before_branch_open','sales_orders']}.get(case['id'],[])
        signals.append({**case, 'rule_id':f'case-link:{case["id"]}',
            'classification':'observed investigation lead',
            'metrics':[metrics[k] for k in keys if k in metrics],
            'confidence':None,
            'interpretation':'Requires source reconciliation; not a predicted financial loss.'})
    return {'signals':signals,'summary':{'total':len(signals),
        'critical':sum(x['severity']=='critical' for x in signals),
        'high':sum(x['severity']=='high' for x in signals),
        'unresolved':sum(x['status'] not in ('resolved','dismissed') for x in signals)},
        'limitations':['Risk severity is rule-based, not a calibrated probability.',
                       'No monetary loss should be inferred from procurement quantity gaps.']}

@router.get('/periods')
def periods():
    if not query("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_mart'"):
        raise HTTPException(503,'Sales mart unavailable. Run scripts/build_sales_mart.py')
    return {'months':[r['month'] for r in query('SELECT DISTINCT month FROM sales_mart ORDER BY month')]}

@router.get('/compare')
def compare(current:str=Query(...,pattern=r'^\d{4}-\d{2}$'),previous:str=Query(...,pattern=r'^\d{4}-\d{2}$'),limit:int=Query(12,ge=1,le=50)):
    if current==previous:raise HTTPException(422,'Choose two different months')
    if not query("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_mart'"):
        raise HTTPException(503,'Sales mart unavailable. Run scripts/build_sales_mart.py')
    def totals(m):
        row=query('SELECT ROUND(COALESCE(SUM(net),0),2) revenue,ROUND(COALESCE(SUM(units),0),2) units,COUNT(*) cells FROM sales_mart WHERE month=?',(m,))[0]
        return row
    a,b=totals(current),totals(previous)
    if not a['cells'] or not b['cells']:raise HTTPException(404,'No sales mart data for one or both selected months')
    def breakdown(dimension):
        # dimension comes from a fixed internal allowlist only
        assert dimension in ('branch_id','product_id','channel')
        sql=f'''SELECT {dimension} label,
            ROUND(SUM(CASE WHEN month=? THEN net ELSE 0 END),2) current_revenue,
            ROUND(SUM(CASE WHEN month=? THEN net ELSE 0 END),2) previous_revenue
            FROM sales_mart WHERE month IN (?,?) GROUP BY {dimension}
            ORDER BY ABS(SUM(CASE WHEN month=? THEN net ELSE -net END)) DESC LIMIT ?'''
        items=query(sql,(current,previous,current,previous,current,limit))
        return [{**x,'delta':round(x['current_revenue']-x['previous_revenue'],2)} for x in items]
    delta=round(a['revenue']-b['revenue'],2)
    return {'current':{'month':current,**a},'previous':{'month':previous,**b},
            'delta':delta,'change_pct':round(delta/b['revenue']*100,2) if b['revenue'] else None,
            'branches':breakdown('branch_id'),'products':breakdown('product_id'),
            'channels':breakdown('channel'),
            'trust':'warning','source':'sales_mart derived from original Cottonil sales order lines',
            'limitations':['Revenue movement is observational, not proof of cause.',
                           'Data completeness and business coverage between periods are not validated.']}

@router.get('/sku/{sku_id}')
def sku(sku_id:str):
    base=query('SELECT s.sku_id,s.units,s.revenue,s.margin,s.lines,p.units purchased_units,p.line_cost purchase_line_cost FROM sku_sales s LEFT JOIN sku_purchases p ON p.sku_id=s.sku_id WHERE s.sku_id=?',(sku_id,))
    if not base:raise HTTPException(404,'SKU not found')
    trend=[]
    if query("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_mart'"):
        # Existing mart uses product_id rather than SKU ID. Do not join across unverified key spaces.
        trend=[]
    return {'sku':base[0], 'cases':[], 'trend':trend,
            'trust':{'revenue':'warning','margin':'warning','purchased_units':'unverified'},
            'limitations':['Sales SKU identity is not validated against sales mart product_id.',
                           'Purchase and sold quantities may have different units or reporting windows.',
                           'Reported margin uses source-provided line margin and requires cost reconciliation.'],
            'sources':['sales_order_items.csv','purchase_order_items.csv']}
