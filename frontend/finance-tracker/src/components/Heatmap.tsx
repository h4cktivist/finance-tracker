import type { HeatmapDay } from '@/lib/types'
import { formatDate, formatMoney } from '@/lib/format'

type Props = {
  days: HeatmapDay[]
}

function getLevel(intensity: number): string {
  if (intensity <= 0) return ''
  if (intensity < 0.25) return 'l1'
  if (intensity < 0.5) return 'l2'
  if (intensity < 0.8) return 'l3'
  return 'l4'
}

export function Heatmap({ days }: Props) {
  return (
    <div className="heatmap">
      {days.map((d) => (
        <div
          key={d.date}
          className={`heatmap-cell ${getLevel(d.intensity)}`}
          title={`${formatDate(d.date)} • ${d.count} операций • ${formatMoney(d.total_amount)}`}
        />
      ))}
    </div>
  )
}
