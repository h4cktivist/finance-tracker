import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Bar,
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import {
  ArrowDownRight,
  ArrowUpRight,
  Coins,
  PiggyBank,
  Sparkles,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { ExcludeInvestmentsToggle } from '@/components/ExcludeInvestmentsToggle'
import { useAnalyticsPreferences } from '@/context/AnalyticsPreferencesContext'
import {
  useDashboard,
  useHeatmap,
  useMerchants,
  useRatios,
  useStatistics,
  useTrends,
} from '@/hooks/useQueries'
import { currentMonthStartIso, formatMoney, todayIso } from '@/lib/format'
import { Heatmap } from '@/components/Heatmap'
import { IncomeExpenseTrendCharts } from '@/components/IncomeExpenseTrendCharts'
import { MerchantTreemap } from '@/components/MerchantTreemap'
import { Link } from 'react-router-dom'
import { categoryChartColor } from '@/lib/categoryColor'

const monthFrom = currentMonthStartIso()
const monthTo = todayIso()

export function DashboardPage() {
  const { excludeInvestments } = useAnalyticsPreferences()
  const dashboard = useDashboard(excludeInvestments)
  const stats = useStatistics(monthFrom, monthTo, excludeInvestments)
  const heatmap = useHeatmap(monthFrom, monthTo, excludeInvestments)
  const merchants = useMerchants(monthFrom, monthTo, excludeInvestments)
  const ratios = useRatios(excludeInvestments)
  const trends = useTrends(monthFrom, monthTo, excludeInvestments)

  const d = dashboard.data
  const s = stats.data
  const h = heatmap.data
  const mch = merchants.data
  const r = ratios.data

  const expensePie = (s?.top_expense_categories ?? []).map((c, i) => ({
    name: c.category_name,
    value: Number(c.total),
    color: categoryChartColor(c.color, i),
  }))
  const incomeBars = (s?.top_income_categories ?? []).map((c, i) => ({
    name: c.category_name,
    value: Number(c.total),
    color: categoryChartColor(c.color, i),
  }))

  return (
    <>
      <ExcludeInvestmentsToggle />

      <section className="kpi-grid">
        <div className="kpi">
          <span className="label"><Wallet size={14} /> Общий баланс</span>
          <span className="value mono">{formatMoney(d?.total_balance ?? 0)}</span>
          <span className="hint">по всем активным счетам</span>
        </div>
        <div className="kpi">
          <span className="label"><ArrowUpRight size={14} /> Доходы</span>
          <span className="value mono value-positive">{formatMoney(d?.total_income ?? 0)}</span>
          <span className="hint">за текущий месяц</span>
        </div>
        <div className="kpi">
          <span className="label"><ArrowDownRight size={14} /> Расходы</span>
          <span className="value mono value-negative">{formatMoney(d?.total_expenses ?? 0)}</span>
          <span className="hint">за текущий месяц</span>
        </div>
        <div className="kpi">
          <span className="label"><PiggyBank size={14} /> Норма сбережений</span>
          <span className="value mono">{(d?.savings_rate ?? 0).toFixed(1)}%</span>
          <span className="hint">доход − расход</span>
        </div>
        <div className="kpi">
          <span className="label"><Sparkles size={14} /> Кэшбэк</span>
          <span className="value mono value-positive">{formatMoney(d?.cashback_earned ?? 0)}</span>
          <span className="hint">накоплено</span>
        </div>
        <div className="kpi">
          <span className="label"><TrendingUp size={14} /> Денежный поток</span>
          <span className={`value mono ${Number(s?.cashflow ?? 0) >= 0 ? 'value-positive' : 'value-negative'}`}>
            {formatMoney(s?.cashflow ?? 0)}
          </span>
          <span className="hint">за месяц</span>
        </div>
      </section>

      <IncomeExpenseTrendCharts
        points={trends.data?.points}
        dateFrom={monthFrom}
        dateTo={monthTo}
        periodLabel="текущий месяц"
      />

      <section className="grid-2">
        <div className="card">
          <div className="card-header">
            <h2>Топ расходов</h2>
            <span className="card-subtitle">по категориям</span>
          </div>
          {expensePie.length === 0 ? (
            <div className="empty"><p>Нет данных</p></div>
          ) : (
            <div className="pie-chart-block">
              <div className="chart-area chart-area--pie">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={expensePie}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                    >
                      {expensePie.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(v) => formatMoney(Number(v))}
                      contentStyle={{
                        background: '#141c3c',
                        border: '1px solid rgba(120,134,200,0.28)',
                        borderRadius: 10,
                      }}
                      labelStyle={{ color: '#e8ecff' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="pie-legend">
                {expensePie.map((entry) => (
                  <span key={entry.name} className="pill">
                    <span className="color-swatch" style={{ background: entry.color }} />
                    {entry.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Топ доходов</h2>
            <span className="card-subtitle">по категориям</span>
          </div>
          {incomeBars.length === 0 ? (
            <div className="empty"><p>Нет данных</p></div>
          ) : (
            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={incomeBars}>
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
                    labelStyle={{ color: '#e8ecff' }}
                    itemStyle={{ color: '#e8ecff' }}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {incomeBars.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <h2>Карта магазинов</h2>
            <p className="card-subtitle">Размер блока — сумма трат, цвет — категория</p>
          </div>
        </div>
        {!mch || mch.categories.length === 0 ? (
          <div className="empty"><p>Нет данных</p></div>
        ) : (
          <MerchantTreemap categories={mch.categories} />
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <h2>Активность по дням</h2>
            <p className="card-subtitle">Чем ярче — тем больше операций</p>
          </div>
        </div>
        {!h || h.days.length === 0 ? (
          <div className="empty"><p>Нет данных</p></div>
        ) : (
          <Heatmap days={h.days} dateFrom={monthFrom} dateTo={monthTo} />
        )}
      </section>

      <section className="grid-2">
        <div className="card">
          <div className="card-header">
            <h2>Финансовые коэффициенты</h2>
          </div>
          <div className="col" style={{ gap: 14 }}>
            <RatioBar
              label="Норма сбережений"
              value={r?.savings_rate ?? 0}
              hint="Доля сбережений от доходов"
              variant="success"
            />
            <RatioBar
              label="Расходы / Доходы"
              value={r?.expense_to_income_ratio ?? 0}
              hint="Чем ниже — тем лучше"
              variant="warning"
              inverse
            />
            <RatioBar
              label="Необязательные расходы"
              value={r?.discretionary_spending_ratio ?? 0}
              hint="Доля не обязательных трат"
              variant="info"
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Цели</h2>
            <Link to="/goals" className="card-subtitle">Все цели →</Link>
          </div>
          {!d || d.goals_progress.length === 0 ? (
            <div className="empty"><p>Целей пока нет</p></div>
          ) : (
            <div className="col">
              {d.goals_progress.slice(0, 5).map((g) => (
                <div key={g.id}>
                  <div className="row-between" style={{ marginBottom: 6 }}>
                    <span style={{ fontWeight: 500 }}>{g.name}</span>
                    <span className="mono dim">
                      {formatMoney(g.current_amount)} / {formatMoney(g.target_amount)}
                    </span>
                  </div>
                  <div className="progress">
                    <div
                      className="progress-bar success"
                      style={{ width: `${Math.min(100, g.progress_percent)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="grid-3">
        <div className="kpi">
          <span className="label"><Coins size={14} /> Средние расходы / день</span>
          <span className="value mono">{formatMoney(s?.average_daily_spending ?? 0)}</span>
        </div>
        <div className="kpi">
          <span className="label"><TrendingUp size={14} /> Средний доход / месяц</span>
          <span className="value mono">{formatMoney(s?.average_monthly_income ?? 0)}</span>
        </div>
        <div className="kpi">
          <span className="label">Денежный поток</span>
          <span className={`value mono ${Number(s?.cashflow ?? 0) >= 0 ? 'value-positive' : 'value-negative'}`}>
            {formatMoney(s?.cashflow ?? 0)}
          </span>
        </div>
      </section>
    </>
  )
}

function RatioBar({
  label,
  value,
  hint,
  variant,
  inverse,
}: {
  label: string
  value: number
  hint: string
  variant: 'success' | 'warning' | 'info' | 'danger'
  inverse?: boolean
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  return (
    <div>
      <div className="row-between" style={{ marginBottom: 6 }}>
        <div>
          <div style={{ fontWeight: 500 }}>{label}</div>
          <div className="dim">{hint}</div>
        </div>
        <span className={`badge badge-${inverse ? (value > 0.7 ? 'danger' : 'success') : variant}`}>
          {(value * 100).toFixed(1)}%
        </span>
      </div>
      <div className="progress">
        <div
          className={`progress-bar ${inverse && value > 0.7 ? 'danger' : variant}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
