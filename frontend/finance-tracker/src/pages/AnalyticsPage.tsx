import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ExcludeInvestmentsToggle } from '@/components/ExcludeInvestmentsToggle'
import { useAnalyticsPreferences } from '@/context/AnalyticsPreferencesContext'
import { useHeatmap, useRatios, useStatistics, useTrends } from '@/hooks/useQueries'
import { formatMoney, toIsoDate } from '@/lib/format'
import { Heatmap } from '@/components/Heatmap'
import { IncomeExpenseTrendCharts } from '@/components/IncomeExpenseTrendCharts'

const PIE_COLORS = ['#7c5cff', '#38bdf8', '#2dd4bf', '#f5b450', '#ef4761', '#a78bfa', '#34d399']

function defaultRange(daysBack: number) {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - daysBack)
  return { from: toIsoDate(from), to: toIsoDate(to) }
}

export function AnalyticsPage() {
  const { excludeInvestments } = useAnalyticsPreferences()
  const [range, setRange] = useState<{ from: string; to: string }>(() => defaultRange(30))
  const stats = useStatistics(range.from, range.to, excludeInvestments)
  const heat = useHeatmap(range.from, range.to, excludeInvestments)
  const trends = useTrends(range.from, range.to, excludeInvestments)
  const ratios = useRatios(excludeInvestments)

  const expenses = (stats.data?.top_expense_categories ?? []).map((c) => ({
    name: c.category_name,
    value: Number(c.total),
  }))
  const incomes = (stats.data?.top_income_categories ?? []).map((c) => ({
    name: c.category_name,
    value: Number(c.total),
  }))

  return (
    <>
      <ExcludeInvestmentsToggle />

      <div className="card">
        <div className="date-range-toolbar">
          <div className="date-range-fields">
            <div className="field">
              <label>Дата от</label>
              <input className="input" type="date" value={range.from} onChange={(e) => setRange({ ...range, from: e.target.value })} />
            </div>
            <div className="field">
              <label>Дата до</label>
              <input className="input" type="date" value={range.to} onChange={(e) => setRange({ ...range, to: e.target.value })} />
            </div>
          </div>
          <div className="date-range-presets">
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRange(defaultRange(7))}>Неделя</button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRange(defaultRange(30))}>30 дней</button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRange(defaultRange(90))}>3 месяца</button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRange(defaultRange(365))}>Год</button>
          </div>
        </div>
      </div>

      <section className="kpi-grid">
        <div className="kpi">
          <span className="label">Денежный поток</span>
          <span className={`value mono ${Number(stats.data?.cashflow ?? 0) >= 0 ? 'value-positive' : 'value-negative'}`}>
            {formatMoney(stats.data?.cashflow ?? 0)}
          </span>
        </div>
        <div className="kpi">
          <span className="label">Средний расход / день</span>
          <span className="value mono">{formatMoney(stats.data?.average_daily_spending ?? 0)}</span>
        </div>
        <div className="kpi">
          <span className="label">Средний доход / месяц</span>
          <span className="value mono">{formatMoney(stats.data?.average_monthly_income ?? 0)}</span>
        </div>
        <div className="kpi">
          <span className="label">Норма сбережений</span>
          <span className="value mono">{((ratios.data?.savings_rate ?? 0) * 100).toFixed(1)}%</span>
        </div>
      </section>

      <IncomeExpenseTrendCharts
        points={trends.data?.points}
        dateFrom={range.from}
        dateTo={range.to}
      />

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h2>Расходы по категориям</h2>
          </div>
          {expenses.length === 0 ? (
            <div className="empty"><p>Нет данных</p></div>
          ) : (
            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={expenses} dataKey="value" innerRadius={70} outerRadius={110} paddingAngle={2}>
                    {expenses.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v) => formatMoney(Number(v))}
                    contentStyle={{
                      background: '#141c3c',
                      border: '1px solid rgba(120,134,200,0.28)',
                      borderRadius: 10,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          {expenses.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <table className="table">
                <tbody>
                  {expenses.map((e, i) => (
                    <tr key={e.name}>
                      <td>
                        <span className="row" style={{ gap: 8 }}>
                          <span className="color-swatch" style={{ background: PIE_COLORS[i % PIE_COLORS.length], margin: 0 }} />
                          {e.name}
                        </span>
                      </td>
                      <td className="mono" style={{ textAlign: 'right' }}>{formatMoney(e.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Доходы по категориям</h2>
          </div>
          {incomes.length === 0 ? (
            <div className="empty"><p>Нет данных</p></div>
          ) : (
            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={incomes}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(120,134,200,0.12)" />
                  <XAxis dataKey="name" stroke="#8a94c4" fontSize={11} />
                  <YAxis stroke="#8a94c4" fontSize={11} />
                  <Tooltip
                    formatter={(v) => formatMoney(Number(v))}
                    contentStyle={{
                      background: '#141c3c',
                      border: '1px solid rgba(120,134,200,0.28)',
                      borderRadius: 10,
                    }}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#2dd4bf" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Активность</h2>
        </div>
        {!heat.data || heat.data.days.length === 0 ? (
          <div className="empty"><p>Нет данных</p></div>
        ) : (
          <Heatmap days={heat.data.days} />
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Коэффициенты</h2>
        </div>
        <div className="grid-3">
          <Ratio
            label="Норма сбережений"
            value={ratios.data?.savings_rate ?? 0}
            description="Какая доля доходов уходит в сбережения"
            target=">20% хорошо"
          />
          <Ratio
            label="Расходы / доходы"
            value={ratios.data?.expense_to_income_ratio ?? 0}
            description="Доля доходов, уходящая на расходы"
            target="<80% хорошо"
            inverse
          />
          <Ratio
            label="Необязательные расходы"
            value={ratios.data?.discretionary_spending_ratio ?? 0}
            description="Доля расходов, отмеченных как необязательные"
            target="<30% оптимум"
            inverse
          />
        </div>
      </div>
    </>
  )
}

function Ratio({ label, value, description, target, inverse }: {
  label: string
  value: number
  description: string
  target: string
  inverse?: boolean
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  const variant = inverse
    ? value > 0.7 ? 'danger' : value > 0.5 ? 'warning' : 'success'
    : value < 0.1 ? 'danger' : value < 0.2 ? 'warning' : 'success'
  return (
    <div style={{ padding: 16, background: 'rgba(11,16,32,0.4)', border: '1px solid var(--border)', borderRadius: 12 }}>
      <div className="dim">{label}</div>
      <div className="mono" style={{ fontSize: 26, fontWeight: 700, margin: '4px 0' }}>
        {(value * 100).toFixed(1)}%
      </div>
      <div className="progress" style={{ marginBottom: 8 }}>
        <div className={`progress-bar ${variant}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="dim" style={{ fontSize: 12 }}>{description}</div>
      <div className={`badge badge-${variant}`} style={{ marginTop: 8 }}>{target}</div>
    </div>
  )
}
