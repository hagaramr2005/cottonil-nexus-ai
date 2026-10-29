import React from 'react'
import { ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { Lang, fmtMoney, fmtCompact } from '../i18n'

type Point = { label: string; revenue: number | null; discount?: number | null; units?: number | null }
type Props = { lang: Lang; monthly?: Point[]; branches?: Point[]; products?: Point[] }
const isFiniteValue = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const clean = (items?: Point[]) => (items || []).filter(p => typeof p.label === 'string' && isFiniteValue(p.revenue))
const words = (lang: Lang) => lang === 'ar'
  ? { revenue: 'صافي المبيعات', discount: 'الخصومات', branch: 'أداء الفروع', product: 'المنتجات الأعلى مبيعًا', empty: 'لا توجد بيانات مؤكدة للعرض', source: 'المصدر: تجميع سجلات المبيعات من النظام' }
  : { revenue: 'Net revenue', discount: 'Discounts', branch: 'Branch performance', product: 'Top products', empty: 'No verified chart data available', source: 'Source: aggregated sales records from the backend' }
const tooltip = (lang: Lang) => ({
  contentStyle: { background: 'var(--c-surface)', color: 'var(--c-text)', border: '1px solid var(--c-border)', borderRadius: 10 },
  formatter: (value: number, name: string) => [fmtMoney(lang, Number(value), 'EGP', false), name] as [string, string],
})
function NoData({ lang }: { lang: Lang }) { return <p className="sales-chart-empty" role="status">{words(lang).empty}</p> }
export function SalesVisuals({ lang, monthly, branches, products }: Props) {
  const text = words(lang)
  const months = clean(monthly)
  const rankedBranches = [...clean(branches)].sort((a, b) => b.revenue! - a.revenue!).slice(0, 10)
  const rankedProducts = [...clean(products)].sort((a, b) => b.revenue! - a.revenue!).slice(0, 10)
  return <>
    <div className="twocol">
      <section className="card sales-visual-card">
        <h3>{lang === 'ar' ? 'المبيعات والخصومات شهريًا' : 'Monthly revenue and discounts'}</h3>
        {months.length ? <div className="chart" role="img" aria-label={text.revenue}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={months} margin={{ top: 12, right: 12, left: 0, bottom: 2 }}>
              <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
              <XAxis dataKey="label" tick={{ fill: 'var(--chart-axis)', fontSize: 11 }} minTickGap={25} />
              <YAxis tick={{ fill: 'var(--chart-axis)', fontSize: 11 }} tickFormatter={v => fmtCompact(lang, v)} width={65} />
              <Tooltip {...tooltip(lang)} />
              <Legend />
              <Area isAnimationActive={false} type="monotone" name={text.revenue} dataKey="revenue" stroke="var(--chart-1)" fill="var(--chart-1)" fillOpacity={0.12} strokeWidth={2} />
              <Area isAnimationActive={false} type="monotone" name={text.discount} dataKey="discount" stroke="var(--chart-4)" fill="var(--chart-4)" fillOpacity={0.06} strokeWidth={2} connectNulls={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div> : <NoData lang={lang} />}
        <small className="sales-chart-source">{text.source}</small>
      </section>
      <RankedChart lang={lang} title={text.branch} points={rankedBranches} />
    </div>
    <div className="twocol">
      <RankedChart lang={lang} title={text.product} points={rankedProducts} />
    </div>
  </>
}
function RankedChart({lang, title, points}: {lang: Lang; title: string; points: Point[]}) {
  return <section className="card sales-visual-card"><h3>{title}</h3>
    {points.length ? <div className="chart" role="img" aria-label={title}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={points} layout="vertical" margin={{ top: 6, right: 16, bottom: 4, left: 6 }}>
          <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
          <XAxis type="number" tickFormatter={v => fmtCompact(lang, v)} tick={{ fill: 'var(--chart-axis)', fontSize: 10 }} />
          <YAxis type="category" dataKey="label" width={95} tick={{ fill: 'var(--chart-axis)', fontSize: 10 }} />
          <Tooltip {...tooltip(lang)} />
          <Bar dataKey="revenue" name={words(lang).revenue} fill="var(--chart-2)" radius={[0,4,4,0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div> : <NoData lang={lang} />}
  </section>
}
