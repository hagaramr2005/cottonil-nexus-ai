import React, { useEffect, useState } from "react";
import { authFetch } from "../authSession";

type Obj = Record<string, any>;
const route = "/api/decision-ai";
async function load(path: string, init?: RequestInit): Promise<Obj> {
  const response = await authFetch((path.startsWith("/decision-loop/") ? "/api" : route) + path, { ...init, headers: {"Content-Type":"application/json", ...init?.headers} });
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : `HTTP ${response.status}`);
  return result;
}
export function DecisionAI({lang}: {lang: "ar" | "en"}) {
  const ar = lang === "ar";
  const [runs,setRuns] = useState<Obj[]>([]);
  const [decisions,setDecisions] = useState<Obj[]>([]);
  const [forecast,setForecast] = useState<Obj|null>(null);
  const [answer,setAnswer] = useState<Obj|null>(null);
  const [intent,setIntent] = useState("open_cases");
  const [caseId,setCaseId] = useState("NEX-001");
  const [action,setAction] = useState("");
  const [owner,setOwner] = useState("");
  const [insights,setInsights] = useState<Obj[]>([]);
  const [measureDecision,setMeasureDecision] = useState("");
  const [baselineStart,setBaselineStart] = useState("");
  const [baselineEnd,setBaselineEnd] = useState("");
  const [afterStart,setAfterStart] = useState("");
  const [afterEnd,setAfterEnd] = useState("");
  const [measurement,setMeasurement] = useState<Obj|null>(null);
  const [error,setError] = useState("");
  const [notice,setNotice] = useState("");
  const refresh = () => Promise.all([load('/ml/runs'),load('/decisions'),load('/decision-loop/insights')]).then(([m,d,i])=>{setRuns(m as unknown as Obj[]);setDecisions(d as unknown as Obj[]);setInsights(i.insights as Obj[])});
  useEffect(()=>{refresh().catch(e=>setError(e.message));},[]);
  async function execute(fn:()=>Promise<any>) {setError("");setNotice("");try {await fn();} catch(e) {setError(e instanceof Error?e.message:String(e));}}
  const writeHeaders={};
  return <div className="decisionAI" dir={ar?"rtl":"ltr"} style={{display:"grid",gap:18}}>
    <section className="card"><h2>{ar?"مركز تعلّم الآلة والقرارات":"ML & Decision Intelligence"}</h2>
      <p className="muted">{ar?"نتائج فعلية من قاعدة البيانات، بدون أرقام تدريب وهمية أو ادعاء وجود LLM":"Verified database evidence, no invented training scores or hosted-LLM claims."}</p>
      <p className="muted">{ar?"تتم عمليات الكتابة بصلاحيات المشرف المؤكدة على الخادم":"Write operations require an authorized administrator session."}</p>
      {error&&<p role="alert" style={{color:"var(--danger, #c44)"}}>{error}</p>}{notice&&<p role="status">{notice}</p>}
    </section>
    <section className="card"><h3>{ar?"تقييم نموذج التوقع":"Forecast Evaluation"}</h3>
      <p className="muted">{ar?"مقارنة Seasonal Naive وLast Observation على آخر 28 يوم مبيعات":"Seasonal naive versus last-observation baseline on a 28-day holdout of observed sales."}</p>
      <button className="primary" onClick={()=>execute(async()=>{const result=await load('/ml/train',{method:'POST',headers:writeHeaders});setNotice(`Evaluation run ${result.run_id}: MAE ${result.evaluation.mae}`);await refresh();})}>{ar?"درّب وقيّم النموذج":"Train & Evaluate"}</button>{" "}
      <button onClick={()=>execute(async()=>setForecast(await load('/ml/forecast?days=7')))}>{ar?"توقع 7 أيام":"Forecast 7 Days"}</button>
      <p>{ar?"مرات التقييم":"Evaluation runs"}: {runs.length}</p>
      {runs.slice(0,5).map(r=><p key={r.id}><b>#{r.id} {r.selected}</b> — MAE {r.mae} EGP · WAPE {r.wape??"N/A"}% · {r.test_start} → {r.test_end}</p>)}
      {forecast&&<div><p><b>{ar?"توقعات افتراضية مبنية على النموذج":"Model-derived projections"}</b> · {forecast.status}</p><p className="muted">{forecast.uncertainty_intervals} · trust: {forecast.trust}</p><div style={{overflowX:"auto"}}><table><tbody>{forecast.predictions.map((p:Obj)=><tr key={p.date}><td>{p.date}</td><td>{Number(p.predicted_sales_EGP).toLocaleString(ar?"ar-EG":"en-US")} EGP</td></tr>)}</tbody></table></div></div>}
    </section>
    <section className="card"><h3>{ar?"المساعد التحليلي القائم على الأدلة":"Evidence-grounded Copilot"}</h3>
      <p className="muted">{ar?"مساعد بأدوات قراءة محددة وليس نموذج محادثة LLM":"Read-only allowlisted tools; this is not a generative LLM."}</p>
      <select value={intent} onChange={e=>setIntent(e.target.value)}><option value="open_cases">Open cases</option><option value="metrics">Metrics</option><option value="decisions">Decisions</option><option value="model_status">Model status</option></select>{" "}
      <button onClick={()=>execute(async()=>setAnswer(await load('/copilot/query',{method:'POST',body:JSON.stringify({intent,language:lang})})))}>{ar?"افحص الأدلة":"Inspect Evidence"}</button>
      {answer&&<div><p>{answer.answer}</p><p>{answer.evidence_count} records · {answer.tool}</p><details><summary>{ar?"بيانات الأدلة":"Evidence records"}</summary><pre style={{whiteSpace:"pre-wrap",wordBreak:"break-word",maxHeight:360,overflow:"auto"}}>{JSON.stringify(answer.evidence,null,2)}</pre></details></div>}
    </section>
    <section className="card"><h3>{ar?"اكتشاف الانحرافات والتوصيات":"Detect → Diagnose → Recommend"}</h3>
      <p className="muted">{ar?"كشف إحصائي مبني على الأيام السابقة فقط. النتيجة لا تثبت سبب التغيّر ولا تمثل خسارة مؤكدة":"Historical same-weekday statistical deviations. Findings do not establish a cause or financial loss."}</p>
      <button onClick={()=>execute(async()=>{const res=await load('/decision-loop/scan',{method:'POST',headers:writeHeaders});setNotice(`${res.anomalies_detected} findings; ${res.new_insights_saved} new`);await refresh();})}>{ar?"تشغيل الفحص":"Run evidence scan"}</button>
      {insights.slice(0,10).map(i=><div key={i.id} style={{padding:"10px 0",borderBottom:"1px solid var(--line, #8885)"}}>
        <b>{i.observed_date}</b> · {i.evidence.direction} · score {i.score.toFixed(2)}
        <p>{ar?"مبيعات مرصودة":"Observed"}: {Number(i.observed_value).toLocaleString()} EGP · {ar?"الوسيط المتوقع":"Expected median"}: {Number(i.expected_value).toLocaleString()} EGP</p>
        <p className="muted">{i.recommendation.action} · {i.recommendation.estimated_impact}</p>
        <button onClick={()=>execute(async()=>{await load('/decision-loop/decisions/from-insight',{method:'POST',headers:writeHeaders,body:JSON.stringify({insight_id:i.id,case_id:caseId,owner:owner||'Analyst',actor:owner||'Analyst'})});setNotice('Evidence-backed decision proposed');await refresh();})}>{ar?"اقترح قرار للمراجعة":"Propose review decision"}</button>
      </div>)}
    </section>
    <section className="card"><h3>{ar?"قياس النتائج بعد التنفيذ":"Measure outcome after implementation"}</h3>
      <p className="muted">{ar?"مقارنة وصفية لمتوسط المبيعات قبل وبعد فقط ولا تثبت السببية":"Descriptive before/after daily sales comparison; no causal attribution."}</p>
      <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
        <input aria-label="Implemented decision ID" placeholder="Decision ID" value={measureDecision} onChange={e=>setMeasureDecision(e.target.value)}/>
        {([[baselineStart,setBaselineStart,'Baseline start'],[baselineEnd,setBaselineEnd,'Baseline end'],[afterStart,setAfterStart,'After start'],[afterEnd,setAfterEnd,'After end']] as const).map(([value,update,label])=><label key={label}>{label}<input type="date" value={value} onChange={e=>update(e.target.value)}/></label>)}
      </div>
      <button onClick={()=>execute(async()=>{const res=await load(`/decision-loop/decisions/${Number(measureDecision)}/measure`,{method:'POST',headers:writeHeaders,body:JSON.stringify({baseline_start:baselineStart,baseline_end:baselineEnd,after_start:afterStart,after_end:afterEnd})});setMeasurement(res);setNotice('Descriptive measurement saved');})}>{ar?"احسب وسجّل الفرق":"Calculate & record difference"}</button>
      {measurement&&<p>{measurement.change_EGP_per_day} EGP/day ({measurement.change_percent??'N/A'}%) · {measurement.causality} · {measurement.trust}</p>}
    </section>
    <section className="card"><h3>{ar?"سير عمل القرارات":"Governed Decision Workflow"}</h3>
      <div style={{display:"flex",flexWrap:"wrap",gap:8}}><input aria-label="Case ID" value={caseId} onChange={e=>setCaseId(e.target.value)} placeholder="Case ID"/><input aria-label="Action" value={action} onChange={e=>setAction(e.target.value)} placeholder="Proposed action"/><input aria-label="Owner" value={owner} onChange={e=>setOwner(e.target.value)} placeholder="Owner"/></div>
      <p className="muted">{ar?"يُنشأ القرار كاقتراح يحتاج مراجعة؛ ربطنا الدليل بالمقياس net_sales في هذا النموذج":"New decisions are proposed for review, with a verified net_sales metric reference."}</p>
      <button onClick={()=>execute(async()=>{await load('/decisions',{method:'POST',headers:writeHeaders,body:JSON.stringify({case_id:caseId,title:'Investigate '+caseId,action,owner,actor:owner,evidence_keys:['net_sales']})});await refresh();setNotice('Decision proposed successfully');})}>{ar?"إنشاء قرار مقترح":"Propose Decision"}</button>
      {decisions.map(d=><div key={d.id} style={{padding:"10px 0",borderBottom:"1px solid var(--line, #8885)"}}><b>#{d.id} {d.title}</b> · {d.status} · {d.owner}<p>{d.action}</p>
        {({proposed:'reviewed',reviewed:'approved',approved:'in_progress',in_progress:'implemented',implemented:'measured',measured:'closed'} as Record<string,string>)[d.status]&&<button onClick={()=>execute(async()=>{const next=({proposed:'reviewed',reviewed:'approved',approved:'in_progress',in_progress:'implemented',implemented:'measured',measured:'closed'} as Record<string,string>)[d.status];await load(`/decisions/${d.id}`,{method:'PATCH',headers:writeHeaders,body:JSON.stringify({status:next,actor:owner||d.owner,reason:'Reviewed by authorized operator',...(next==='measured'?{measured_outcome:prompt('Document measured outcome and baseline')||''}:{})})});await refresh();})}>{ar?"انقل للمرحلة":"Advance to"} {({proposed:'reviewed',reviewed:'approved',approved:'in_progress',in_progress:'implemented',implemented:'measured',measured:'closed'} as Record<string,string>)[d.status]}</button>}
      </div>)}
    </section>
  </div>;
}
