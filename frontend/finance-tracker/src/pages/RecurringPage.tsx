import { useState } from 'react'
import { Pause, Play, Plus, RefreshCw } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useAccounts,
  useCategories,
  useCreateRecurring,
  useRecurring,
  useUpdateRecurring,
} from '@/hooks/useQueries'
import type { Recurring, RecurringFrequency, TransactionType } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { EmptyState } from '@/components/EmptyState'
import { formatDate, formatMoney, todayIso } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

const FREQ_LABELS: Record<RecurringFrequency, string> = {
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
  monthly: 'Ежемесячно',
  yearly: 'Ежегодно',
}

const schema = z.object({
  type: z.enum(['expense', 'income', 'transfer']),
  account_id: z.string().min(1),
  category_id: z.string().optional().or(z.literal('')),
  amount: z.string().refine((v) => Number(v) > 0, 'Сумма должна быть > 0'),
  frequency: z.enum(['daily', 'weekly', 'monthly', 'yearly']),
  interval: z.string().refine((v) => Number(v) >= 1, '≥ 1'),
  start_date: z.string().min(1),
  end_date: z.string().optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
  merchant_name: z.string().optional().or(z.literal('')),
})
type FormValues = z.infer<typeof schema>

export function RecurringPage() {
  const [open, setOpen] = useState(false)
  const recurring = useRecurring()
  const accounts = useAccounts()
  const categories = useCategories()
  const create = useCreateRecurring()
  const update = useUpdateRecurring()

  const accMap = Object.fromEntries((accounts.data ?? []).map((a) => [a.id, a]))
  const catMap = Object.fromEntries((categories.data ?? []).map((c) => [c.id, c]))

  async function toggle(r: Recurring) {
    try {
      await update.mutateAsync({ id: r.id, data: { is_active: !r.is_active } })
      toast.success(r.is_active ? 'Приостановлено' : 'Возобновлено')
    } catch (e) {
      handleApiError(e)
    }
  }

  return (
    <>
      <div className="row-between page-toolbar">
        <div className="muted">Подписки, ежемесячные платежи и регулярные операции</div>
        <button className="btn btn-primary" onClick={() => setOpen(true)}>
          <Plus size={16} /> Добавить
        </button>
      </div>

      {recurring.isLoading ? (
        <div className="card"><div className="muted">Загрузка…</div></div>
      ) : !recurring.data || recurring.data.length === 0 ? (
        <div className="card">
          <EmptyState
            title="Нет повторяющихся операций"
            description="Добавьте подписки или регулярные платежи, чтобы они создавались автоматически"
            icon={<RefreshCw size={36} />}
            action={<button className="btn btn-primary" onClick={() => setOpen(true)}><Plus size={16} /> Добавить</button>}
          />
        </div>
      ) : (
        <div className="grid-2">
          {recurring.data.map((r) => (
            <div key={r.id} className="card">
              <div className="row-between recurring-card-header">
                <div>
                  <h3>{r.description || (r.category_id ? catMap[r.category_id]?.name : 'Без описания')}</h3>
                  <div className="dim">
                    {FREQ_LABELS[r.frequency]}{r.interval > 1 ? ` (каждые ${r.interval})` : ''} • {accMap[r.account_id]?.name ?? '—'}
                  </div>
                </div>
                <button
                  className={`btn btn-sm ${r.is_active ? 'btn-secondary' : 'btn-primary'}`}
                  onClick={() => toggle(r)}
                >
                  {r.is_active ? <><Pause size={14} /> Пауза</> : <><Play size={14} /> Возобновить</>}
                </button>
              </div>

              <div className="row-between" style={{ marginTop: 16 }}>
                <div>
                  <div className="dim">Сумма</div>
                  <div className="mono" style={{ fontSize: 20, fontWeight: 600, marginTop: 4 }}>
                    <span className={r.type === 'income' ? 'value-positive' : r.type === 'expense' ? 'value-negative' : ''}>
                      {r.type === 'expense' ? '−' : r.type === 'income' ? '+' : ''}
                      {formatMoney(r.amount)}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="dim">Следующая операция</div>
                  <div className="mono" style={{ marginTop: 4 }}>{formatDate(r.next_execution_date)}</div>
                </div>
              </div>

              <div className="row" style={{ marginTop: 10, gap: 6 }}>
                <span className={`badge ${r.is_active ? 'badge-success' : 'badge-muted'}`}>
                  {r.is_active ? 'Активна' : 'Приостановлена'}
                </span>
                {r.category_id && catMap[r.category_id] && (
                  <span className="badge badge-muted">{catMap[r.category_id]?.name}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {open && <RecurringModal
        onClose={() => setOpen(false)}
        accounts={accounts.data ?? []}
        categories={categories.data ?? []}
        onSubmit={async (v) => {
          try {
            await create.mutateAsync({
              type: v.type as TransactionType,
              account_id: v.account_id,
              category_id: v.category_id || null,
              amount: v.amount,
              frequency: v.frequency,
              interval: Number(v.interval),
              start_date: v.start_date,
              end_date: v.end_date || null,
              description: v.description || null,
              merchant_name: v.merchant_name || null,
            })
            toast.success('Создано')
            setOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={create.isPending}
      />}
    </>
  )
}

function RecurringModal({
  onClose, accounts, categories, onSubmit, submitting,
}: {
  onClose: () => void
  accounts: Array<{ id: string; name: string }>
  categories: Array<{ id: string; name: string; type: 'expense' | 'income' }>
  onSubmit: (v: FormValues) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, watch, reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: 'expense',
      account_id: '',
      category_id: '',
      amount: '',
      frequency: 'monthly',
      interval: '1',
      start_date: todayIso(),
      end_date: '',
      description: '',
      merchant_name: '',
    },
  })
  const type = watch('type')

  return (
    <Modal open onClose={() => { onClose(); reset() }} title="Новая повторяющаяся операция" size="lg">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-row form-row-2">
          <div className="field">
            <label>Тип</label>
            <select className="select" {...register('type')}>
              <option value="expense">Расход</option>
              <option value="income">Доход</option>
            </select>
          </div>
          <div className="field">
            <label>Сумма</label>
            <input className="input mono" type="number" step="0.01" min="0.01" {...register('amount')} />
            {errors.amount && <span className="field-error">{errors.amount.message}</span>}
          </div>
        </div>

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Счёт</label>
            <select className="select" {...register('account_id')}>
              <option value="">Выберите счёт</option>
              {accounts.map((a) => (<option key={a.id} value={a.id}>{a.name}</option>))}
            </select>
          </div>
          <div className="field">
            <label>Категория</label>
            <select className="select" {...register('category_id')}>
              <option value="">Без категории</option>
              {categories.filter((c) => c.type === (type === 'income' ? 'income' : 'expense')).map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Частота</label>
            <select className="select" {...register('frequency')}>
              <option value="daily">Ежедневно</option>
              <option value="weekly">Еженедельно</option>
              <option value="monthly">Ежемесячно</option>
              <option value="yearly">Ежегодно</option>
            </select>
          </div>
          <div className="field">
            <label>Каждые N периодов</label>
            <input className="input" type="number" min="1" {...register('interval')} />
          </div>
        </div>

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Начало</label>
            <input className="input" type="date" {...register('start_date')} />
          </div>
          <div className="field">
            <label>Конец (опц.)</label>
            <input className="input" type="date" {...register('end_date')} />
          </div>
        </div>

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Описание</label>
            <input className="input" placeholder="Например, Netflix" {...register('description')} />
          </div>
          <div className="field">
            <label>Магазин / получатель</label>
            <input className="input" {...register('merchant_name')} />
          </div>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '…' : 'Создать'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
