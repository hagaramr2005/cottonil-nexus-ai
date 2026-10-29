"""V8: bounded, deterministic contextual assistant and advisory recommendations.
Never executes model-authored SQL or creates decisions automatically.
"""
import json
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from .core import db

router=APIRouter(prefix='/api/client',tags=['Client intelligence'])

def read(query,args=()):
    conn=db()
    try:return [dict(x) for x in conn.execute(query,args).fetchall()]
    finally:conn.close()

def translate(en,ar,lang):return ar if lang=='ar' else en

def language(lang):
    if lang not in ('en','ar'):raise HTTPException(422,'Unsupported language')

@router.get('/recommendations')
def recommendations(lang:str='en',limit:int=Query(12,ge=1,le=40)):
    language(lang)
    result=[]
    for c in read("SELECT id,title,status,severity,evidence_json FROM cases WHERE status NOT IN ('resolved','dismissed') ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 ELSE 2 END,id LIMIT ?",(limit,)):
        sources=json.loads(c['evidence_json']) if c['evidence_json'] else []
        result.append({'id':'case:'+c['id'],'type':'investigation','title':translate('Review: ','مراجعة: ',lang)+c['title'],
          'context':translate('Unresolved recorded investigation','تحقيق مسجل لم يتم حسمه',lang),
          'evidence':sources,'source':['cases'],'case_id':c['id'],'priority':c['severity'],
          'action':translate('Examine observations and source evidence, then assign a human owner.','افحص المشاهدات والمصادر وحدد مسؤولًا عن المتابعة.',lang),
          'assumptions':[translate('An alert is not proof of a loss or wrongdoing.','التنبيه لا يثبت حدوث خسارة أو مخالفة.',lang)],
          'estimated_benefit':None,'approval':'human_required','confidence':'not_calibrated'})
    available=limit-len(result)
    if available>0:
        ms=read("SELECT key,definition,source,trust FROM metrics WHERE trust IN ('warning','unverified','blocked') ORDER BY key LIMIT ?",(available,))
        for m in ms:
            result.append({'id':'quality:'+m['key'],'type':'data_quality',
              'title':translate('Verify metric: ','راجع تعريف المؤشر: ',lang)+m['key'],
              'context':m['definition'],'evidence':[m['key'],m['trust']], 'source':[m['source']],
              'case_id':None,'priority':'review','action':translate('Reconcile source units, period and coverage before interpreting.','طابق الوحدات والفترة وتغطية المصدر قبل التفسير.',lang),
              'assumptions':[translate('The reliability state comes from the existing metric ledger.','حالة الموثوقية مستمدة من سجل المؤشرات الحالي.',lang)],
              'estimated_benefit':None,'approval':'human_required','confidence':'not_calibrated'})
    return {'recommendations':result,'mode':'rule-based-advisory','limitations':[translate('No projected savings or causal claim. No recommendations execute automatically.','لا تقديرات وفورات أو ادعاءات سببية ولا يتم تنفيذ توصيات تلقائيًا.',lang)]}

class ContextQuestion(BaseModel):
    question:str=Field(min_length=3,max_length=500)
    page:str=Field(default='overview',max_length=50)
    case_id:str|None=Field(default=None,max_length=150)
    sku_id:str|None=Field(default=None,max_length=150)
    metric_id:str|None=Field(default=None,max_length=150)
    lang:str='en'

@router.post('/ask')
def context_ask(body:ContextQuestion):
    language(body.lang)
    allowed_pages={'overview','briefing','sales','trust','cases','money','sku','risk','change','decision','anomaly','passport','graph','ai','reports','settings'}
    if body.page not in allowed_pages:raise HTTPException(422,'Unsupported workspace')
    facts=[];sources=[];next_steps=[]
    if body.case_id:
        found=read('SELECT * FROM cases WHERE id=?',(body.case_id,))
        if not found:raise HTTPException(404,'Investigation not found')
        c=found[0];facts.append({'type':'investigation','id':c['id'],'title':c['title'],'status':c['status'],'severity':c['severity'],
           'observations':json.loads(c['observations_json']),'hypotheses_not_facts':json.loads(c['hypotheses_json']),
           'evidence':json.loads(c['evidence_json'])})
        sources+=['cases',*json.loads(c['evidence_json'])]
        next_steps.append(translate('Review supporting evidence and missing validation before a decision.','راجع الأدلة والتحقق المطلوب قبل اتخاذ القرار.',body.lang))
    if body.sku_id:
        sku=read('SELECT sku_id,revenue,units,margin,lines FROM sku_sales WHERE sku_id=?',(body.sku_id,))
        if not sku:raise HTTPException(404,'SKU not found')
        facts.append({'type':'sku','values':sku[0]});sources.append('sku_sales <= sales_order_items.csv')
        next_steps.append(translate('Inspect the SKU source and cost coverage; do not infer its profitability from sales alone.','افحص مصدر المنتج وتغطية التكلفة ولا تستنتج ربحيته من المبيعات وحدها.',body.lang))
    if body.metric_id:
        metric=read('SELECT * FROM metrics WHERE key=?',(body.metric_id,))
        if not metric:raise HTTPException(404,'Metric not found')
        facts.append({'type':'metric','values':metric[0]});sources.append(metric[0]['source'])
    if not facts:
        q=body.question.lower()
        mapping=[('net_sales',['revenue','sales','مبيعات','الإيرادات']),('sales_orders',['orders','طلبات']),('refunds',['refund','استرداد']),('purchase_sales_ratio',['purchase','procurement','شراء','مشتريات'])]
        keys=[key for key,terms in mapping if any(t in q for t in terms)]
        if body.page in ('overview','briefing') and not keys:keys=['net_sales','sales_orders']
        if body.page=='money' and not keys:keys=['net_sales','margin','refunds']
        if body.page=='trust' and not keys:keys=['purchase_sales_ratio']
        if keys:
            placeholders=','.join('?' for _ in keys)
            selected=read(f'SELECT * FROM metrics WHERE key IN ({placeholders})',keys)
            facts=[{'type':'metric','values':m} for m in selected];sources+=[m['source'] for m in selected]
        if body.page in ('cases','anomaly','risk'):
            selected=read("SELECT id,title,status,severity FROM cases WHERE status NOT IN ('resolved','dismissed') ORDER BY id LIMIT 8")
            facts.extend({'type':'investigation_summary',**c} for c in selected);sources.append('cases')
    if not facts:
        return {'mode':'deterministic-context','supported':False,'answer':translate('No approved analytical evidence supports this question in the current context. Specify a metric, SKU or investigation.','لا تتوفر أدلة تحليلية معتمدة لهذا السؤال في السياق الحالي. حدّد مؤشرًا أو منتجًا أو تحقيقًا.',body.lang),'facts':[],'sources':[],'next_actions':[], 'limitations':['No inferred facts or unrestricted SQL.']}
    answer=translate('These are the recorded facts for the selected context. Review their trust labels, sources and unresolved assumptions before acting.','هذه هي الحقائق المسجلة للسياق المحدد. راجع درجة موثوقيتها ومصادرها والافتراضات غير المحسومة قبل اتخاذ إجراء.',body.lang)
    return {'mode':'deterministic-context','supported':True,'answer':answer,'facts':facts,'sources':sorted(set(sources)),
       'next_actions':next_steps or [translate('Open a source or investigation to continue verifying the finding.','افتح المصدر أو التحقيق لمتابعة التحقق من النتيجة.',body.lang)],
       'limitations':[translate('Correlations and investigation flags do not establish causes or losses.','الارتباطات والتنبيهات لا تثبت الأسباب أو الخسائر.',body.lang)]}
