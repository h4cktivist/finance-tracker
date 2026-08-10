import { endOfMonth, format, formatDistanceToNow, parseISO, startOfMonth } from 'date-fns'
import { ru } from 'date-fns/locale'

const currencyFmt = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 2,
})

const numberFmt = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 })

export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (!Number.isFinite(n)) return '—'
  return currencyFmt.format(n)
}

export function formatNumber(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '0'
  const n = typeof value === 'string' ? Number(value) : value
  if (!Number.isFinite(n)) return '0'
  return numberFmt.format(n)
}

export function formatDate(value: string | null | undefined, withTime = false): string {
  if (!value) return '—'
  try {
    const d = parseISO(value)
    return format(d, withTime ? 'dd MMM yyyy, HH:mm' : 'dd MMM yyyy', { locale: ru })
  } catch {
    return value
  }
}

export function formatRelative(value: string): string {
  try {
    const d = parseISO(value)
    return formatDistanceToNow(d, { addSuffix: true, locale: ru })
  } catch {
    return value
  }
}

export function todayIso(): string {
  return format(new Date(), 'yyyy-MM-dd')
}

/** `2026-07` → `июль 2026` */
export function formatPeriodMonth(value: string | null | undefined): string {
  if (!value) return '—'
  try {
    return format(parseISO(`${value}-01`), 'LLLL yyyy', { locale: ru })
  } catch {
    return value
  }
}

export function currentMonthStartIso(): string {
  return toIsoDate(startOfMonth(new Date()))
}

export function currentMonthEndIso(): string {
  return toIsoDate(endOfMonth(new Date()))
}

export function toIsoDate(value: Date): string {
  return format(value, 'yyyy-MM-dd')
}
