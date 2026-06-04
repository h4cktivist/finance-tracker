import { useState } from 'react'
import { Pencil, Plus, Target, Trash2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useBudgetStatus,
  useBudgets,
  useCategories,
  useCreateBudget,
  useDeleteBudget,
  useUpdateBudget,
} from '@/hooks/useQueries'
import type { Budget, BudgetPeriodType } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { formatDate, formatMoney, todayIso } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

const PERIOD_LABELS: Record<BudgetPeriodType, string> = {
  weekly: 'Неделя',
  monthly: 'Месяц',
  yearly: 'Год',
}

const createSchema = z.object({
  category_id: z.string().min(1, 'Выберите категорию'),
  amount_limit: z.string().refine((v) => Number(v) > 0, 'Сумма должна быть > 0'),
  period_type: z.enum(['weekly', 'monthly', 'yearly']),
  start_date: z.string().min(1),
  end_date: z.string().optional().or(z.literal('')),
  rollover_enabled: z.boolean().optional(),
})
type FormValues = z.infer<typeof createSchema>

export function BudgetsPage() {
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Budget | null>(null)
  const [deleting, setDeleting] = useState<Budget | null>(null)

  const budgets = useBudgets()
  const categories = useCategories()
  const create = useCreateBudget()
  const update = useUpdateBudget()
  const remove = useDeleteBudget()

  const categoryMap = Object.fromEntries((categories.data ?? []).map((c) => [c.id, c]))

  async function handleDelete() {
    if (!deleting) return
    try {
      await remove.mutateAsync(deleting.id)
      toast.success('Бюджет удалён')
      setDeleting(null)
    } catch (e) {
      handleApiError(e)
    }
  }

  return (
    <>
      <div className="row-between page-toolbar">
        <div className="muted">Управляйте лимитами по категориям расходов</div>
        <button className="btn btn-primary" onClick={() => { setEditing(null); setOpen(true) }}>
          <Plus size={16} /> Новый бюджет
        </button>
      </div>

      {budgets.isLoading ? (
        <div className="card"><div className="muted">Загрузка…</div></div>
      ) : !budgets.data || budgets.data.length === 0 ? (
        <div className="card">
          <EmptyState
            title="Нет бюджетов"
            description="Создайте первый бюджет, чтобы контролировать расходы"
            icon={<Target size={36} />}
            action={<button className="btn btn-primary" onClick={() => { setEditing(null); setOpen(true) }}><Plus size={16} /> Создать</button>}
          />
        </div>
      ) : (
        <div className="grid-2">
          {budgets.data.map((b) => (
            <BudgetCard
              key={b.id}
              budget={b}
              categoryName={b.category_id ? categoryMap[b.category_id]?.name ?? '—' : '—'}
              onEdit={() => { setEditing(b); setOpen(true) }}
              onDelete={() => setDeleting(b)}
            />
          ))}
        </div>
      )}

      <BudgetFormModal
        open={open}
        onClose={() => setOpen(false)}
        editing={editing}
        categories={(categories.data ?? []).filter((c) => c.type === 'expense')}
        onSubmit={async (values) => {
          try {
            if (editing) {
              await update.mutateAsync({
                id: editing.id,
                data: {
                  amount_limit: values.amount_limit,
                  end_date: values.end_date || null,
                  rollover_enabled: values.rollover_enabled,
                },
              })
              toast.success('Бюджет обновлён')
            } else {
              await create.mutateAsync({
                category_id: values.category_id,
                amount_limit: values.amount_limit,
                period_type: values.period_type,
                start_date: values.start_date,
                end_date: values.end_date || null,
                rollover_enabled: values.rollover_enabled,
              })
              toast.success('Бюджет создан')
            }
            setOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={create.isPending || update.isPending}
      />

      <ConfirmDialog
        open={!!deleting}
        title="Удалить бюджет?"
        confirmText="Удалить"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
        loading={remove.isPending}
      />
    </>
  )
}

function BudgetCard({
  budget, categoryName, onEdit, onDelete,
}: {
  budget: Budget
  categoryName: string
  onEdit: () => void
  onDelete: () => void
}) {
  const status = useBudgetStatus(budget.id)
  const s = status.data
  const variant = !s ? 'success' : s.is_exceeded ? 'danger' : s.percent_used > 80 ? 'warning' : 'success'

  return (
    <div className="card">
      <div className="row-between">
        <div>
          <h3>{categoryName}</h3>
          <div className="dim">
            {PERIOD_LABELS[budget.period_type]} • с {formatDate(budget.start_date)}
            {budget.end_date && ` до ${formatDate(budget.end_date)}`}
          </div>
        </div>
        <div className="row" style={{ gap: 4 }}>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onEdit}><Pencil size={14} /></button>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onDelete}><Trash2 size={14} /></button>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div className="row-between" style={{ marginBottom: 8 }}>
          <span className="mono" style={{ fontSize: 18, fontWeight: 600 }}>
            {formatMoney(s?.spent ?? 0)}
          </span>
          <span className="muted mono">из {formatMoney(budget.amount_limit)}</span>
        </div>
        <div className="progress">
          <div className={`progress-bar ${variant}`} style={{ width: `${Math.min(100, s?.percent_used ?? 0)}%` }} />
        </div>
        <div className="row-between" style={{ marginTop: 8 }}>
          <span className={`badge badge-${variant}`}>{(s?.percent_used ?? 0).toFixed(0)}% использовано</span>
          <span className="muted">
            Остаток: <span className="mono">{formatMoney(s?.remaining ?? budget.amount_limit)}</span>
          </span>
        </div>
        {s?.days_until_exceed !== null && s?.days_until_exceed !== undefined && (
          <div className="dim" style={{ marginTop: 8 }}>
            При текущем темпе лимит будет превышен через {s.days_until_exceed} дн.
          </div>
        )}
        {budget.rollover_enabled && (
          <div className="badge badge-info" style={{ marginTop: 8 }}>Перенос остатка включён</div>
        )}
      </div>
    </div>
  )
}

function BudgetFormModal({
  open, onClose, editing, categories, onSubmit, submitting,
}: {
  open: boolean
  onClose: () => void
  editing: Budget | null
  categories: Array<{ id: string; name: string }>
  onSubmit: (values: FormValues) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, reset,
  } = useForm<FormValues>({
    resolver: zodResolver(createSchema),
    values: editing
      ? {
          category_id: editing.category_id,
          amount_limit: editing.amount_limit,
          period_type: editing.period_type,
          start_date: editing.start_date,
          end_date: editing.end_date ?? '',
          rollover_enabled: editing.rollover_enabled,
        }
      : {
          category_id: '',
          amount_limit: '',
          period_type: 'monthly',
          start_date: todayIso(),
          end_date: '',
          rollover_enabled: false,
        },
  })

  return (
    <Modal open={open} onClose={() => { onClose(); reset() }} title={editing ? 'Редактировать бюджет' : 'Новый бюджет'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Категория</label>
          <select className="select" {...register('category_id')} disabled={!!editing}>
            <option value="">Выберите категорию</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          {errors.category_id && <span className="field-error">{errors.category_id.message}</span>}
        </div>
        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Лимит</label>
            <input className="input mono" type="number" step="0.01" min="0.01" {...register('amount_limit')} />
            {errors.amount_limit && <span className="field-error">{errors.amount_limit.message}</span>}
          </div>
          <div className="field">
            <label>Период</label>
            <select className="select" {...register('period_type')} disabled={!!editing}>
              <option value="weekly">Неделя</option>
              <option value="monthly">Месяц</option>
              <option value="yearly">Год</option>
            </select>
          </div>
        </div>
        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Начало</label>
            <input className="input" type="date" {...register('start_date')} disabled={!!editing} />
          </div>
          <div className="field">
            <label>Конец (опц.)</label>
            <input className="input" type="date" {...register('end_date')} />
          </div>
        </div>
        <label className="row" style={{ marginTop: 12, gap: 8, cursor: 'pointer' }}>
          <input type="checkbox" {...register('rollover_enabled')} />
          <span>Переносить остаток на следующий период</span>
        </label>

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '…' : editing ? 'Сохранить' : 'Создать'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
