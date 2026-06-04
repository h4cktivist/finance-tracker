import { useState } from 'react'
import { Lightbulb, Pencil, Plus, Target, Trash2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useBudgetRecommendations,
  useBudgetStatus,
  useBudgets,
  useCategories,
  useCreateBudget,
  useDeleteBudget,
  useUpdateBudget,
} from '@/hooks/useQueries'
import type {
  Budget,
  BudgetPeriodType,
  BudgetRecommendation,
  BudgetRecommendations,
} from '@/lib/types'
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

const REC_ACTION: Record<BudgetRecommendation['recommendation_type'], string> = {
  create: 'Создать бюджет',
  increase: 'Повысить лимит',
  decrease: 'Снизить лимит',
}

const REC_TITLE: Record<BudgetRecommendation['recommendation_type'], string> = {
  create: 'Новый бюджет',
  increase: 'Повысить лимит',
  decrease: 'Снизить лимит',
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

  const [createPrefill, setCreatePrefill] = useState<{
    category_id: string
    amount_limit: string
  } | null>(null)
  const [suggestedLimit, setSuggestedLimit] = useState<string | undefined>()

  const budgets = useBudgets()
  const recommendations = useBudgetRecommendations()
  const categories = useCategories()
  const create = useCreateBudget()
  const update = useUpdateBudget()
  const remove = useDeleteBudget()

  const categoryMap = Object.fromEntries((categories.data ?? []).map((c) => [c.id, c]))
  const budgetById = Object.fromEntries((budgets.data ?? []).map((b) => [b.id, b]))

  function applyRecommendation(rec: BudgetRecommendation) {
    setSuggestedLimit(rec.suggested_amount_limit)
    if (rec.recommendation_type === 'create') {
      setEditing(null)
      setCreatePrefill({
        category_id: rec.category_id,
        amount_limit: rec.suggested_amount_limit,
      })
      setOpen(true)
      return
    }
    const budget = rec.existing_budget_id ? budgetById[rec.existing_budget_id] : null
    if (!budget) return
    setCreatePrefill(null)
    setEditing(budget)
    setOpen(true)
  }

  function openNewBudget() {
    setEditing(null)
    setCreatePrefill(null)
    setSuggestedLimit(undefined)
    setOpen(true)
  }

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
        <button className="btn btn-primary" onClick={openNewBudget}>
          <Plus size={16} /> Новый бюджет
        </button>
      </div>

      <BudgetRecommendationsPanel
        data={recommendations.data}
        isLoading={recommendations.isLoading}
        onApply={applyRecommendation}
        applying={create.isPending || update.isPending}
      />

      {budgets.isLoading ? (
        <div className="card"><div className="muted">Загрузка…</div></div>
      ) : !budgets.data || budgets.data.length === 0 ? (
        <div className="card">
          <EmptyState
            title="Нет бюджетов"
            description="Создайте первый бюджет, чтобы контролировать расходы"
            icon={<Target size={36} />}
            action={
              <button className="btn btn-primary" onClick={openNewBudget}>
                <Plus size={16} /> Создать
              </button>
            }
          />
        </div>
      ) : (
        <div className="grid-2">
          {budgets.data.map((b) => (
            <BudgetCard
              key={b.id}
              budget={b}
              categoryName={b.category_id ? categoryMap[b.category_id]?.name ?? '—' : '—'}
              onEdit={() => {
                setCreatePrefill(null)
                setSuggestedLimit(undefined)
                setEditing(b)
                setOpen(true)
              }}
              onDelete={() => setDeleting(b)}
            />
          ))}
        </div>
      )}

      <BudgetFormModal
        open={open}
        onClose={() => {
          setOpen(false)
          setCreatePrefill(null)
          setSuggestedLimit(undefined)
        }}
        editing={editing}
        createPrefill={createPrefill}
        suggestedLimit={suggestedLimit}
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

function BudgetRecommendationsPanel({
  data,
  isLoading,
  onApply,
  applying,
}: {
  data: BudgetRecommendations | undefined
  isLoading: boolean
  onApply: (rec: BudgetRecommendation) => void
  applying: boolean
}) {
  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h2><Lightbulb size={18} style={{ verticalAlign: -3, marginRight: 8 }} />Рекомендации по бюджетам</h2>
        </div>
        <p className="dim">Анализ трат…</p>
      </div>
    )
  }
  if (!data || data.items.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h2><Lightbulb size={18} style={{ verticalAlign: -3, marginRight: 8 }} />Рекомендации по бюджетам</h2>
        </div>
        <p className="dim" style={{ fontSize: 13 }}>
          Недостаточно данных за последние {data?.months_analyzed ?? 3} мес. (нужны регулярные расходы
          от 500 ₽ и минимум 2 операции по категории).
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2><Lightbulb size={18} style={{ verticalAlign: -3, marginRight: 8 }} />Рекомендации по бюджетам</h2>
        <span className="dim" style={{ fontSize: 13 }}>
          На основе трат за {data.months_analyzed} мес., без ИИ
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {data.items.map((rec) => {
          const variant =
            rec.recommendation_type === 'create'
              ? 'info'
              : rec.recommendation_type === 'increase'
                ? 'warning'
                : 'success'
          return (
            <div
              key={`${rec.category_id}-${rec.recommendation_type}`}
              style={{
                padding: 14,
                borderRadius: 12,
                border: '1px solid var(--border)',
                background: 'rgba(11,16,32,0.35)',
              }}
            >
              <div className="row-between" style={{ alignItems: 'flex-start', gap: 12 }}>
                <div>
                  <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
                    <strong>{rec.category_name}</strong>
                    <span className={`badge badge-${variant}`}>{REC_TITLE[rec.recommendation_type]}</span>
                  </div>
                  <p className="dim" style={{ margin: '8px 0 0', fontSize: 13, lineHeight: 1.45 }}>
                    {rec.reason}
                  </p>
                  <div className="dim" style={{ marginTop: 8, fontSize: 12 }}>
                    Среднее {formatMoney(rec.avg_monthly_spent)}/мес. · пик {formatMoney(rec.max_monthly_spent)}
                    {' · '}{rec.transaction_count} операций
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div className="mono" style={{ fontSize: 18, fontWeight: 700 }}>
                    {formatMoney(rec.suggested_amount_limit)}
                  </div>
                  <div className="dim" style={{ fontSize: 12 }}>лимит / мес.</div>
                  {rec.current_amount_limit && (
                    <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>
                      сейчас {formatMoney(rec.current_amount_limit)}
                    </div>
                  )}
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    style={{ marginTop: 10 }}
                    disabled={applying}
                    onClick={() => onApply(rec)}
                  >
                    {REC_ACTION[rec.recommendation_type]}
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function BudgetFormModal({
  open,
  onClose,
  editing,
  createPrefill,
  suggestedLimit,
  categories,
  onSubmit,
  submitting,
}: {
  open: boolean
  onClose: () => void
  editing: Budget | null
  createPrefill: { category_id: string; amount_limit: string } | null
  suggestedLimit?: string
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
          amount_limit: suggestedLimit ?? editing.amount_limit,
          period_type: editing.period_type,
          start_date: editing.start_date,
          end_date: editing.end_date ?? '',
          rollover_enabled: editing.rollover_enabled,
        }
      : createPrefill
        ? {
            category_id: createPrefill.category_id,
            amount_limit: createPrefill.amount_limit,
            period_type: 'monthly',
            start_date: todayIso(),
            end_date: '',
            rollover_enabled: false,
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
