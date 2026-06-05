const CATEGORY_COLOR_FALLBACKS = [
  '#7c5cff',
  '#38bdf8',
  '#2dd4bf',
  '#f5b450',
  '#ef4761',
  '#a78bfa',
  '#34d399',
  '#22d3ee',
  '#10b981',
  '#facc15',
  '#fb923c',
  '#ec4899',
]

export function categoryChartColor(color: string | null | undefined, fallbackIndex: number): string {
  return color ?? CATEGORY_COLOR_FALLBACKS[fallbackIndex % CATEGORY_COLOR_FALLBACKS.length]
}
