import { useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { differenceInCalendarDays, format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { TrendPoint } from '@/lib/types'
import { formatMoney } from '@/lib/format'

const TOOLTIP_STYLE = {
  background: '#141c3c',
  border: '1px solid rgba(120,134,200,0.28)',
  borderRadius: 10,
}

type ChartRow = {
  date: string
  income: number
  expenses: number
}

function toChartRows(points: TrendPoint[]): ChartRow[] {
  return points.map((p) => ({
    date: p.date,
    income: Number(p.income),
    expenses: Number(p.expenses),
  }))
}

function hasAnyValue(rows: ChartRow[], key: 'income' | 'expenses'): boolean {
  return rows.some((r) => r[key] > 0)
}

function formatTick(dateStr: string, rangeDays: number): string {
  const d = parseISO(dateStr)
  if (rangeDays > 90) return format(d, 'MMM', { locale: ru })
  if (rangeDays > 31) return format(d, 'd MMM', { locale: ru })
  return format(d, 'd', { locale: ru })
}

function TrendLineChart({
  title,
  subtitle,
  dataKey,
  color,
  rows,
  rangeDays,
}: {
  title: string
  subtitle: string
  dataKey: 'income' | 'expenses'
  color: string
  rows: ChartRow[]
  rangeDays: number
}) {
  const tickFormatter = (value: string) => formatTick(value, rangeDays)

  return (
    <div className="card">
      <div className="card-header">
        <h2>{title}</h2>
        <span className="card-subtitle">{subtitle}</span>
      </div>
      {!hasAnyValue(rows, dataKey) ? (
        <div className="empty"><p>Нет данных за период</p></div>
      ) : (
        <div className="chart-area">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(120,134,200,0.12)" />
              <XAxis
                dataKey="date"
                stroke="#8a94c4"
                fontSize={11}
                tickFormatter={tickFormatter}
                interval="preserveStartEnd"
                minTickGap={24}
              />
              <YAxis stroke="#8a94c4" fontSize={11} tickFormatter={(v) => formatMoney(v)} width={72} />
              <Tooltip
                labelFormatter={(label) => format(parseISO(String(label)), 'd MMMM yyyy', { locale: ru })}
                formatter={(v) => formatMoney(Number(v))}
                contentStyle={TOOLTIP_STYLE}
                labelStyle={{ color: '#e8ecff' }}
              />
              <Line
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                strokeWidth={2}
                dot={rows.length <= 31 ? { r: 3, fill: color } : false}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

type Props = {
  points: TrendPoint[] | undefined
  dateFrom: string
  dateTo: string
  periodLabel?: string
}

export function IncomeExpenseTrendCharts({ points, dateFrom, dateTo, periodLabel }: Props) {
  const rows = useMemo(() => toChartRows(points ?? []), [points])
  const rangeDays = useMemo(
    () => Math.max(1, differenceInCalendarDays(parseISO(dateTo), parseISO(dateFrom)) + 1),
    [dateFrom, dateTo],
  )
  const subtitle = periodLabel ?? `${format(parseISO(dateFrom), 'd MMM', { locale: ru })} — ${format(parseISO(dateTo), 'd MMM yyyy', { locale: ru })}`

  return (
    <section className="grid-2">
      <TrendLineChart
        title="Доходы"
        subtitle={subtitle}
        dataKey="income"
        color="#2dd4bf"
        rows={rows}
        rangeDays={rangeDays}
      />
      <TrendLineChart
        title="Расходы"
        subtitle={subtitle}
        dataKey="expenses"
        color="#ef4761"
        rows={rows}
        rangeDays={rangeDays}
      />
    </section>
  )
}
