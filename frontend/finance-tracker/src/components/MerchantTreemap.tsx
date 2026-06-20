import { Treemap, ResponsiveContainer } from 'recharts'
import type { CategoryMerchants } from '@/lib/types'
import { categoryChartColor } from '@/lib/categoryColor'
import { formatMoney } from '@/lib/format'

type Props = {
  categories: CategoryMerchants[]
}

type LeafDatum = {
  name: string
  size: number
  count: number
  category: string
  color: string
  share: number
}

type CategoryDatum = {
  name: string
  color: string
  children: LeafDatum[]
}

function buildData(categories: CategoryMerchants[]): CategoryDatum[] {
  return categories.map((cat, i) => {
    const color = categoryChartColor(cat.color, i)
    const total = Number(cat.total) || 1
    return {
      name: cat.category_name,
      color,
      children: cat.merchants.map((m) => ({
        name: m.merchant_name,
        size: Number(m.total),
        count: m.count,
        category: cat.category_name,
        color,
        share: (Number(m.total) / total) * 100,
      })),
    }
  })
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function MerchantCell(props: any) {
  const { x, y, width, height, depth, name, color, size, count, category, share } = props

  if (depth === 1) {
    return (
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{ fill: 'transparent', stroke: 'rgba(255,255,255,0.16)', strokeWidth: 2 }}
      />
    )
  }

  if (depth !== 2 || width <= 0 || height <= 0) return null

  const showText = width > 56 && height > 32
  const showAmount = width > 70 && height > 48
  return (
    <g>
      <rect
        x={x + 1}
        y={y + 1}
        width={Math.max(width - 2, 0)}
        height={Math.max(height - 2, 0)}
        rx={6}
        style={{ fill: color, fillOpacity: 0.55 + Math.min(share, 100) / 220, stroke: '#0b1020', strokeWidth: 1.5 }}
      >
        <title>
          {`${name} • ${category} • ${formatMoney(size)} • ${count} ${count === 1 ? 'операция' : 'операций'} • ${share.toFixed(0)}% категории`}
        </title>
      </rect>
      {showText && (
        <text x={x + 8} y={y + 17} fill="#fff" fontSize={12} fontWeight={600}>
          {truncate(name, Math.floor(width / 7))}
        </text>
      )}
      {showAmount && (
        <text x={x + 8} y={y + 33} fill="rgba(255,255,255,0.85)" fontSize={11}>
          {formatMoney(size)}
        </text>
      )}
    </g>
  )
}

export function MerchantTreemap({ categories }: Props) {
  const data = buildData(categories)
  return (
    <div className="merchant-treemap-block">
      <div className="chart-area merchant-treemap-area">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={data}
            dataKey="size"
            nameKey="name"
            aspectRatio={4 / 3}
            content={<MerchantCell />}
            isAnimationActive={false}
          />
        </ResponsiveContainer>
      </div>
      <div className="pie-legend">
        {data.map((cat) => (
          <span key={cat.name} className="pill">
            <span className="color-swatch" style={{ background: cat.color }} />
            {cat.name}
          </span>
        ))}
      </div>
    </div>
  )
}
