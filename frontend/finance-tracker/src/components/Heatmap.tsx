import type { HeatmapDay } from '@/lib/types'
import { formatDate, formatMoney } from '@/lib/format'

type Props = {
  days: HeatmapDay[]
  dateFrom?: string
  dateTo?: string
}

const MONTH_SHORT = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
const DOW_LABELS = ['Пн', '', 'Ср', '', 'Пт', '', 'Вс']

function getLevel(intensity: number): string {
  if (intensity <= 0) return ''
  if (intensity < 0.25) return 'l1'
  if (intensity < 0.5) return 'l2'
  if (intensity < 0.8) return 'l3'
  return 'l4'
}

function localDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function isoDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

type Cell = { iso: string; day: HeatmapDay | null; inRange: boolean }

export function Heatmap({ days, dateFrom, dateTo }: Props) {
  const dayMap = new Map<string, HeatmapDay>()
  for (const d of days) dayMap.set(d.date, d)

  const end = dateTo ? localDate(dateTo) : new Date()
  let start: Date
  if (dateFrom) {
    start = localDate(dateFrom)
  } else if (days.length > 0) {
    start = localDate(days[0].date)
  } else {
    start = new Date(end)
    start.setDate(start.getDate() - 29)
  }

  // Pad back to the nearest Monday
  const gridStart = new Date(start)
  const dow = gridStart.getDay() // 0=Sun
  gridStart.setDate(gridStart.getDate() - (dow === 0 ? 6 : dow - 1))

  const allCells: Cell[] = []
  const cur = new Date(gridStart)
  while (cur <= end) {
    const iso = isoDate(cur)
    const inRange = cur >= start && cur <= end
    allCells.push({
      iso,
      day: inRange
        ? (dayMap.get(iso) ?? { date: iso, count: 0, total_amount: '0', intensity: 0 })
        : null,
      inRange,
    })
    cur.setDate(cur.getDate() + 1)
  }
  // Pad to complete last week
  while (allCells.length % 7 !== 0) {
    const last = new Date(allCells.at(-1)!.iso)
    last.setDate(last.getDate() + 1)
    allCells.push({ iso: isoDate(last), day: null, inRange: false })
  }

  const numWeeks = allCells.length / 7

  // One label per week column: show month name when it first appears
  const monthLabels: string[] = []
  let lastMonth = -1
  for (let w = 0; w < numWeeks; w++) {
    const monday = allCells[w * 7]
    if (monday.inRange) {
      const m = localDate(monday.iso).getMonth()
      if (m !== lastMonth) {
        monthLabels.push(MONTH_SHORT[m])
        lastMonth = m
      } else {
        monthLabels.push('')
      }
    } else {
      monthLabels.push('')
    }
  }

  return (
    <div className="heatmap-wrap">
      <div className="heatmap-inner">
        <div className="heatmap-month-row">
          <div className="heatmap-dow-spacer" />
          <div className="heatmap-month-labels">
            {monthLabels.map((label, i) => (
              <div key={i} className="heatmap-month-label">{label}</div>
            ))}
          </div>
        </div>
        <div className="heatmap-body">
          <div className="heatmap-dow-col">
            {DOW_LABELS.map((label, i) => (
              <div key={i} className="heatmap-dow-label">{label}</div>
            ))}
          </div>
          <div className="heatmap-grid">
            {allCells.map((cell) => (
              <div
                key={cell.iso}
                className={[
                  'heatmap-cell',
                  !cell.inRange ? 'heatmap-cell--void' : getLevel(cell.day?.intensity ?? 0),
                ].filter(Boolean).join(' ')}
                title={
                  cell.inRange && cell.day && cell.day.count > 0
                    ? `${formatDate(cell.iso)} · ${cell.day.count} операций · ${formatMoney(cell.day.total_amount)}`
                    : undefined
                }
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
