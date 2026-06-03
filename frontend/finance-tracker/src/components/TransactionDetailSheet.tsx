import type { ReactNode } from 'react'
import {
  ArrowDownRight,
  ArrowLeftRight,
  ArrowUpRight,
  Pencil,
  RotateCcw,
  Trash2,
} from 'lucide-react'
import type { Account, Category, Tag, Transaction, TransactionType } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { formatDate, formatMoney } from '@/lib/format'

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
}: Props) {
  if (!t) return null

  const acc = accountMap[t.account_id]
  const cat = t.category_id ? categoryMap[t.category_id] : null
  const card = t.card_id ? cardMap[t.card_id] : null
  const amountClass =
    t.type === 'income' ? 'value-positive' : t.type === 'expense' ? 'value-negative' : ''
  const amountPrefix = t.type === 'expense' ? '−' : t.type === 'income' ? '+' : ''

  const title = t.description || t.merchant_name || 'Операция'
  const subtitle = formatDate(t.transaction_date)

  return (
    <Modal open onClose={onClose} title={title} subtitle={subtitle}>
      <div className="tx-detail-amount mono">
        <span className={amountClass}>
          {amountPrefix}
          {formatMoney(t.amount)}
        </span>
      </div>

      <div className="tx-detail-grid">
        <DetailRow label="Тип">{typeBadge(t.type)}</DetailRow>

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

        {t.merchant_name && t.description && (
          <DetailRow label="Магазин">{t.merchant_name}</DetailRow>
        )}

        {t.tag_ids.length > 0 && (
          <DetailRow label="Теги">
            <div className="row" style={{ gap: 4, flexWrap: 'wrap' }}>
              {t.tag_ids.map((id) => {
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

        {t.type === 'expense' && (
          <DetailRow label="Кэшбэк">
            {t.cashback_amount && Number(t.cashback_amount) > 0 ? (
              <span className="mono value-positive">+{formatMoney(t.cashback_amount)}</span>
            ) : (
              <span className="dim">—</span>
            )}
          </DetailRow>
        )}

        {t.notes && <DetailRow label="Заметки">{t.notes}</DetailRow>}

        {t.correction_of_id && (
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
            onEdit(t)
          }}
        >
          <Pencil size={14} /> Редактировать
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            onClose()
            onCorrect(t)
          }}
        >
          <RotateCcw size={14} /> Исправление
        </button>
        <button
          type="button"
          className="btn btn-danger"
          onClick={() => {
            onClose()
            onDelete(t)
          }}
        >
          <Trash2 size={14} /> Удалить
        </button>
      </div>
    </Modal>
  )
}
