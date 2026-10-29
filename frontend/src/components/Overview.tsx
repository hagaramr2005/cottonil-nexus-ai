import React from 'react'
import { ChevronRight } from 'lucide-react'
import { Lang, t, fmtMoney, fmtNumber, fmtDate, Key, D } from '../i18n'
import { Pill, R, Num, Amount, Empty, Skeleton } from './ui'
import { tx, unitLabel } from '../backendText'
import { TrendChart } from './Chart'

const KPI: { key: string; lead?: boolean; money?: boolean }[] = [
  { key: 'net_sales', lead: true, money: true },
  { key: 'sales_orders' },
  { key: 'sold_units' },
  { key: 'purchase_sales_ratio' },
]

export function Overview(p: {
  lang: Lang; overview: R | null; recs: R | null; chartStory: R | null; openCases: number
  onExplain: (id: string) => void; onExplainChart: () => void; onCloseChart: () => void; go: (page: string, caseId?: string) => void
}) {
  const { lang, overview, recs } = p
  const L = (k: string) => t(lang, k as Key)
  const has = (k: string) => (`m_${k}` as string) in (D as any)
  const metric = (k: string) => overview?.metrics?.find((x: R) => x.key === k)
  const daily: R[] = overview?.daily || []
  const through = daily.length ? daily[daily.length - 1].date : null
  const label = (k: string) => (has(k) ? L('m_' + k) : k.replace(/_/g, ' '))
  const desc = (k: string, m?: R) => (has(k + '_d') ? L('m_' + k + '_d') : tx(lang, m?.definition) || '')
  const recTitle = (ti: string) => {
    const m = String(ti).match(/^(?:Verify metric: |راجع تعريف المؤشر: )(.+)$/)
    return m ? L('ac_verify') + ': ' + label(m[1]) : tx(lang, String(ti).replace(/^(Review: |مراجعة: )/, ''))
  }
  const insights: R[] = recs?.recommendations?.slice(0, 3) || []
  return (
    <>
      <section className="hero">
        <div>
          <h2>{t(lang, 'ov_title')}</h2>
          <p className="muted" style={{ maxInlineSize: '60ch' }}>{t(lang, 'ov_sub')}</p>
        </div>
        <div className="meta">
          <span>{t(lang, 'period')}<b>{t(lang, 'period_all')}</b></span>
          <span>{t(lang, 'ov_data_through')}<b><bdi>{through ? fmtDate(lang, through) : '—'}</bdi></b></span>
          <span>{t(lang, 'ov_open_cases')}<b><Num>{fmtNumber(lang, p.openCases)}</Num></b></span>
        </div>
      </section>
      <div className="kpis exec">
        {!overview && [0, 1, 2, 3].map((i) => <div className="kpi" key={i}><Skeleton h={14} w="50%" /><Skeleton h={34} w="70%" /><Skeleton h={12} /></div>)}
        {overview && KPI.map(({ key, lead, money }) => {
          const m = metric(key)
          return (
            <div className={'kpi' + (lead ? ' lead' : '')} key={key}>
              <small>{label(key)}</small>
              <strong>{m ? <Amount lang={lang} value={m.value} unit={m.unit} /> : t(lang, 'unavailable')}</strong>
              <span className="desc">{desc(key, m)}</span>
              <div className="kpifoot">
                {m ? <Pill lang={lang} kind="trust" value={m.trust} /> : <Pill lang={lang} kind="trust" value="unavailable" />}
                <button className="explainBtn" onClick={() => p.onExplain(key)}>{t(lang, 'explain_number')}</button>
              </div>
            </div>
          )
        })}
      </div>
      <section className="card">
        <div className="sectionhead"><h3>{t(lang, 'ov_sales_chart')}</h3><button className="explainBtn" onClick={p.onExplainChart}>{t(lang, 'explain_chart')}</button></div>
        <TrendChart lang={lang} data={daily} x="date" y="revenue" label={t(lang, 'revenue')} />
        <p className="muted" style={{ marginBlockStart: 8 }}>{t(lang, 'ov_chart_note')}</p>
      </section>
      {p.chartStory && (
        <section className="card storyExplanation">
          <div className="sectionhead"><h3>{t(lang, 'chart_interp')}</h3><button className="link" onClick={p.onCloseChart} aria-label={t(lang, 'close')}>{t(lang, 'close')}</button></div>
          {p.chartStory.available ? (<><h4 style={{ marginBlockStart: 0 }}>{p.chartStory.takeaway}</h4><p>{p.chartStory.interpretation}</p><p>{p.chartStory.next_action}</p><p className="muted">{[...(p.chartStory.limitations || []), ...(p.chartStory.sources || [])].join(' · ')}</p></>) : <p>{p.chartStory.reason}</p>}
        </section>
      )}
      <h3>{t(lang, 'ov_insights')}</h3>
      {insights.length ? (
        <div className="insights">
          {insights.map((r) => (
            <article className="insight" key={r.id}>
              <dl>
                <div><dt>{t(lang, 'ov_what')}</dt><dd><b>{recTitle(r.title)}</b></dd></div>
                <div><dt>{t(lang, 'ov_why')}</dt><dd>{r.context}</dd></div>
                <div><dt>{t(lang, 'ov_proof')}</dt><dd>{(r.evidence || []).map((k: string) => label(k)).join(' · ') || '—'}</dd></div>
                <div><dt>{t(lang, 'ov_next')}</dt><dd className="step">{r.action}</dd></div>
              </dl>
              <div style={{ marginBlockStart: 12 }}>
                <button className="explainBtn" onClick={() => (r.case_id ? p.go('cases', r.case_id) : p.go('passport'))}>
                  {t(lang, r.case_id ? 'open_investigation' : 'review_reliability')} <ChevronRight size={12} className="chev" style={{ verticalAlign: 'middle' }} />
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : <div className="card"><Empty title={t(lang, 'ov_no_insights')} /></div>}
    </>
  )
}
