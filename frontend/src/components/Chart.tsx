import React from 'react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { Lang, t, fmtMoney, fmtCompact, fmtNumber } from '../i18n'
import { Empty } from './ui'

/** Branded time-series. Strategy: the plot is ALWAYS oldest→newest, left→right (chronology is never
 *  reversed for RTL); only labels, tooltip text and number formatting follow the interface language. */
export function TrendChart({ lang, data, x, y, label }: { lang: Lang; data: any[]; x: string; y: string; label: string }) {
  if (!data?.length) return <Empty title={t(lang, 'chart_empty')} />
  return (
    <div className="chart" role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="brandFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.22} />
              <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey={x} tick={{ fill: 'var(--chart-axis)', fontSize: 11 }} minTickGap={48} tickLine={false} axisLine={{ stroke: 'var(--chart-grid)' }} />
          <YAxis tick={{ fill: 'var(--chart-axis)', fontSize: 11 }} tickLine={false} axisLine={false} width={64} tickFormatter={(n) => fmtCompact(lang, n)} />
          <Tooltip
            formatter={(v: any) => [fmtMoney(lang, Number(v), 'EGP', false), label]}
            contentStyle={{ background: 'var(--c-surface)', border: '1px solid var(--c-border)', borderRadius: 8, fontSize: 12, direction: lang === 'ar' ? 'rtl' : 'ltr' }}
          />
          <Area type="monotone" dataKey={y} name={label} stroke="var(--chart-1)" strokeWidth={2} fill="url(#brandFill)" isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
export { fmtNumber }
