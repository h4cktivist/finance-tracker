import { useState } from 'react'
import { Banknote, CreditCard, Pencil, Plus, Trash2, Wallet, PiggyBank } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useAccounts,
  useCreateAccount,
  useDeleteAccount,
  useUpdateAccount,
} from '@/hooks/useQueries'
import type { Account, AccountType } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { formatMoney } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

const TYPE_LABELS: Record<AccountType, string> = {
  debit: 'Дебетовый',
  credit: 'Кредитный',
  cash: 'Наличные',
  savings: 'Сберегательный',
}
const TYPE_ICONS: Record<AccountType, typeof Wallet> = {
  debit: CreditCard,
  credit: CreditCard,
  cash: Banknote,
  savings: PiggyBank,
}

const schema = z.object({
  name: z.string().min(1, 'Введите название').max(255),
  type: z.enum(['debit', 'credit', 'cash', 'savings']),
  initial_balance: z.string().refine((v) => !isNaN(Number(v)) && Number(v) >= 0, 'Введите число ≥ 0'),
})

type FormValues = z.infer<typeof schema>

export function AccountsPage() {
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Account | null>(null)
  const [deleting, setDeleting] = useState<Account | null>(null)

  const { data, isLoading } = useAccounts()
  const create = useCreateAccount()
  const update = useUpdateAccount()
  const remove = useDeleteAccount()

  function openCreate() {
    setEditing(null)
    setOpen(true)
  }
  function openEdit(a: Account) {
    setEditing(a)
    setOpen(true)
  }

  async function handleDelete() {
    if (!deleting) return
    try {
      await remove.mutateAsync(deleting.id)
      toast.success('Счёт удалён')
      setDeleting(null)
    } catch (e) {
      handleApiError(e)
    }
  }

  const total = data?.reduce((acc, a) => acc + Number(a.balance ?? a.initial_balance ?? 0), 0) ?? 0

  return (
    <>
      <div className="row-between">
        <div>
          <div className="muted">Всего счетов: {data?.length ?? 0}</div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 4 }} className="mono">
            {formatMoney(total)}
          </div>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          <Plus size={16} /> Новый счёт
        </button>
      </div>

      {isLoading ? (
        <div className="card"><div className="muted">Загрузка…</div></div>
      ) : !data || data.length === 0 ? (
        <div className="card">
          <EmptyState
            title="Пока нет счетов"
            description="Создайте первый счёт, чтобы начать учёт"
            action={<button className="btn btn-primary" onClick={openCreate}><Plus size={16} /> Создать счёт</button>}
            icon={<Wallet size={36} />}
          />
        </div>
      ) : (
        <div className="grid-3">
          {data.map((a) => {
            const Icon = TYPE_ICONS[a.type]
            const balance = a.balance ?? a.initial_balance
            return (
              <div key={a.id} className="card" style={{ position: 'relative' }}>
                <div className="row-between">
                  <div className="row" style={{ gap: 12 }}>
                    <div
                      style={{
                        width: 44, height: 44, borderRadius: 12,
                        background: 'linear-gradient(135deg, rgba(124,92,255,0.25), rgba(56,189,248,0.25))',
                        display: 'grid', placeItems: 'center',
                      }}
                    >
                      <Icon size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600 }}>{a.name}</div>
                      <div className="dim">{TYPE_LABELS[a.type]}</div>
                    </div>
                  </div>
                  <div className="row" style={{ gap: 4 }}>
                    <button className="btn btn-ghost btn-icon btn-sm" onClick={() => openEdit(a)} aria-label="Редактировать">
                      <Pencil size={14} />
                    </button>
                    <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setDeleting(a)} aria-label="Удалить">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <div style={{ marginTop: 18 }}>
                  <div className="dim">Текущий баланс</div>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 600, marginTop: 4 }}>
                    {formatMoney(balance)}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <AccountFormModal
        open={open}
        onClose={() => setOpen(false)}
        editing={editing}
        onSubmit={async (values) => {
          try {
            if (editing) {
              await update.mutateAsync({
                id: editing.id,
                data: { name: values.name, type: values.type },
              })
              toast.success('Счёт обновлён')
            } else {
              await create.mutateAsync({
                name: values.name,
                type: values.type,
                initial_balance: values.initial_balance,
              })
              toast.success('Счёт создан')
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
        title="Удалить счёт?"
        description={`«${deleting?.name}» будет удалён. Транзакции по нему останутся.`}
        confirmText="Удалить"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
        loading={remove.isPending}
      />
    </>
  )
}

function AccountFormModal({
  open, onClose, editing, onSubmit, submitting,
}: {
  open: boolean
  onClose: () => void
  editing: Account | null
  onSubmit: (values: FormValues) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: editing
      ? { name: editing.name, type: editing.type, initial_balance: editing.initial_balance }
      : { name: '', type: 'debit', initial_balance: '0' },
  })

  return (
    <Modal
      open={open}
      onClose={() => { onClose(); reset() }}
      title={editing ? 'Редактировать счёт' : 'Новый счёт'}
      subtitle={editing ? 'Обновите название или тип' : 'Введите начальный баланс — он не изменится после'}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Название</label>
          <input className="input" placeholder="Например, Тинькофф Black" {...register('name')} />
          {errors.name && <span className="field-error">{errors.name.message}</span>}
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Тип</label>
          <select className="select" {...register('type')}>
            <option value="debit">Дебетовый</option>
            <option value="credit">Кредитный</option>
            <option value="cash">Наличные</option>
            <option value="savings">Сберегательный</option>
          </select>
        </div>
        {!editing && (
          <div className="field" style={{ marginTop: 12 }}>
            <label>Начальный баланс</label>
            <input className="input mono" type="number" step="0.01" min="0" {...register('initial_balance')} />
            {errors.initial_balance && <span className="field-error">{errors.initial_balance.message}</span>}
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
