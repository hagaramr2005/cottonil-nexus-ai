import React, { useEffect, useRef, useState } from 'react'
import { Copy, ChevronDown, ChevronUp, Send, Check, Trash2, Wifi, WifiOff } from 'lucide-react'
import { Lang, t, Key, D } from '../i18n'
import { Pill, R, Num, Amount, Skeleton } from './ui'
import { tx, txl } from '../backendText'

type AgentStep = { agent: string; status: 'completed' | 'blocked' | 'skipped' | 'fallback'; detail: string }
type ChatResult = R & { language?: 'ar' | 'en'; mode?: string; llm_used?: boolean; llm_available?: boolean; llm_reason?: string; agent_trace?: AgentStep[] }
type Turn = { id: number; q: string; res?: ChatResult; err?: string; ctx?: boolean }
type ModelStatus = { configured: boolean; available: boolean | null; mode: string; model: string | null; reason: string | null }
type Sugg = { key: Key; mode: 'analyst' | 'context' | 'link'; page?: string; hint?: Key }
const GENERAL: Sugg[] = [
  { key: 'ai_s_sales', mode: 'analyst' }, { key: 'ai_s_orders', mode: 'analyst' },
  { key: 'ai_s_proc', mode: 'analyst' }, { key: 'ai_s_cases', mode: 'analyst' },
  { key: 'ai_q1', mode: 'link', page: 'change', hint: 'ai_opens_xray' },
  { key: 'ai_q5', mode: 'link', page: 'passport', hint: 'ai_opens_rel' },
]
const CASE: Sugg[] = [
  { key: 'ai_q2', mode: 'context' }, { key: 'ai_q3', mode: 'context' },
  { key: 'ai_q4', mode: 'context' }, { key: 'ai_q5', mode: 'link', page: 'passport', hint: 'ai_opens_rel' },
]

function modelLabel(lang: Lang, status: ModelStatus | null): string {
  if (!status) return lang === 'ar' ? 'جارٍ فحص النموذج' : 'Checking model'
  if (status.available === true) return `${status.model || 'LLM'} · ${lang === 'ar' ? 'متاح في Ollama' : 'detected in Ollama'}`
  if (status.available === null) return lang === 'ar' ? 'الاتصال غير مؤكد' : 'Provider not verified'
  return lang === 'ar' ? 'وضع تحليلي بديل · النموذج غير متاح' : 'Fallback mode · LLM unavailable'
}

export function Copilot({ lang, api, contextLabel, contextPage, contextCase, go }: {
  lang: Lang; api: (path: string, init?: RequestInit) => Promise<any>
  contextLabel: string; contextPage: string; contextCase: string | null
  go: (page: string, caseId?: string) => void
}) {
  const [q, setQ] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)
  const [model, setModel] = useState<ModelStatus | null>(null)
  const id = useRef(0)
  const ending = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let mounted = true
    api('/copilot/status').then((s) => { if (mounted) setModel(s) })
      .catch(() => { if (mounted) setModel({ configured: false, available: false, mode: 'unavailable', model: null, reason: 'Status endpoint unreachable' }) })
    return () => { mounted = false }
  }, [api])
  useEffect(() => { ending.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) }, [turns])

  const run = async (question: string, ctx = false) => {
    const clean = question.trim()
    if (!clean || busy) return
    const tid = ++id.current
    // History is for follow-up references only. Backend never trusts it as business evidence.
    const history = turns.flatMap((turn) => [
      { role: 'user', content: turn.q.slice(0, 1500) },
      ...(turn.res ? [{ role: 'assistant', content: String(turn.res.answer || '').slice(0, 1500) }] : []),
    ]).slice(-12)
    setTurns((current) => [...current, { id: tid, q: clean, ctx }])
    setBusy(true)
    setQ('')
    try {
      const res: ChatResult = await api('/copilot/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: clean, language: 'auto',
          page: ctx ? contextPage : 'ai', case_id: ctx ? contextCase : null, history }),
      })
      setTurns((current) => current.map((turn) => turn.id === tid ? { ...turn, res } : turn))
    } catch (err) {
      setTurns((current) => current.map((turn) => turn.id === tid ? { ...turn,
        err: `${t(lang, 'err_generic')}${err instanceof Error ? ` (${err.message.slice(0, 120)})` : ''}` } : turn))
    } finally { setBusy(false) }
  }

  return (
    <div className="aiLayout">
      <section className="card chat" aria-label={t(lang, 'ai_title')}>
        <div className="copilotHeader">
          <div><h3>{t(lang, 'ai_title')}</h3><p className="muted">{t(lang, 'ai_sub')}</p></div>
          <div className="copilotActions">
            <span className="copilotStatus" title={model?.reason || undefined}>
              {model?.available ? <Wifi size={14} /> : <WifiOff size={14} />}{modelLabel(lang, model)}
            </span>
            <button className="chip" onClick={() => { setTurns([]); setQ(''); id.current = 0 }} disabled={busy || turns.length === 0}
              aria-label={lang === 'ar' ? 'مسح المحادثة' : 'Clear conversation'}>
              <Trash2 size={14} aria-hidden="true" /> {lang === 'ar' ? 'مسح المحادثة' : 'Clear chat'}
            </button>
          </div>
        </div>
        {!turns.length && <p className="muted">{t(lang, 'ai_scope')}</p>}
        <div className="copilotMessages" role="log" aria-live="polite" aria-relevant="additions text">
          {turns.map((u) => (
            <React.Fragment key={u.id}>
              <div className="bubble user" dir="auto" style={{ unicodeBidi: 'plaintext' }}>{u.q}</div>
              {!u.res && !u.err && <div className="bubble bot"><span className="muted">{t(lang, 'ai_thinking')}</span><Skeleton h={12} /></div>}
              {u.err && <div className="bubble bot error" role="alert">{u.err}</div>}
              {u.res && <Answer lang={lang} res={u.res} go={go} />}
            </React.Fragment>
          ))}
          <div ref={ending} />
        </div>
        <div className="composer">
          <textarea dir="auto" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder={t(lang, 'ai_placeholder')} aria-label={t(lang, 'ai_title')}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && q.trim() && !busy) { e.preventDefault(); void run(q) } }} />
          <button className="primary" disabled={busy || !q.trim()} onClick={() => void run(q)} aria-label={t(lang, 'ai_send')}>
            <Send size={16} aria-hidden="true" style={{ transform: lang === 'ar' ? 'scaleX(-1)' : 'none' }} /> {t(lang, 'ai_send')}
          </button>
        </div>
      </section>
      <aside>
        <div className="card">
          <h4 style={{ marginBlockStart: 0 }}>{t(lang, contextCase ? 'ai_case_h' : 'ai_general_h')}</h4>
          <div className="copilotSuggestions">
            {(contextCase ? CASE : GENERAL).map((sg) => (
              <button className="chip" key={sg.key} disabled={busy}
                onClick={() => sg.mode === 'link' ? go(sg.page!) : void run(D[sg.key][lang], sg.mode === 'context')}>
                {D[sg.key][lang]}
                {sg.hint && <small className="copilotHint">{D[sg.hint][lang]}</small>}
              </button>
            ))}
          </div>
        </div>
        <div className="card">
          <h4 style={{ marginBlockStart: 0 }}>{t(lang, 'ai_context')}</h4>
          <p className="muted">{contextLabel}{contextCase ? <> · <Num>{contextCase}</Num></> : null}</p>
          <button className="ghost" disabled={busy} onClick={() => void run(D.ai_context_btn[lang], true)}>{t(lang, 'ai_context_btn')}</button>
        </div>
      </aside>
    </div>
  )
}

function Answer({ lang, res, go }: { lang: Lang; res: ChatResult; go: (page: string, caseId?: string) => void }) {
  const [open, setOpen] = useState(false), [done, setDone] = useState(false)
  const text: string = res.llm_answer || res.answer || ''
  const metrics: R[] = res.metrics || [], cases: R[] = res.cases || [], facts: R[] = res.facts || []
  const sources: string[] = res.sources || []
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500) } catch { /* clipboard unavailable */ }
  }
  if (!text) return <div className="bubble bot"><p>{t(lang, 'ai_no_answer')}</p></div>
  const hasDetail = Boolean(metrics.length || facts.length || cases.length || res.limitations?.length)
  const mode = res.mode === 'grounded-llm' ? (lang === 'ar' ? 'شرح بمساعدة النموذج مع أدلة' : 'LLM-assisted with evidence') :
    res.mode === 'conversational' ? (lang === 'ar' ? 'محادثة' : 'Conversation') :
    (lang === 'ar' ? 'إجابة من أدوات تحليل محددة' : 'Deterministic analytical answer')
  return (
    <div className="bubble bot">
      <div className="copilotAnswer" dir="auto" style={{ whiteSpace: 'pre-wrap', unicodeBidi: 'plaintext' }}>{text}</div>
      <small className="muted copilotMode">{mode}</small>
      {res.agent_trace?.length ? <details className="agentTrace">
        <summary>{lang === 'ar' ? 'عرض مسار عمل الـ AI Agents' : 'View AI agent workflow'}
          <span className="agentTraceCount">{res.agent_trace.filter(x => x.status === 'completed').length}/{res.agent_trace.length}</span>
        </summary>
        <ol>
          {res.agent_trace.map((step, idx) => <li key={`${step.agent}-${idx}`}>
            <span className={`agentTraceDot agentTraceDot-${step.status}`} aria-hidden="true" />
            <span className="agentTraceName">{agentName(lang, step.agent)}</span>
            <small className="muted">{agentStepStatus(lang, step.status)}</small>
          </li>)}
        </ol>
        <small className="muted">{lang === 'ar' ? 'مسار تنفيذي فعلي بأدوات قراءة محددة، مش 5 موديلات LLM مستقلة.' : 'Actual bounded execution steps, not five independent LLM models.'}</small>
      </details> : null}
      {res.llm_reason && <small className="muted copilotMode" dir="auto">{lang === 'ar' ? 'تعذّر توليد إجابة من النموذج؛ تم استخدام الأدلة المسجلة.' : res.llm_reason}</small>}
      {(sources.length > 0 || metrics.length > 0) && (
        <div className="chips" aria-label={t(lang, 'evidence')}>
          {metrics.map((m) => <span className="chip src" key={m.key}>{(D as any)['m_' + m.key]?.[lang] || m.key}</span>)}
          {sources.map((s) => <span className="chip src" key={s}>{srcLabel(lang, s)}</span>)}
        </div>
      )}
      {open && <div style={{ marginBlockStart: 12 }}>
        {metrics.map((m) => <div className="evidence" key={m.key}>
          <span><b>{(D as any)['m_' + m.key]?.[lang] || m.key}</b><small className="muted" style={{ display: 'block' }}>{tx(lang, m.definition)}</small></span>
          <span><b><Amount lang={lang} value={m.value} unit={m.unit} /></b> <Pill lang={lang} kind="trust" value={m.trust} /></span>
        </div>)}
        {cases.map((c) => <button key={c.id} className="caseRow" onClick={() => go('cases', c.id)}>
          <div><b>{tx(lang, c.title)}</b><small><Num code>{c.id}</Num></small></div>
        </button>)}
        {facts.map((f,i) => <Fact key={i} lang={lang} f={f} go={go} />)}
        {res.limitations?.length > 0 && <p className="muted">{t(lang, 'limits')}: {txl(lang, res.limitations)}</p>}
      </div>}
      {res.next_actions?.length > 0 && <><h4>{t(lang, 'ai_next')}</h4>{res.next_actions.map((a: string) => <p key={a}>{a}</p>)}</>}
      <div className="chips" style={{ marginBlockStart: 8 }}>
        <button className="chip" onClick={copy}>{done ? <Check size={12} /> : <Copy size={12} />} {t(lang, done ? 'copied' : 'copy')}</button>
        {hasDetail && <button className="chip" onClick={() => setOpen(!open)} aria-expanded={open}>
          {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />} {t(lang, open ? 'collapse' : 'expand')}
        </button>}
      </div>
    </div>
  )
}

function Fact({ lang, f, go }: { lang: Lang; f: R; go: (page: string, caseId?: string) => void }) {
  if (f.type === 'metric' && f.values) {
    const m = f.values
    return <div className="evidence">
      <span><b>{(D as any)['m_' + m.key]?.[lang] || m.key}</b><small className="muted" style={{ display: 'block' }}>{tx(lang, m.definition)}</small></span>
      <span><b><Amount lang={lang} value={m.value} unit={m.unit} /></b> <Pill lang={lang} kind="trust" value={m.trust} /></span>
    </div>
  }
  if (f.type === 'investigation' || f.type === 'investigation_summary') return <div>
    <button className="caseRow" onClick={() => go('cases', f.id)}>
      <div><b>{tx(lang, f.title)}</b><small><Num code>{f.id}</Num></small></div>
      <Pill lang={lang} kind="status" value={f.status} />
    </button>
    {f.observations?.map((o: string) => <p key={o}>{tx(lang, o)}</p>)}
    {f.hypotheses_not_facts?.length > 0 && <p className="muted">{f.hypotheses_not_facts.map((h: string) => tx(lang, h)).join(' · ')}</p>}
  </div>
  // Unknown factual types are not rendered as a raw JSON dump in the client.
  return <p className="muted">{lang === 'ar' ? 'تفاصيل إضافية متاحة في مصادر التحليل.' : 'Additional details are available in the source evidence.'}</p>
}

const srcLabel = (lang: Lang, s: string) => ((D as any)['m_' + s]?.[lang] as string) || (s === 'cases' ? t(lang, 'p_investigations') : s)

const AGENT_NAMES: Record<string, [string, string]> = {
  supervisor: ['المشرف / التوجيه', 'Supervisor / Routing'],
  sales_analyst: ['محلل المبيعات', 'Sales Analyst'],
  risk_investigator: ['محلل التحقيقات', 'Risk Investigator'],
  grounding_reviewer: ['مراجع الأدلة والأمان', 'Evidence & Safety Reviewer'],
  narrative: ['مساعد صياغة الإجابة', 'Narrative Agent'],
}
function agentName(lang: Lang, agent: string) {
  return (AGENT_NAMES[agent] || [agent, agent])[lang === 'ar' ? 0 : 1]
}
function agentStepStatus(lang: Lang, status: AgentStep['status']) {
  const labels = {
    completed: ['اكتمل', 'Completed'],
    blocked: ['مرفوض بأمان', 'Safely blocked'],
    skipped: ['غير مطلوب', 'Not required'],
    fallback: ['وضع بديل', 'Fallback'],
  }
  return labels[status][lang === 'ar' ? 0 : 1]
}
