import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  ArrowDownRight,
  ArrowLeftRight,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Filter,
  Pencil,
  Plus,
  Receipt,
  RotateCcw,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import {
  useAccounts,
  useCards,
  useCategories,
  useCorrectTransaction,
  useCreateTransaction,
  useDeleteTransaction,
  useTags,
  useTransactions,
  useUpdateTransaction,
} from '@/hooks/useQueries'
import type {
  Transaction,
  TransactionCreate,
  TransactionType,
} from '@/lib/types'
import { Modal } from '@/components/Modal'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { formatDate, formatMoney, todayIso } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

const createSchema = z.object({
  account_id: z.string().min(1, 'Выберите счёт'),
  category_id: z.string(),
  type: z.enum(['expense', 'income', 'transfer']),
  amount: z.string().refine((v) => Number(v) > 0, 'Сумма должна быть > 0'),
  description: z.string().max(500),
  merchant_name: z.string().max(255),
  transaction_date: z.string().min(1),
  notes: z.string(),
  tag_ids: z.array(z.string()),
  target_account_id: z.string(),
  card_id: z.string(),
})
type CreateForm = z.infer<typeof createSchema>

export function TransactionsPage() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{
    type?: TransactionType
    account_id?: string
    category_id?: string
    tag_id?: string
    date_from?: string
    date_to?: string
    search?: string
  }>({})
  const [search, setSearch] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<Transaction | null>(null)
  const [correcting, setCorrecting] = useState<Transaction | null>(null)
  const [deleting, setDeleting] = useState<Transaction | null>(null)

  const queryFilters = useMemo(
    () => ({ ...filters, search: search || undefined, page, page_size: 20 }),
    [filters, search, page],
  )

  const transactions = useTransactions(queryFilters)
  const accounts = useAccounts()
  const categories = useCategories()
  const tags = useTags()

  const create = useCreateTransaction()
  const update = useUpdateTransaction()
  const correct = useCorrectTransaction()
  const remove = useDeleteTransaction()

  const accountMap = useMemo(
    () => Object.fromEntries((accounts.data ?? []).map((a) => [a.id, a])),
    [accounts.data],
  )
  const categoryMap = useMemo(
    () => Object.fromEntries((categories.data ?? []).map((c) => [c.id, c])),
    [categories.data],
  )
  const tagMap = useMemo(
    () => Object.fromEntries((tags.data ?? []).map((t) => [t.id, t])),
    [tags.data],
  )

  async function handleDelete() {
    if (!deleting) return
    try {
      await remove.mutateAsync(deleting.id)
      toast.success('Транзакция удалена')
      setDeleting(null)
    } catch (e) {
      handleApiError(e)
    }
  }

  function resetFilters() {
    setFilters({})
    setSearch('')
    setPage(1)
  }

  const items = transactions.data?.items ?? []
  const total = transactions.data?.total ?? 0
  const pages = transactions.data?.pages ?? 1

  return (
    <>
      <div className="row" style={{ gap: 10, flexWrap: 'wrap', justifyContent: 'space-between' }}>
        <div className="row" style={{ gap: 10, flexWrap: 'wrap', flex: 1, minWidth: 0 }}>
          <div className="row" style={{ background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 12, padding: '4px 12px', gap: 8, flex: 1, minWidth: 200, maxWidth: 360 }}>
            <Search size={14} className="muted" />
            <input
              className="input"
              placeholder="Поиск по описанию / магазину"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              style={{ border: 'none', background: 'transparent', padding: '6px 0', flex: 1, minWidth: 0 }}
            />
          </div>
          <button className="btn btn-secondary" onClick={() => setShowFilters((v) => !v)}>
            <Filter size={16} /> Фильтры
          </button>
          {(Object.keys(filters).length > 0 || search) && (
            <button className="btn btn-ghost btn-sm" onClick={resetFilters}>
              <X size={14} /> Сбросить
            </button>
          )}
        </div>
        <button className="btn btn-primary" onClick={() => { setCreateOpen(true) }}>
          <Plus size={16} /> Новая операция
        </button>
      </div>

      {showFilters && (
        <div className="card">
          <div className="form-row" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            <div className="field">
              <label>Тип</label>
              <select
                className="select"
                value={filters.type ?? ''}
                onChange={(e) => { setFilters({ ...filters, type: (e.target.value || undefined) as TransactionType | undefined }); setPage(1) }}
              >
                <option value="">Все</option>
                <option value="expense">Расход</option>
                <option value="income">Доход</option>
                <option value="transfer">Перевод</option>
              </select>
            </div>
            <div className="field">
              <label>Счёт</label>
              <select
                className="select"
                value={filters.account_id ?? ''}
                onChange={(e) => { setFilters({ ...filters, account_id: e.target.value || undefined }); setPage(1) }}
              >
                <option value="">Все</option>
                {(accounts.data ?? []).map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Категория</label>
              <select
                className="select"
                value={filters.category_id ?? ''}
                onChange={(e) => { setFilters({ ...filters, category_id: e.target.value || undefined }); setPage(1) }}
              >
                <option value="">Все</option>
                {(categories.data ?? []).map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Тег</label>
              <select
                className="select"
                value={filters.tag_id ?? ''}
                onChange={(e) => { setFilters({ ...filters, tag_id: e.target.value || undefined }); setPage(1) }}
              >
                <option value="">Все</option>
                {(tags.data ?? []).map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Дата от</label>
              <input
                className="input"
                type="date"
                value={filters.date_from ?? ''}
                onChange={(e) => { setFilters({ ...filters, date_from: e.target.value || undefined }); setPage(1) }}
              />
            </div>
            <div className="field">
              <label>Дата до</label>
              <input
                className="input"
                type="date"
                value={filters.date_to ?? ''}
                onChange={(e) => { setFilters({ ...filters, date_to: e.target.value || undefined }); setPage(1) }}
              />
            </div>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {transactions.isLoading ? (
          <div className="muted" style={{ padding: 20 }}>Загрузка…</div>
        ) : items.length === 0 ? (
          <EmptyState
            title="Пока нет операций"
            description="Добавьте первую транзакцию"
            icon={<Receipt size={36} />}
            action={<button className="btn btn-primary" onClick={() => setCreateOpen(true)}><Plus size={16} /> Добавить</button>}
          />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Тип</th>
                  <th>Описание</th>
                  <th>Категория</th>
                  <th>Счёт</th>
                  <th>Теги</th>
                  <th style={{ textAlign: 'right' }}>Сумма</th>
                  <th style={{ textAlign: 'right' }}>Кэшбэк</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((t) => {
                  const acc = accountMap[t.account_id]
                  const cat = t.category_id ? categoryMap[t.category_id] : null
                  return (
                    <tr key={t.id}>
                      <td className="mono">{formatDate(t.transaction_date)}</td>
                      <td>{renderTypeBadge(t.type)}</td>
                      <td>
                        <div>{t.description || <span className="dim">—</span>}</div>
                        {t.merchant_name && <div className="dim">{t.merchant_name}</div>}
                        {t.correction_of_id && <span className="badge badge-warning" style={{ marginTop: 4 }}>Исправление</span>}
                      </td>
                      <td>
                        {cat ? (
                          <span className="row" style={{ gap: 6 }}>
                            {cat.color && <span className="color-swatch" style={{ background: cat.color, margin: 0 }} />}
                            {cat.name}
                          </span>
                        ) : (
                          <span className="dim">—</span>
                        )}
                      </td>
                      <td>{acc?.name ?? <span className="dim">—</span>}</td>
                      <td>
                        {t.tag_ids.length === 0 ? (
                          <span className="dim">—</span>
                        ) : (
                          <div className="row" style={{ gap: 4, flexWrap: 'wrap' }}>
                            {t.tag_ids.map((id) => {
                              const tag = tagMap[id]
                              return (
                                <span key={id} className="badge badge-muted">
                                  {tag?.color && <span className="color-swatch" style={{ background: tag.color, margin: 0, width: 8, height: 8 }} />}
                                  {tag?.name ?? id.slice(0, 6)}
                                </span>
                              )
                            })}
                          </div>
                        )}
                      </td>
                      <td className="mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                        <span className={t.type === 'income' ? 'value-positive' : t.type === 'expense' ? 'value-negative' : ''}>
                          {t.type === 'expense' ? '−' : t.type === 'income' ? '+' : ''}
                          {formatMoney(t.amount)}
                        </span>
                      </td>
                      <td className="mono" style={{ textAlign: 'right' }}>
                        {t.type === 'expense' && t.cashback_amount && Number(t.cashback_amount) > 0 ? (
                          <span className="value-positive">+{formatMoney(t.cashback_amount)}</span>
                        ) : (
                          <span className="dim">—</span>
                        )}
                      </td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setEditing(t)} title="Редактировать">
                            <Pencil size={14} />
                          </button>
                          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setCorrecting(t)} title="Исправление">
                            <RotateCcw size={14} />
                          </button>
                          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setDeleting(t)} title="Удалить">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {items.length > 0 && (
        <div className="row-between">
          <span className="muted">Всего: {total}</span>
          <div className="row" style={{ gap: 6 }}>
            <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft size={14} />
            </button>
            <span className="muted" style={{ minWidth: 80, textAlign: 'center' }}>
              {page} / {pages}
            </span>
            <button className="btn btn-ghost btn-sm" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

      {createOpen && <TransactionCreateModal
        onClose={() => setCreateOpen(false)}
        onSubmit={async (values) => {
          try {
            const payload: TransactionCreate = {
              account_id: values.account_id,
              type: values.type,
              amount: values.amount,
              transaction_date: values.transaction_date,
              category_id: values.category_id || null,
              description: values.description || null,
              merchant_name: values.merchant_name || null,
              notes: values.notes || null,
              tag_ids: values.tag_ids ?? [],
              target_account_id: values.type === 'transfer' ? (values.target_account_id || null) : null,
              card_id: values.type === 'expense' ? (values.card_id || null) : null,
            }
            await create.mutateAsync(payload)
            toast.success('Операция создана')
            setCreateOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={create.isPending}
      />}

      <TransactionEditModal
        open={!!editing}
        onClose={() => setEditing(null)}
        transaction={editing}
        onSubmit={async (data) => {
          if (!editing) return
          try {
            await update.mutateAsync({ id: editing.id, data })
            toast.success('Сохранено')
            setEditing(null)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={update.isPending}
      />

      {correcting && <CorrectionModal
        onClose={() => setCorrecting(null)}
        transaction={correcting}
        onSubmit={async (data) => {
          if (!correcting) return
          try {
            await correct.mutateAsync({ id: correcting.id, data })
            toast.success('Исправление создано')
            setCorrecting(null)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={correct.isPending}
      />}

      <ConfirmDialog
        open={!!deleting}
        title="Удалить транзакцию?"
        description="Эта операция будет помечена как удалённая."
        confirmText="Удалить"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
        loading={remove.isPending}
      />
    </>
  )
}

function renderTypeBadge(type: TransactionType) {
  if (type === 'income') return <span className="badge badge-success"><ArrowUpRight size={11} /> Доход</span>
  if (type === 'expense') return <span className="badge badge-danger"><ArrowDownRight size={11} /> Расход</span>
  return <span className="badge badge-info"><ArrowLeftRight size={11} /> Перевод</span>
}

function TransactionCreateModal({
  onClose, onSubmit, submitting,
}: {
  onClose: () => void
  onSubmit: (values: CreateForm) => void
  submitting: boolean
}) {
  const accounts = useAccounts()
  const categories = useCategories()
  const tags = useTags()
  const cards = useCards()

  const {
    register, handleSubmit, formState: { errors }, watch, setValue, reset,
  } = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      account_id: '',
      category_id: '',
      type: 'expense',
      amount: '',
      description: '',
      merchant_name: '',
      transaction_date: todayIso(),
      notes: '',
      tag_ids: [],
      target_account_id: '',
      card_id: '',
    },
  })

  const type = watch('type')
  const accountId = watch('account_id')
  const selectedTags = watch('tag_ids') ?? []

  const filteredCategories = useMemo(() => {
    if (type === 'transfer') return []
    return (categories.data ?? []).filter((c) => c.type === (type === 'income' ? 'income' : 'expense'))
  }, [categories.data, type])

  const cardsForAccount = useMemo(
    () => (cards.data ?? []).filter((c) => c.account_id === accountId),
    [cards.data, accountId],
  )

  function toggleTag(tagId: string) {
    const next = selectedTags.includes(tagId)
      ? selectedTags.filter((id) => id !== tagId)
      : [...selectedTags, tagId]
    setValue('tag_ids', next, { shouldDirty: true })
  }

  return (
    <Modal
      open
      onClose={() => { onClose(); reset() }}
      title="Новая операция"
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="row" style={{ background: 'rgba(11,16,32,0.4)', border: '1px solid var(--border)', borderRadius: 10, padding: 4, marginBottom: 16 }}>
          {(['expense', 'income', 'transfer'] as TransactionType[]).map((t) => (
            <button
              key={t}
              type="button"
              className={`btn btn-sm ${type === t ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setValue('type', t)}
              style={{ flex: 1 }}
            >
              {t === 'expense' ? 'Расход' : t === 'income' ? 'Доход' : 'Перевод'}
            </button>
          ))}
        </div>

        <div className="form-row form-row-2">
          <div className="field">
            <label>Сумма</label>
            <input className="input mono" type="number" step="0.01" min="0.01" {...register('amount')} />
            {errors.amount && <span className="field-error">{errors.amount.message}</span>}
          </div>
          <div className="field">
            <label>Дата</label>
            <input className="input" type="date" {...register('transaction_date')} />
          </div>
        </div>

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>{type === 'transfer' ? 'Счёт списания' : 'Счёт'}</label>
            <select className="select" {...register('account_id')}>
              <option value="">Выберите счёт</option>
              {(accounts.data ?? []).map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
            {errors.account_id && <span className="field-error">{errors.account_id.message}</span>}
          </div>
          {type === 'transfer' ? (
            <div className="field">
              <label>Счёт зачисления</label>
              <select className="select" {...register('target_account_id')}>
                <option value="">Выберите счёт</option>
                {(accounts.data ?? []).filter((a) => a.id !== accountId).map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
          ) : (
            <div className="field">
              <label>Категория</label>
              <select className="select" {...register('category_id')}>
                <option value="">Без категории</option>
                {filteredCategories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Описание</label>
            <input className="input" {...register('description')} />
          </div>
          <div className="field">
            <label>Магазин / получатель</label>
            <input className="input" {...register('merchant_name')} />
          </div>
        </div>

        {type === 'expense' && cardsForAccount.length > 0 && (
          <div className="field" style={{ marginTop: 12 }}>
            <label>Карта (для расчёта кэшбэка)</label>
            <select className="select" {...register('card_id')}>
              <option value="">Без карты</option>
              {cardsForAccount.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        )}

        {(tags.data ?? []).length > 0 && (
          <div className="field" style={{ marginTop: 12 }}>
            <label>Теги</label>
            <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
              {(tags.data ?? []).map((t) => {
                const active = selectedTags.includes(t.id)
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => toggleTag(t.id)}
                    className="pill"
                    style={{
                      cursor: 'pointer',
                      background: active ? 'var(--primary-soft)' : undefined,
                      borderColor: active ? 'rgba(124,92,255,0.4)' : undefined,
                      color: active ? '#fff' : undefined,
                    }}
                  >
                    {t.color && <span className="color-swatch" style={{ background: t.color, margin: 0, marginRight: 6 }} />}
                    {t.name}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        <div className="field" style={{ marginTop: 12 }}>
          <label>Заметки</label>
          <textarea className="textarea" {...register('notes')} />
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

const editSchema = z.object({
  description: z.string().optional(),
  merchant_name: z.string().optional(),
  notes: z.string().optional(),
  tag_ids: z.array(z.string()).optional(),
})
type EditForm = z.infer<typeof editSchema>

function TransactionEditModal({
  open, onClose, transaction, onSubmit, submitting,
}: {
  open: boolean
  onClose: () => void
  transaction: Transaction | null
  onSubmit: (data: EditForm) => void
  submitting: boolean
}) {
  const tags = useTags()
  const {
    register, handleSubmit, watch, setValue, reset,
  } = useForm<EditForm>({
    resolver: zodResolver(editSchema),
    values: transaction
      ? {
          description: transaction.description ?? '',
          merchant_name: transaction.merchant_name ?? '',
          notes: transaction.notes ?? '',
          tag_ids: transaction.tag_ids,
        }
      : { description: '', merchant_name: '', notes: '', tag_ids: [] },
  })

  const selected = watch('tag_ids') ?? []

  function toggle(id: string) {
    const next = selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]
    setValue('tag_ids', next, { shouldDirty: true })
  }

  return (
    <Modal open={open} onClose={() => { onClose(); reset() }} title="Редактировать операцию"
      subtitle="Сумму и счёт можно изменить только через «Исправление»"
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Описание</label>
          <input className="input" {...register('description')} />
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Магазин / получатель</label>
          <input className="input" {...register('merchant_name')} />
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Заметки</label>
          <textarea className="textarea" {...register('notes')} />
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Теги</label>
          <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
            {(tags.data ?? []).map((t) => {
              const active = selected.includes(t.id)
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => toggle(t.id)}
                  className="pill"
                  style={{
                    cursor: 'pointer',
                    background: active ? 'var(--primary-soft)' : undefined,
                    borderColor: active ? 'rgba(124,92,255,0.4)' : undefined,
                  }}
                >
                  {t.color && <span className="color-swatch" style={{ background: t.color, margin: 0, marginRight: 6 }} />}
                  {t.name}
                </button>
              )
            })}
          </div>
        </div>
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

const correctSchema = z.object({
  reason: z.string().min(1, 'Укажите причину').max(500),
  new_amount: z.string().optional(),
  new_account_id: z.string().optional(),
  new_category_id: z.string().optional(),
})
type CorrectForm = z.infer<typeof correctSchema>

function CorrectionModal({
  onClose, transaction, onSubmit, submitting,
}: {
  onClose: () => void
  transaction: Transaction
  onSubmit: (data: { reason: string; new_amount?: string; new_account_id?: string; new_category_id?: string }) => void
  submitting: boolean
}) {
  const accounts = useAccounts()
  const categories = useCategories()
  const {
    register, handleSubmit, formState: { errors }, reset,
  } = useForm<CorrectForm>({
    resolver: zodResolver(correctSchema),
    defaultValues: { reason: '', new_amount: '', new_account_id: '', new_category_id: '' },
  })

  return (
    <Modal open onClose={() => { onClose(); reset() }} title="Исправление операции"
      subtitle="Старая операция будет помечена удалённой, появится новая со ссылкой на оригинал."
    >
      <form onSubmit={handleSubmit((v) => onSubmit({
        reason: v.reason,
        new_amount: v.new_amount || undefined,
        new_account_id: v.new_account_id || undefined,
        new_category_id: v.new_category_id || undefined,
      }))}>
        <div className="field">
          <label>Причина</label>
          <input className="input" {...register('reason')} />
          {errors.reason && <span className="field-error">{errors.reason.message}</span>}
        </div>
        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Новая сумма (опционально)</label>
            <input className="input mono" type="number" step="0.01" min="0.01" {...register('new_amount')} />
          </div>
          <div className="field">
            <label>Новый счёт</label>
            <select className="select" {...register('new_account_id')}>
              <option value="">Не менять</option>
              {(accounts.data ?? []).map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Новая категория</label>
          <select className="select" {...register('new_category_id')}>
            <option value="">Не менять</option>
            {(categories.data ?? []).filter((c) => c.type === (transaction.type === 'income' ? 'income' : 'expense')).map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '…' : 'Создать исправление'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
