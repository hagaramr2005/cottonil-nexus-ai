import React, { useEffect, useRef, useState } from 'react'
import { X, ChevronLeft, ChevronRight, Maximize } from 'lucide-react'
import { Lang, t, fmtMoney, fmtNumber, Key, LOGO_SRC } from '../i18n'
import { R, Num, Amount, Pill } from './ui'
import { TrendChart } from './Chart'
import { tx } from '../backendText'

const SLIDES: Key[] = ['story_s1', 'story_s2', 'story_s3', 'story_s4', 'story_s5']

export function ExecutiveStory({ lang, briefing, daily, onClose }: { lang: Lang; briefing: R | null; daily: R[]; onClose: () => void }) {
  const [i, setI] = useState(0)
  const frame = useRef<HTMLDivElement>(null)
  const rtl = lang === 'ar'
  const last = SLIDES.length - 1
  const next = () => setI((x) => Math.min(last, x + 1)), prev = () => setI((x) => Math.max(0, x - 1))
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      // arrow keys follow reading direction
      if (e.key === 'ArrowRight') (rtl ? prev : next)()
      if (e.key === 'ArrowLeft') (rtl ? next : prev)()
    }
    window.addEventListener('keydown', h); frame.current?.focus()
    return () => window.removeEventListener('keydown', h)
  }, [rtl])
  const m: R[] = briefing?.metrics || []
  const Back = rtl ? ChevronRight : ChevronLeft, Fwd = rtl ? ChevronLeft : ChevronRight
  return (
    <div className="presentationOverlay" role="dialog" aria-modal="true" aria-label={t(lang, 'story_start')}>
      <div className="presentationFrame" ref={frame} tabIndex={-1}>
        <div className="pbar">
          <img src={LOGO_SRC} alt="Cottonil" width={345} height={50} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="ghost" onClick={() => frame.current?.requestFullscreen?.().catch(() => {})} aria-label={t(lang, 'fullscreen')}><Maximize size={16} /></button>
            <button className="ghost" onClick={onClose}><X size={16} style={{ verticalAlign: 'middle' }} /> {t(lang, 'story_close')}</button>
          </div>
        </div>
        <div className="presentationBody">
          <span className="eyebrow"><Num>{i + 1} / {SLIDES.length}</Num></span>
          <h2>{t(lang, SLIDES[i])}</h2>
          {i === 0 && (<><p>{briefing?.key_takeaway || t(lang, 'story_no_takeaway')}</p><div className="kpis">{m.slice(0, 3).map((x) => <div className="kpi" key={x.id}><small>{x.title}</small><strong><Amount lang={lang} value={x.value} unit={x.unit} /></strong></div>)}</div><TrendChart lang={lang} data={daily} x="date" y="revenue" label={t(lang, 'revenue')} /></>)}
          {i === 1 && <div className="kpis">{m.slice(0, 4).map((x) => <div className="kpi" key={x.id}><small>{x.title}</small><Pill lang={lang} kind="trust" value={x.trust} /></div>)}</div>}
          {i === 2 && (briefing?.open_investigations?.length ? briefing.open_investigations.slice(0, 4).map((c: R) => <p key={c.id}><b>{c.title}</b> <Pill lang={lang} kind="status" value={c.status} /></p>) : <p>{t(lang, 'ov_no_insights')}</p>)}
          {i === 3 && (briefing?.next_actions?.length ? briefing.next_actions.slice(0, 4).map((a: string) => <p key={a}>{a}</p>) : <p>{t(lang, 'ov_no_insights')}</p>)}
          {i === 4 && (<><p>{t(lang, 'rp_desc')}</p>{briefing?.limitations?.map((l: string) => <p className="muted" key={l}>{tx(lang, l)}</p>)}</>)}
          {(briefing?.limitations?.length ?? 0) > 0 && i === 1 && <p className="muted">{briefing?.limitations.map((l: string) => tx(lang, l)).join(' · ')}</p>}
        </div>
        <div className="presentationControls">
          <button className="ghost" onClick={prev} disabled={i === 0}><Back size={16} style={{ verticalAlign: 'middle' }} /> {t(lang, 'story_prev')}</button>
          <div className="dots" aria-hidden>{SLIDES.map((_, k) => <i key={k} className={k === i ? 'on' : ''} />)}</div>
          <button className="primary" onClick={next} disabled={i === last}>{t(lang, 'story_next')} <Fwd size={16} /></button>
        </div>
      </div>
    </div>
  )
}
