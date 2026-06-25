import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Coins,
  PieChart,
  RefreshCw,
  Settings,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { useBrokerPortfolio } from '@/hooks/useQueries'
import { brokerSettings } from '@/lib/brokerSettings'
import { EmptyState } from '@/components/EmptyState'
import { ApiException } from '@/lib/api'
import { formatDate, formatMoney, formatNumber, formatRelative } from '@/lib/format'
import type { BrokerTransactionKind } from '@/lib/types'

const INCOME_LABELS: Record<'coupon' | 'dividend' | 'redemption' | 'lending' | 'other' | 'commission', string> = {
  coupon: 'Купонный доход',
  dividend: 'Дивиденды',
  redemption: 'Погашения ценных бумаг',
  lending: 'Доход от займа ЦБ',
  other: 'Прочий доход',
  commission: 'Комиссии брокера',
}

const NEUTRAL_KINDS: BrokerTransactionKind[] = ['deposit', 'withdrawal']
const PAGE_SIZE = 10

function amountClass(kind: BrokerTransactionKind, amount: number): string {
  if (NEUTRAL_KINDS.includes(kind)) return 'mono'
  return `mono ${amount >= 0 ? 'value-positive' : 'value-negative'}`
}

function Pager({
  page, totalPages, onChange,
}: { page: number; totalPages: number; onChange: (page: number) => void }) {
  if (totalPages <= 1) return null
  return (
    <div className="row-between" style={{ marginTop: 12 }}>
      <span className="muted">Стр. {page} из {totalPages}</span>
      <div className="row" style={{ gap: 6 }}>
        <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft size={14} />
        </button>
        <button className="btn btn-ghost btn-sm" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}

export function BrokerPage() {
  const portfolio = useBrokerPortfolio()
  const [positionsPage, setPositionsPage] = useState(1)
  const [transactionsPage, setTransactionsPage] = useState(1)

  if (!brokerSettings.get()) {
    return (
      <div className="card">
        <EmptyState
          title="Брокерский счёт не подключён"
          description="Укажите токен Finam и номер счёта в настройках, чтобы увидеть портфель"
          icon={<Briefcase size={36} />}
          action={
            <Link to="/settings" className="btn btn-primary">
              <Settings size={16} /> Перейти в настройки
            </Link>
          }
        />
      </div>
    )
  }

  if (portfolio.isLoading) {
    return <div className="card"><div className="muted">Загрузка…</div></div>
  }

  if (portfolio.isError || !portfolio.data) {
    const message = portfolio.error instanceof ApiException
      ? portfolio.error.message
      : 'Не удалось получить данные с брокерского счёта'
    return (
      <div className="card">
        <EmptyState
          title="Брокерский счёт недоступен"
          description={message}
          icon={<Briefcase size={36} />}
          action={
            <button className="btn btn-primary" onClick={() => portfolio.refetch()}>
              <RefreshCw size={16} /> Повторить
            </button>
          }
        />
      </div>
    )
  }

  const data = portfolio.data
  const unrealizedPnl = Number(data.unrealized_pnl)
  const dailyPnl = Number(data.daily_pnl)
  const totalReturn = Number(data.income.total_return)
  const cashHint = data.cash.length
    ? data.cash.map((c) => `${formatNumber(c.amount)} ${c.currency}`).join(' · ')
    : '—'
  const cashTotalRub = data.cash.find((c) => c.currency === 'RUB')?.amount ?? 0

  const positionsTotalPages = Math.max(1, Math.ceil(data.positions.length / PAGE_SIZE))
  const positionsPageClamped = Math.min(positionsPage, positionsTotalPages)
  const visiblePositions = data.positions.slice(
    (positionsPageClamped - 1) * PAGE_SIZE,
    positionsPageClamped * PAGE_SIZE,
  )

  const transactionsTotalPages = Math.max(1, Math.ceil(data.transactions.length / PAGE_SIZE))
  const transactionsPageClamped = Math.min(transactionsPage, transactionsTotalPages)
  const visibleTransactions = data.transactions.slice(
    (transactionsPageClamped - 1) * PAGE_SIZE,
    transactionsPageClamped * PAGE_SIZE,
  )

  return (
    <>
      <div className="row-between page-toolbar">
        <div className="muted">
          Счёт {data.account_id} • Обновлено {formatRelative(data.updated_at)}
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => portfolio.refetch()}
          disabled={portfolio.isFetching}
        >
          <RefreshCw size={14} /> {portfolio.isFetching ? 'Обновление…' : 'Обновить'}
        </button>
      </div>

      <section className="kpi-grid">
        <div className="kpi">
          <span className="label"><Briefcase size={14} /> Общая стоимость</span>
          <span className="value mono">{formatMoney(data.equity)}</span>
        </div>
        <div className="kpi">
          <span className="label"><Wallet size={14} /> Денежные средства</span>
          <span className="value mono">{formatMoney(cashTotalRub)}</span>
          <span className="hint">{cashHint}</span>
        </div>
        <div className="kpi">
          <span className="label">
            {unrealizedPnl >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />} Общий P&L
          </span>
          <span className={`value mono ${unrealizedPnl >= 0 ? 'value-positive' : 'value-negative'}`}>
            {unrealizedPnl >= 0 ? '+' : ''}{formatMoney(unrealizedPnl)}
          </span>
        </div>
        <div className="kpi">
          <span className="label">
            {dailyPnl >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />} P&L за день
          </span>
          <span className={`value mono ${dailyPnl >= 0 ? 'value-positive' : 'value-negative'}`}>
            {dailyPnl >= 0 ? '+' : ''}{formatMoney(dailyPnl)}
          </span>
          <span className="hint">изменение за сегодня</span>
        </div>
        <div className="kpi">
          <span className="label"><Coins size={14} /> Доход с купонами и дивидендами</span>
          <span className={`value mono ${totalReturn >= 0 ? 'value-positive' : 'value-negative'}`}>
            {totalReturn >= 0 ? '+' : ''}{formatMoney(totalReturn)}
          </span>
          <span className="hint">с {formatDate(data.income.period_from)}</span>
        </div>
      </section>

      {data.allocation.length > 0 && (
        <section className="card">
          <div className="card-header">
            <h2>Распределение по классам активов</h2>
            <span className="card-subtitle"><PieChart size={14} /></span>
          </div>
          <div className="col" style={{ gap: 12 }}>
            {data.allocation.map((a) => (
              <div key={a.asset_class}>
                <div className="row-between" style={{ marginBottom: 6 }}>
                  <span>{a.asset_class}</span>
                  <span className="muted mono">
                    {formatMoney(a.market_value)} • {a.weight_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="progress">
                  <div className="progress-bar" style={{ width: `${a.weight_percent}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card">
        <div className="card-header">
          <h2>Доход по типам</h2>
          <span className="card-subtitle">с {formatDate(data.income.period_from)}</span>
        </div>
        <div className="col" style={{ gap: 10 }}>
          {(['coupon', 'dividend', 'redemption', 'lending', 'other', 'commission'] as const)
            .filter((key) => Number(data.income[key]) !== 0)
            .map((key) => {
              const amount = Number(data.income[key])
              return (
                <div key={key} className="row-between">
                  <span className="muted">{INCOME_LABELS[key]}</span>
                  <span className={`mono ${amount >= 0 ? 'value-positive' : 'value-negative'}`}>
                    {amount >= 0 ? '+' : ''}{formatMoney(amount)}
                  </span>
                </div>
              )
            })}
          <div className="row-between" style={{ paddingTop: 10, borderTop: '1px solid var(--border)' }}>
            <span style={{ fontWeight: 500 }}>Итого с учётом P&L</span>
            <span className={`mono ${totalReturn >= 0 ? 'value-positive' : 'value-negative'}`} style={{ fontWeight: 600 }}>
              {totalReturn >= 0 ? '+' : ''}{formatMoney(totalReturn)}
            </span>
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>Позиции</h2>
          <span className="card-subtitle">{data.positions.length} инструментов</span>
        </div>
        {data.positions.length === 0 ? (
          <EmptyState title="Нет открытых позиций" />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Инструмент</th>
                  <th>Класс актива</th>
                  <th>Кол-во</th>
                  <th>Средняя цена</th>
                  <th>Текущая цена</th>
                  <th>Стоимость</th>
                  <th>P&L за день</th>
                  <th>Общий P&L</th>
                  <th>Доля</th>
                </tr>
              </thead>
              <tbody>
                {visiblePositions.map((p) => {
                  const pnl = Number(p.unrealized_pnl)
                  const daily = Number(p.daily_pnl)
                  return (
                    <tr key={p.symbol}>
                      <td>
                        <div style={{ fontWeight: 500 }}>{p.name ?? p.symbol}</div>
                        <div className="dim">{p.symbol}</div>
                      </td>
                      <td>{p.asset_class ?? '—'}</td>
                      <td className="mono">{formatNumber(p.quantity)}</td>
                      <td className="mono">
                        {formatMoney(p.average_price)}
                        {p.average_price_percent !== null && (
                          <div className="dim">{Number(p.average_price_percent).toFixed(2)}%</div>
                        )}
                      </td>
                      <td className="mono">
                        {formatMoney(p.current_price)}
                        {p.current_price_percent !== null && (
                          <div className="dim">{Number(p.current_price_percent).toFixed(2)}%</div>
                        )}
                      </td>
                      <td className="mono">{formatMoney(p.market_value)}</td>
                      <td className={`mono ${daily >= 0 ? 'value-positive' : 'value-negative'}`}>
                        {daily >= 0 ? '+' : ''}{formatMoney(daily)}
                      </td>
                      <td className={`mono ${pnl >= 0 ? 'value-positive' : 'value-negative'}`}>
                        {pnl >= 0 ? '+' : ''}{formatMoney(pnl)} ({p.unrealized_pnl_percent.toFixed(1)}%)
                      </td>
                      <td className="mono">{p.weight_percent.toFixed(1)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <Pager page={positionsPageClamped} totalPages={positionsTotalPages} onChange={setPositionsPage} />
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <h2>Последние операции</h2>
          <span className="card-subtitle">{data.transactions.length} операций</span>
        </div>
        {data.transactions.length === 0 ? (
          <EmptyState title="Операций не найдено" />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Операция</th>
                  <th>Инструмент</th>
                  <th>Сумма</th>
                </tr>
              </thead>
              <tbody>
                {visibleTransactions.map((tx) => {
                  const amount = Number(tx.amount)
                  return (
                    <tr key={tx.id}>
                      <td className="dim">{formatDate(tx.timestamp, true)}</td>
                      <td>{tx.name}</td>
                      <td className="dim">{tx.symbol ?? '—'}</td>
                      <td className={amountClass(tx.kind, amount)}>
                        {amount >= 0 ? '+' : ''}{formatMoney(amount)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <Pager page={transactionsPageClamped} totalPages={transactionsTotalPages} onChange={setTransactionsPage} />
          </div>
        )}
      </section>
    </>
  )
}
