import { useState } from 'react'
import type { FormEvent } from 'react'
import { toast } from 'sonner'
import { ArrowLeftRight, Bookmark, ChevronDown, Folder, Pencil, Trash2 } from 'lucide-react'
import {
  useApplyTemplate,
  useDeleteTemplate,
  useDeleteTransaction,
  useTemplates,
  useUpdateTemplate,
} from '@/hooks/useQueries'
import type { Account, Category, TransactionTemplate } from '@/lib/types'
import { getIcon } from '@/lib/icons'
import { formatMoney } from '@/lib/format'
import { handleApiError } from '@/lib/errors'
import { Modal } from '@/components/Modal'
import { ConfirmDialog } from '@/components/ConfirmDialog'

const COLLAPSED_KEY = 'transactions.templates.collapsed'

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === '1'
  } catch {
    return false
  }
}

function writeCollapsed(value: boolean) {
  try {
    localStorage.setItem(COLLAPSED_KEY, value ? '1' : '0')
  } catch {
    /* ignore */
  }
}

type Props = {
  accountMap: Record<string, Account>
  categoryMap: Record<string, Category>
}

export function TemplatesPanel({ accountMap, categoryMap }: Props) {
  const templates = useTemplates()
  const apply = useApplyTemplate()
  const removeTx = useDeleteTransaction()
  const update = useUpdateTemplate()
  const remove = useDeleteTemplate()

  const [collapsed, setCollapsed] = useState(readCollapsed)
  const [applyingId, setApplyingId] = useState<string | null>(null)
  const [editing, setEditing] = useState<TransactionTemplate | null>(null)
  const [deleting, setDeleting] = useState<TransactionTemplate | null>(null)

  const items = templates.data ?? []

  function toggle() {
    setCollapsed((v) => {
      writeCollapsed(!v)
      return !v
    })
  }

  async function handleApply(t: TransactionTemplate) {
    if (applyingId) return
    setApplyingId(t.id)
    try {
      const result = await apply.mutateAsync({ id: t.id })
      const created = Array.isArray(result) ? result[0] : result
      toast.success(`Операция «${t.name}» создана`, {
        action: {
          label: 'Отменить',
          onClick: () => {
            removeTx.mutate(created.id, {
              onSuccess: () => toast.success('Операция отменена'),
              onError: handleApiError,
            })
          },
        },
      })
    } catch (e) {
      handleApiError(e)
    } finally {
      setApplyingId(null)
    }
  }

  async function handleDelete() {
    if (!deleting) return
    try {
      await remove.mutateAsync(deleting.id)
      toast.success('Шаблон удалён')
      setDeleting(null)
    } catch (e) {
      handleApiError(e)
    }
  }

  return (
    <div className="card templates-panel">
      <button
        type="button"
        className="templates-panel-header"
        onClick={toggle}
        aria-expanded={!collapsed}
      >
        <Bookmark size={16} className="muted" />
        <span className="templates-panel-title">Шаблоны</span>
        {items.length > 0 && <span className="badge badge-muted">{items.length}</span>}
        <ChevronDown
          size={16}
          className="muted templates-panel-chevron"
          style={{ transform: collapsed ? 'rotate(-90deg)' : undefined }}
        />
      </button>

      {!collapsed && (
        <div className="templates-panel-body">
          {templates.isLoading ? (
            <div className="muted">Загрузка…</div>
          ) : items.length === 0 ? (
            <div className="muted" style={{ fontSize: 13 }}>
              Шаблонов пока нет. Откройте любую операцию и нажмите «В шаблоны» — потом её можно
              будет повторить одним нажатием.
            </div>
          ) : (
            <div className="templates-grid">
              {items.map((t) => (
                <TemplateTile
                  key={t.id}
                  template={t}
                  account={accountMap[t.account_id]}
                  target={t.target_account_id ? accountMap[t.target_account_id] : undefined}
                  category={t.category_id ? categoryMap[t.category_id] : undefined}
                  busy={applyingId === t.id}
                  disabled={!!applyingId}
                  onApply={() => handleApply(t)}
                  onEdit={() => setEditing(t)}
                  onDelete={() => setDeleting(t)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {editing && (
        <TemplateFormModal
          title="Редактировать шаблон"
          initialName={editing.name}
          initialAmount={editing.amount}
          submitting={update.isPending}
          onClose={() => setEditing(null)}
          onSubmit={async ({ name, amount }) => {
            try {
              await update.mutateAsync({ id: editing.id, data: { name, amount } })
              toast.success('Шаблон сохранён')
              setEditing(null)
            } catch (e) {
              handleApiError(e)
            }
          }}
        />
      )}

      <ConfirmDialog
        open={!!deleting}
        title="Удалить шаблон?"
        description={deleting ? `Шаблон «${deleting.name}» будет удалён. Операции, созданные по нему, останутся.` : undefined}
        confirmText="Удалить"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
        loading={remove.isPending}
      />
    </div>
  )
}

function renderTileIcon(t: TransactionTemplate, category?: Category) {
  if (t.type === 'transfer') return <ArrowLeftRight size={14} />
  const Icon = getIcon(category?.icon)
  if (Icon) return <Icon size={14} />
  return <Folder size={14} />
}

function TemplateTile({
  template: t,
  account,
  target,
  category,
  busy,
  disabled,
  onApply,
  onEdit,
  onDelete,
}: {
  template: TransactionTemplate
  account?: Account
  target?: Account
  category?: Category
  busy: boolean
  disabled: boolean
  onApply: () => void
  onEdit: () => void
  onDelete: () => void
}) {
  const color = t.type === 'transfer' ? 'var(--info)' : category?.color ?? undefined
  const amountClass = t.type === 'income' ? 'value-positive' : t.type === 'expense' ? 'value-negative' : ''
  const sign = t.type === 'expense' ? '−' : t.type === 'income' ? '+' : ''
  const meta =
    t.type === 'transfer'
      ? `${account?.name ?? '—'} → ${target?.name ?? '—'}`
      : [account?.name, category?.name].filter(Boolean).join(' · ')

  return (
    <div className={`template-tile ${busy ? 'is-busy' : ''}`}>
      <button
        type="button"
        className="template-tile-main"
        onClick={onApply}
        disabled={disabled}
        title="Создать операцию по шаблону (дата — сегодня)"
      >
        <span
          className="template-tile-icon"
          style={{ background: color ? `color-mix(in srgb, ${color} 14%, transparent)` : undefined, color }}
        >
          {renderTileIcon(t, category)}
        </span>
        <span className="template-tile-text">
          <span className="template-tile-name">{t.name}</span>
          {meta && <span className="template-tile-meta dim">{meta}</span>}
        </span>
        <span className={`mono template-tile-amount ${amountClass}`}>
          {busy ? '…' : `${sign}${formatMoney(t.amount)}`}
        </span>
      </button>
      <div className="template-tile-actions">
        <button type="button" className="btn btn-ghost btn-icon btn-sm" onClick={onEdit} title="Редактировать шаблон">
          <Pencil size={13} />
        </button>
        <button type="button" className="btn btn-ghost btn-icon btn-sm" onClick={onDelete} title="Удалить шаблон">
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  )
}

/** Монтируется условно — начальные значения берутся из пропсов при открытии. */
export function TemplateFormModal({
  title,
  subtitle,
  initialName,
  initialAmount,
  submitting,
  onClose,
  onSubmit,
}: {
  title: string
  subtitle?: string
  initialName: string
  /** Если задано — в форме появляется поле суммы. */
  initialAmount?: string
  submitting: boolean
  onClose: () => void
  onSubmit: (values: { name: string; amount?: string }) => void
}) {
  const [name, setName] = useState(initialName)
  const [amount, setAmount] = useState(initialAmount ?? '')

  const withAmount = initialAmount !== undefined

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      toast.error('Введите название шаблона')
      return
    }
    if (withAmount && !(Number(amount) > 0)) {
      toast.error('Сумма должна быть > 0')
      return
    }
    onSubmit({ name: trimmed, amount: withAmount ? amount : undefined })
  }

  return (
    <Modal open onClose={onClose} title={title} subtitle={subtitle}>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Название</label>
          <input
            className="input"
            value={name}
            maxLength={255}
            autoFocus
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        {withAmount && (
          <div className="field" style={{ marginTop: 12 }}>
            <label>Сумма</label>
            <input
              className="input mono"
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '…' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
