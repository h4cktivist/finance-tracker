import { useMemo } from 'react'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Modal } from '@/components/Modal'
import { useAnalyticsPreferences } from '@/context/AnalyticsPreferencesContext'
import { useAccounts, useCategories, useTransactions } from '@/hooks/useQueries'
import { formatMoney } from '@/lib/format'

/** Категория, которую бэкенд исключает из аналитики при `exclude_investments`. */
const INVESTMENT_CATEGORY_NAME = 'Инвестиции'

const PAGE_SIZE = 100

export type DaySelection = {
  date: string
  kind: 'income' | 'expenses'
  /** Сумма из точки графика — показывается как итог, чтобы совпадать с графиком. */
  total: number
}

export function DayTransactionsModal({
  selection, onClose,
}: {
  selection: DaySelection
  onClose: () => void
}) {
  const { excludeInvestments } = useAnalyticsPreferences()
  const isIncome = selection.kind === 'income'

  const transactions = useTransactions({
    type: isIncome ? 'income' : 'expense',
    date_from: selection.date,
    date_to: selection.date,
    page_size: PAGE_SIZE,
    sort_by: 'amount',
    sort_order: 'desc',
  })
  const categories = useCategories()
  const accounts = useAccounts()

  const categoryMap = useMemo(
    () => Object.fromEntries((categories.data ?? []).map((c) => [c.id, c])),
    [categories.data],
  )
  const accountMap = useMemo(
    () => Object.fromEntries((accounts.data ?? []).map((a) => [a.id, a])),
    [accounts.data],
  )

  const investmentIds = useMemo(
    () =>
      new Set(
        (categories.data ?? [])
          .filter((c) => c.type === 'expense' && c.name === INVESTMENT_CATEGORY_NAME)
          .map((c) => c.id),
      ),
    [categories.data],
  )

  // Тот же отбор, что и в графике: при включённом тумблере расходы на инвестиции не считаются
  const items = useMemo(() => {
    const all = transactions.data?.items ?? []
    if (isIncome || !excludeInvestments || investmentIds.size === 0) return all
    return all.filter((t) => !t.category_id || !investmentIds.has(t.category_id))
  }, [transactions.data, isIncome, excludeInvestments, investmentIds])

  const truncated = (transactions.data?.total ?? 0) > PAGE_SIZE

  return (
    <Modal
      open
      onClose={onClose}
      size="lg"
      title={isIncome ? 'Поступления за день' : 'Траты за день'}
      subtitle={format(parseISO(selection.date), 'd MMMM yyyy', { locale: ru })}
    >
      <div
        className="row-between"
        style={{
          padding: 12,
          borderRadius: 10,
          background: isIncome ? 'rgba(45,212,191,0.08)' : 'rgba(239,71,97,0.08)',
        }}
      >
        <span className="muted">Итого за день</span>
        <span
          className={`mono ${isIncome ? 'value-positive' : 'value-negative'}`}
          style={{ fontSize: 18, fontWeight: 600 }}
        >
          {isIncome ? '+' : '−'}{formatMoney(selection.total)}
        </span>
      </div>

      {transactions.isLoading ? (
        <p className="dim" style={{ marginTop: 14 }}>Загрузка…</p>
      ) : items.length === 0 ? (
        <div className="empty"><p>Операций за этот день нет</p></div>
      ) : (
        <>
          <div className="table-wrap" style={{ marginTop: 14 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Категория</th>
                  <th>Описание</th>
                  <th className="col-desktop-only">Счёт</th>
                  <th style={{ textAlign: 'right' }}>Сумма</th>
                </tr>
              </thead>
              <tbody>
                {items.map((t) => {
                  const category = t.category_id ? categoryMap[t.category_id] : null
                  return (
                    <tr key={t.id}>
                      <td>
                        {category ? (
                          <span className="row" style={{ gap: 8 }}>
                            {category.color && (
                              <span
                                className="color-swatch"
                                style={{ background: category.color, margin: 0 }}
                              />
                            )}
                            <span>{category.name}</span>
                          </span>
                        ) : (
                          <span className="dim">—</span>
                        )}
                      </td>
                      <td>
                        <div>{t.description || <span className="dim">—</span>}</div>
                        {t.merchant_name && <div className="dim">{t.merchant_name}</div>}
                      </td>
                      <td className="col-desktop-only">
                        {accountMap[t.account_id]?.name ?? <span className="dim">—</span>}
                      </td>
                      <td className="mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                        <span className={isIncome ? 'value-positive' : 'value-negative'}>
                          {isIncome ? '+' : '−'}{formatMoney(t.amount)}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <span className="hint" style={{ display: 'block', marginTop: 10 }}>
            {truncated
              ? `Показаны первые ${PAGE_SIZE} операций из ${transactions.data?.total}`
              : `Операций: ${items.length}`}
          </span>
        </>
      )}

      <div className="modal-actions">
        <button type="button" className="btn btn-ghost" onClick={onClose}>Закрыть</button>
      </div>
    </Modal>
  )
}
