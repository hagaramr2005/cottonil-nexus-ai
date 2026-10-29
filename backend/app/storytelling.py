"""Read-only, evidence-grounded client narratives; values always come from source-derived tables."""
from fastapi import APIRouter, HTTPException
from .core import db

router = APIRouter(prefix='/api/story', tags=['Client storytelling'])

GLOSSARY = {
 'net_sales': ('Net sales', 'صافي المبيعات', 'Sum of recorded sales-line net amounts; not independently audited cash receipts.', 'مجموع صافي مبالغ بنود المبيعات المسجلة وليس إثباتًا للمتحصلات النقدية.'),
 'sales_orders': ('Sales orders', 'طلبات البيع', 'Count of order records, not distinct customers.', 'عدد سجلات الطلبات وليس عدد العملاء المختلفين.'),
 'sold_units': ('Units sold', 'الوحدات المباعة', 'Recorded item quantities; comparability with purchase quantities is unverified.', 'مجموع كميات بنود البيع ولا يعني أنها قابلة للمقارنة مع كميات المشتريات.'),
 'purchase_sales_ratio': ('Purchase-to-sales quantity ratio', 'نسبة كميات الشراء إلى البيع', 'A raw quantity ratio; units and periods are not reconciled. Not financial leakage.', 'نسبة حسابية لكميات قد تختلف وحداتها وفتراتها وليست خسارة مالية.'),
 'margin': ('Recorded line margin', 'هامش الربح المسجل', 'Sum of line margins subject to the validity of underlying cost fields.', 'مجموع هوامش بنود البيع وفق دقة بيانات التكلفة.'),
 'refunds': ('Recorded refunds', 'المرتجعات المالية المسجلة', 'Sum of recorded refund amounts; accounting recognition is not independently verified.', 'مجموع مبالغ الاسترداد المسجلة دون مراجعة محاسبية مستقلة.'),
}

def get_rows(sql, params=()):
 c=db()
 try:return [dict(r) for r in c.execute(sql,params).fetchall()]
 finally:c.close()

def local(en, ar, language):return ar if language=='ar' else en

def metric_story(metric, language):
 key=metric['key']; en, ar, meaning_en, meaning_ar = GLOSSARY.get(key,(key.replace('_',' ').title(),key.replace('_',' '),metric['definition'],metric['definition']))
 trust=metric['trust']
 unverified=trust!='verified'
 return {
  'id':key, 'title':local(en,ar,language), 'value':metric['value'], 'unit':metric['unit'], 'trust':trust,
  'what':local(meaning_en, meaning_ar, language),
  'meaning':local('This is the recorded source-derived total, not a prediction.','هذا إجمالي محسوب من السجلات وليس توقعًا.',language),
  'assessment':local('A performance verdict requires an agreed target or comparable period; neither is implied by this total.','الحكم على الأداء يتطلب هدفًا متفقًا عليه أو فترة مقارنة مناسبة ولا يكفي الرقم وحده.',language),
  'change':local('A change cannot be attributed without a comparable period and supporting source breakdown.','لا يمكن تفسير سبب التغير دون مقارنة فترة مناسبة وتحليل مصادر البيانات.',language),
  'next_action':local('Review the source definition and related investigation before making a decision.','راجِع تعريف المؤشر والتحقيقات المرتبطة به قبل اتخاذ القرار.',language),
  'reliability':local('Requires reconciliation or coverage review.' if unverified else 'Calculated from a defined source; not a complete independent audit.', 'يحتاج إلى مطابقة أو مراجعة التغطية.' if unverified else 'محسوب من مصدر محدد ولا يمثل تدقيقًا مستقلًا شاملًا.',language),
  'sources':[s.strip() for s in metric['source'].split(';') if s.strip()],
  'formula':metric['definition'], 'comparison_available':False,
 }

@router.get('/metrics/{metric_id}')
def explain_metric(metric_id:str, lang:str='en'):
 if lang not in ('en','ar'):raise HTTPException(422,'Unsupported language')
 result=get_rows('SELECT key,value,unit,definition,source,trust FROM metrics WHERE key=?',(metric_id,))
 if not result:raise HTTPException(404,'Metric not present in ingested sources')
 return metric_story(result[0],lang)

@router.get('/chart/daily-sales')
def explain_daily_chart(lang:str='en'):
 if lang not in ('en','ar'):raise HTTPException(422,'Unsupported language')
 points=get_rows('SELECT date,revenue FROM daily_sales ORDER BY date DESC LIMIT 90')[::-1]
 if len(points)<2:return {'available':False,'reason':local('At least two recorded dates are required.','يلزم وجود يومين مسجلين على الأقل.',lang),'sources':['daily_sales']}
 first,last=points[0],points[-1]
 difference=round(float(last['revenue'])-float(first['revenue']),2)
 high=max(points,key=lambda p:p['revenue'])
 low=min(points,key=lambda p:p['revenue'])
 return {'available':True,'chart':'daily-sales','period':{'start':first['date'],'end':last['date'],'observations':len(points)},'first':first,'last':last,'difference':difference,'peak':high,'low':low,
  'takeaway':local(f'Between the first and last displayed dates, recorded daily net sales changed by {difference:,.2f} EGP.',f'الفرق بين أول وآخر يوم معروض في صافي المبيعات المسجل هو {difference:,.2f} جنيه.',lang),
  'interpretation':local(f'Highest displayed day: {high["date"]}; lowest: {low["date"]}. This describes observed days, not a period-over-period business growth rate.',f'أعلى يوم معروض: {high["date"]} وأقل يوم: {low["date"]}. هذه مقارنة أيام مسجلة وليست نسبة نمو لفترتين متكافئتين.',lang),
  'next_action':local('Compare complete periods and inspect branch contributors in Revenue X-Ray.','قارِن فترات مكتملة وافحص مساهمة الفروع في تحليل الإيرادات.',lang),
  'limitations':[local('Dates may be missing or partial; no causal attribution or seasonality adjustment.','قد تكون بعض الأيام ناقصة أو غير مكتملة ولا توجد نسبة سببية أو تعديل للموسمية.',lang)],'sources':['daily_sales <= sales_order_items.csv'],'mode':'deterministic'}

@router.get('/briefing')
def briefing(lang:str='en'):
 if lang not in ('en','ar'):raise HTTPException(422,'Unsupported language')
 metrics=get_rows('SELECT key,value,unit,definition,source,trust FROM metrics ORDER BY key')
 cases=get_rows('SELECT id,title,severity,status FROM cases ORDER BY id')
 focus=[metric_story(m,lang) for m in metrics if m['key'] in ('net_sales','sales_orders','margin','refunds')]
 open_cases=[c for c in cases if c['status'] not in ('closed','resolved')]
 return {'available':bool(metrics),'mode':'deterministic-evidence','headline':local('Business pulse: recorded facts and open questions','ملخص الأعمال: الأرقام المسجلة والأسئلة التي تحتاج مراجعة',lang),
  'key_takeaway':local(f'{len(metrics)} source-derived metrics are available, with {len(open_cases)} investigations not marked resolved. None alone proves a loss or a root cause.',f'يتوفر {len(metrics)} مؤشر محسوب من المصادر و{len(open_cases)} تحقيق لم يُسجّل كمُغلق. لا يثبت أي مؤشر وحده خسارة أو سببًا محددًا.',lang),
  'metrics':focus,'open_investigations':open_cases[:6],'investigation_count':len(open_cases),
  'reliability_flags':[{'id':m['key'],'trust':m['trust']} for m in metrics if m['trust']!='verified'][:8],
  'next_actions':[local('Review non-verified source definitions.','مراجعة تعريفات المصادر غير المتحقق منها.',lang),local('Prioritize unresolved investigations using their evidence.','ترتيب التحقيقات المفتوحة حسب الأدلة المتاحة.',lang)],
  'limitations':[local('No comparison baseline supplied. No new financial outcomes are inferred.','لا توجد فترة مرجعية للمقارنة ولم تُستنتج نتائج مالية جديدة.',lang)]}
