import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  ArrowDownRight,
  ArrowLeftRight,
  ArrowUpRight,
  Pencil,
  RotateCcw,
  Trash2,
} from 'lucide-react'
import { toast } from 'sonner'
import type { Account, Card, Category, Tag, Transaction, TransactionType } from '@/lib/types'
import {
  useCards,
  useDeleteTransactionCashback,
  useSetTransactionCashback,
} from '@/hooks/useQueries'
import { Modal } from '@/components/Modal'
import { formatDate, formatMoney } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

type CardLike = { id: string; name: string }

function typeBadge(type: TransactionType) {
  if (type === 'income') {
    return (
      <span className="badge badge-success">
        <ArrowUpRight size={11} /> Доход
      </span>
    )
  }
  if (type === 'expense') {
    return (
      <span className="badge badge-danger">
        <ArrowDownRight size={11} /> Расход
      </span>
    )
  }
  return (
    <span className="badge badge-info">
      <ArrowLeftRight size={11} /> Перевод
    </span>
  )
}

function DetailRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="tx-detail-row">
      <span className="tx-detail-label">{label}</span>
      <div className="tx-detail-value">{children}</div>
    </div>
  )
}

type Props = {
  transaction: Transaction | null
  onClose: () => void
  accountMap: Record<string, Account>
  categoryMap: Record<string, Category>
  tagMap: Record<string, Tag>
  cardMap: Record<string, CardLike>
  onEdit: (t: Transaction) => void
  onCorrect: (t: Transaction) => void
  onDelete: (t: Transaction) => void
  onCashbackUpdated?: (t: Transaction) => void
}

function CashbackEditModal({
  open,
  onClose,
  transaction,
  cards,
  onUpdated,
}: {
  open: boolean
  onClose: () => void
  transaction: Transaction
  cards: Card[]
  onUpdated: (t: Transaction) => void
}) {
  const setCashback = useSetTransactionCashback()
  const deleteCashback = useDeleteTransactionCashback()
  const [amount, setAmount] = useState(
    transaction.cashback_amount ? String(transaction.cashback_amount) : '',
  )
  const [cardId, setCardId] = useState(transaction.card_id ?? cards[0]?.id ?? '')

  async function handleSave() {
    const parsed = Number(amount.replace(',', '.'))
    if (!amount.trim() || Number.isNaN(parsed) || parsed < 0) {
      toast.error('Введите корректную сумму кэшбэка')
      return
    }
    if (!transaction.card_id && !cardId) {
      toast.error('Выберите карту')
      return
    }
    try {
      await setCashback.mutateAsync({
        transactionId: transaction.id,
        data: {
          amount: parsed,
          card_id: transaction.card_id ? undefined : cardId,
        },
      })
      onUpdated({
        ...transaction,
        cashback_amount: parsed > 0 ? String(parsed) : null,
        cashback_is_manual: parsed > 0 ? true : null,
      })
      toast.success(parsed > 0 ? 'Кэшбэк сохранён' : 'Кэшбэк удалён')
      onClose()
    } catch (e) {
      handleApiError(e)
    }
  }

  async function handleRemove() {
    try {
      await deleteCashback.mutateAsync(transaction.id)
      onUpdated({
        ...transaction,
        cashback_amount: null,
        cashback_is_manual: null,
      })
      toast.success('Кэшбэк удалён')
      onClose()
    } catch (e) {
      handleApiError(e)
    }
  }

  const busy = setCashback.isPending || deleteCashback.isPending

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Редактирование кэшбэка"
      subtitle={formatDate(transaction.transaction_date)}
    >
      <div className="stack" style={{ gap: 10, marginTop: 4 }}>
        {!transaction.card_id && (
          <div className="field">
            <label>Карта</label>
            <select
              className="input"
              value={cardId}
              onChange={(e) => setCardId(e.target.value)}
              disabled={busy}
            >
              <option value="">Выберите карту</option>
              {cards.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="field">
          <label>Сумма кэшбэка</label>
          <input
            className="input mono"
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            disabled={busy}
          />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
          <button type="button" className="btn btn-primary" onClick={handleSave} disabled={busy}>
            Сохранить
          </button>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>
            Отмена
          </button>
          {transaction.cashback_amount && Number(transaction.cashback_amount) > 0 && (
            <button type="button" className="btn btn-danger" onClick={handleRemove} disabled={busy}>
              Удалить
            </button>
          )}
        </div>
      </div>
    </Modal>
  )
}

export function TransactionDetailSheet({
  transaction: t,
  onClose,
  accountMap,
  categoryMap,
  tagMap,
  cardMap,
  onEdit,
  onCorrect,
  onDelete,
  onCashbackUpdated,
}: Props) {
  const { data: cards = [] } = useCards()
  const [cashbackModalOpen, setCashbackModalOpen] = useState(false)
  const [localTx, setLocalTx] = useState<Transaction | null>(t)

  useEffect(() => {
    setLocalTx(t)
    setCashbackModalOpen(false)
  }, [t])

  if (!t || !localTx) return null

  const acc = accountMap[localTx.account_id]
  const cat = localTx.category_id ? categoryMap[localTx.category_id] : null
  const card = localTx.card_id ? cardMap[localTx.card_id] : null
  const amountClass =
    localTx.type === 'income' ? 'value-positive' : localTx.type === 'expense' ? 'value-negative' : ''
  const amountPrefix = localTx.type === 'expense' ? '−' : localTx.type === 'income' ? '+' : ''

  const title = localTx.description || localTx.merchant_name || 'Операция'
  const subtitle = formatDate(localTx.transaction_date)

  function handleCashbackUpdated(updated: Transaction) {
    setLocalTx(updated)
    onCashbackUpdated?.(updated)
  }

  return (
    <Modal open onClose={onClose} title={title} subtitle={subtitle}>
      <div className="tx-detail-amount mono">
        <span className={amountClass}>
          {amountPrefix}
          {formatMoney(localTx.amount)}
        </span>
      </div>

      <div className="tx-detail-grid">
        <DetailRow label="Тип">{typeBadge(localTx.type)}</DetailRow>

        {cat && (
          <DetailRow label="Категория">
            <span className="row" style={{ gap: 6 }}>
              {cat.color && (
                <span className="color-swatch" style={{ background: cat.color, margin: 0 }} />
              )}
              {cat.name}
            </span>
          </DetailRow>
        )}

        <DetailRow label="Счёт">{acc?.name ?? <span className="dim">—</span>}</DetailRow>

        {card && <DetailRow label="Карта">{card.name}</DetailRow>}

        {localTx.merchant_name && localTx.description && (
          <DetailRow label="Магазин">{localTx.merchant_name}</DetailRow>
        )}

        {localTx.tag_ids.length > 0 && (
          <DetailRow label="Теги">
            <div className="row" style={{ gap: 4, flexWrap: 'wrap' }}>
              {localTx.tag_ids.map((id) => {
                const tag = tagMap[id]
                return (
                  <span key={id} className="badge badge-muted">
                    {tag?.color && (
                      <span
                        className="color-swatch"
                        style={{ background: tag.color, margin: 0, width: 8, height: 8 }}
                      />
                    )}
                    {tag?.name ?? id.slice(0, 6)}
                  </span>
                )
              })}
            </div>
          </DetailRow>
        )}

        {localTx.type === 'expense' && (
          <DetailRow label="Кэшбэк">
            <span className="row" style={{ gap: 8, alignItems: 'center' }}>
              {localTx.cashback_amount && Number(localTx.cashback_amount) > 0 ? (
                <>
                  <span className="mono value-positive">
                    +{formatMoney(localTx.cashback_amount)}
                  </span>
                  {localTx.cashback_is_manual && (
                    <span className="badge badge-muted">вручную</span>
                  )}
                </>
              ) : (
                <span className="dim">—</span>
              )}
              <button
                type="button"
                className="btn btn-ghost btn-icon"
                aria-label="Редактировать кэшбэк"
                onClick={() => setCashbackModalOpen(true)}
                style={{ marginLeft: 'auto' }}
              >
                <Pencil size={14} />
              </button>
            </span>
          </DetailRow>
        )}

        {localTx.notes && <DetailRow label="Заметки">{localTx.notes}</DetailRow>}

        {localTx.correction_of_id && (
          <DetailRow label="Статус">
            <span className="badge badge-warning">Исправление</span>
          </DetailRow>
        )}
      </div>

      <div className="tx-detail-actions">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            onClose()
            onEdit(localTx)
          }}
        >
          <Pencil size={14} /> Редактировать
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            onClose()
            onCorrect(localTx)
          }}
        >
          <RotateCcw size={14} /> Исправление
        </button>
        <button
          type="button"
          className="btn btn-danger"
          onClick={() => {
            onClose()
            onDelete(localTx)
          }}
        >
          <Trash2 size={14} /> Удалить
        </button>
      </div>

      {localTx.type === 'expense' && (
        <CashbackEditModal
          open={cashbackModalOpen}
          onClose={() => setCashbackModalOpen(false)}
          transaction={localTx}
          cards={cards}
          onUpdated={handleCashbackUpdated}
        />
      )}
    </Modal>
  )
}
