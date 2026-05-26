import { useState } from 'react'
import { CheckCircle2, Goal as GoalIcon, Pencil, Plus } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useAccounts,
  useCreateGoal,
  useGoals,
  useUpdateGoal,
} from '@/hooks/useQueries'
import type { Goal, GoalStatus } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { EmptyState } from '@/components/EmptyState'
import { formatDate, formatMoney } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

const STATUS_LABELS: Record<GoalStatus, string> = {
  active: 'Активна',
  completed: 'Достигнута',
  cancelled: 'Отменена',
}

const schema = z.object({
  name: z.string().min(1, 'Введите название').max(255),
  target_amount: z.string().refine((v) => Number(v) > 0, '> 0'),
  deadline: z.string().optional().or(z.literal('')),
  linked_account_id: z.string().optional().or(z.literal('')),
  status: z.enum(['active', 'completed', 'cancelled']).optional(),
})
type FormValues = z.infer<typeof schema>

export function GoalsPage() {
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Goal | null>(null)

  const goals = useGoals()
  const accounts = useAccounts()
  const create = useCreateGoal()
  const update = useUpdateGoal()

  const accMap = Object.fromEntries((accounts.data ?? []).map((a) => [a.id, a]))

  async function complete(g: Goal) {
    try {
      await update.mutateAsync({ id: g.id, data: { status: 'completed' } })
      toast.success('Цель достигнута!')
    } catch (e) {
      handleApiError(e)
    }
  }

  return (
    <>
      <div className="row-between">
        <div className="muted">Откладывайте деньги на крупные покупки и мечты</div>
        <button className="btn btn-primary" onClick={() => { setEditing(null); setOpen(true) }}>
          <Plus size={16} /> Новая цель
        </button>
      </div>

      {goals.isLoading ? (
        <div className="card"><div className="muted">Загрузка…</div></div>
      ) : !goals.data || goals.data.length === 0 ? (
        <div className="card">
          <EmptyState
            title="Целей пока нет"
            description="Поставьте свою первую финансовую цель"
            icon={<GoalIcon size={36} />}
            action={<button className="btn btn-primary" onClick={() => setOpen(true)}><Plus size={16} /> Создать</button>}
          />
        </div>
      ) : (
        <div className="grid-2">
          {goals.data.map((g) => {
            const target = Number(g.target_amount)
            const current = Number(g.current_amount)
            const percent = target > 0 ? Math.min(100, (current / target) * 100) : 0
            const remaining = Math.max(0, target - current)
            return (
              <div key={g.id} className="card">
                <div className="row-between">
                  <div>
                    <h3>{g.name}</h3>
                    <div className="dim">
                      {g.deadline ? `До ${formatDate(g.deadline)}` : 'Без срока'}
                      {g.linked_account_id && ` • Счёт: ${accMap[g.linked_account_id]?.name ?? '—'}`}
                    </div>
                  </div>
                  <div className="row" style={{ gap: 4 }}>
                    {g.status === 'active' && (
                      <button className="btn btn-ghost btn-icon btn-sm" onClick={() => complete(g)} title="Отметить достигнутой">
                        <CheckCircle2 size={14} />
                      </button>
                    )}
                    <button className="btn btn-ghost btn-icon btn-sm" onClick={() => { setEditing(g); setOpen(true) }}>
                      <Pencil size={14} />
                    </button>
                  </div>
                </div>

                <div style={{ marginTop: 16 }}>
                  <div className="row-between" style={{ marginBottom: 8 }}>
                    <span className="mono" style={{ fontSize: 20, fontWeight: 600 }}>
                      {formatMoney(current)}
                    </span>
                    <span className="muted mono">из {formatMoney(target)}</span>
                  </div>
                  <div className="progress">
                    <div
                      className={`progress-bar ${g.status === 'completed' ? 'success' : ''}`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <div className="row-between" style={{ marginTop: 8 }}>
                    <span className={`badge badge-${g.status === 'completed' ? 'success' : g.status === 'cancelled' ? 'muted' : 'primary'}`}>
                      {STATUS_LABELS[g.status]}
                    </span>
                    <span className="muted">
                      Осталось: <span className="mono">{formatMoney(remaining)}</span> ({percent.toFixed(0)}%)
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <GoalModal
        open={open}
        onClose={() => setOpen(false)}
        editing={editing}
        accounts={accounts.data ?? []}
        onSubmit={async (v) => {
          try {
            if (editing) {
              await update.mutateAsync({
                id: editing.id,
                data: {
                  name: v.name,
                  target_amount: v.target_amount,
                  deadline: v.deadline || null,
                  status: v.status ?? editing.status,
                },
              })
              toast.success('Цель обновлена')
            } else {
              await create.mutateAsync({
                name: v.name,
                target_amount: v.target_amount,
                deadline: v.deadline || null,
                linked_account_id: v.linked_account_id || null,
              })
              toast.success('Цель создана')
            }
            setOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={create.isPending || update.isPending}
      />
    </>
  )
}

function GoalModal({
  open, onClose, editing, accounts, onSubmit, submitting,
}: {
  open: boolean
  onClose: () => void
  editing: Goal | null
  accounts: Array<{ id: string; name: string }>
  onSubmit: (v: FormValues) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: editing
      ? {
          name: editing.name,
          target_amount: editing.target_amount,
          deadline: editing.deadline ?? '',
          linked_account_id: editing.linked_account_id ?? '',
          status: editing.status,
        }
      : {
          name: '', target_amount: '', deadline: '',
          linked_account_id: '', status: 'active',
        },
  })

  return (
    <Modal
      open={open}
      onClose={() => { onClose(); reset() }}
      title={editing ? 'Редактировать цель' : 'Новая цель'}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Название</label>
          <input className="input" placeholder="Например, Машина" {...register('name')} />
          {errors.name && <span className="field-error">{errors.name.message}</span>}
        </div>
        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Целевая сумма</label>
            <input className="input mono" type="number" step="0.01" min="0.01" {...register('target_amount')} />
            {errors.target_amount && <span className="field-error">{errors.target_amount.message}</span>}
          </div>
          <div className="field">
            <label>Срок (опц.)</label>
            <input className="input" type="date" {...register('deadline')} />
          </div>
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Привязать счёт (опц.)</label>
          <select className="select" {...register('linked_account_id')} disabled={!!editing}>
            <option value="">Без привязки</option>
            {accounts.map((a) => (<option key={a.id} value={a.id}>{a.name}</option>))}
          </select>
          <span className="dim" style={{ marginTop: 4 }}>
            Текущая сумма будет синхронизироваться с балансом счёта
          </span>
        </div>
        {editing && (
          <div className="field" style={{ marginTop: 12 }}>
            <label>Статус</label>
            <select className="select" {...register('status')}>
              <option value="active">Активна</option>
              <option value="completed">Достигнута</option>
              <option value="cancelled">Отменена</option>
            </select>
          </div>
        )}

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
