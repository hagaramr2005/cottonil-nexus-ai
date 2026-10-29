import React from 'react'
import { Lang, t, trustKey, statusKey, sevKey, Key, moneyParts, fmtNumber } from '../i18n'
import { unitLabel } from '../backendText'

export type R = Record<string, any>
export const Pill = ({ lang, kind, value }: { lang: Lang; kind: 'trust' | 'status' | 'sev'; value?: string }) => {
  const k: Key | null = kind === 'trust' ? trustKey(value) : kind === 'status' ? statusKey(value) : sevKey(value)
  return <span className={'pill ' + (value || 'unverified')}>{k ? t(lang, k) : value ?? '—'}</span>
}
/** Numbers/identifiers are isolated so RTL never reorders digits, SKU codes or currency. */
export const Num = ({ children, code }: { children: React.ReactNode; code?: boolean }) => <bdi className={'num' + (code ? ' code' : '')}>{children}</bdi>
/** A figure + unit that reads correctly in both directions and never alters the value. */
export const Amount = ({ lang, value, unit, compact = true }: { lang: Lang; value: number | null | undefined; unit?: string; compact?: boolean }) => {
  if (value == null) return <>{t(lang, 'unavailable')}</>
  if (unit === 'EGP') { const m = moneyParts(lang, value, 'EGP', compact); return <><bdi className="num">{m.num}</bdi>{m.word ? <> {m.word}</> : null}</> }
  const u = unitLabel(lang, unit)
  return <><bdi className="num">{fmtNumber(lang, value)}</bdi>{u ? <> {u}</> : null}</>
}
export const Skeleton = ({ h = 20, w = '100%' }: { h?: number; w?: string }) => <div className="skeleton" style={{ height: h, width: w }} aria-hidden />
export const Empty = ({ title, hint }: { title: string; hint?: string }) => (
  <div className="emptystate" role="status"><strong>{title}</strong>{hint && <span className="muted">{hint}</span>}</div>
)
export const LangSwitch = ({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) => (
  <div className="langswitch" role="group" aria-label="Language / اللغة">
    <button aria-pressed={lang === 'ar'} onClick={() => setLang('ar')} lang="ar">العربية</button>
    <button aria-pressed={lang === 'en'} onClick={() => setLang('en')} lang="en">English</button>
  </div>
)
