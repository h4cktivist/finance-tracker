import { useMemo, useState } from 'react'
import { CreditCard, Plus, Sparkles, TrendingDown, TrendingUp } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useAccounts,
  useCardRules,
  useCards,
  useCashbackRecommendations,
  useCashbackSummary,
  useCategories,
  useCreateCard,
  useCreateCashbackRule,
  useMissedCashback,
} from '@/hooks/useQueries'
import { Modal } from '@/components/Modal'
import { EmptyState } from '@/components/EmptyState'
import { formatDate, formatMoney, todayIso } from '@/lib/format'
import { handleApiError } from '@/lib/errors'

export function CashbackPage() {
  const [createCardOpen, setCreateCardOpen] = useState(false)
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null)
  const [ruleModalOpen, setRuleModalOpen] = useState(false)
  const [recCategory, setRecCategory] = useState<string>('')

  const cards = useCards()
  const accounts = useAccounts()
  const categories = useCategories()
  const summary = useCashbackSummary()
  const missed = useMissedCashback()
  const recs = useCashbackRecommendations(recCategory || undefined)
  const rules = useCardRules(selectedCardId ?? undefined)

  const expenseCategories = useMemo(
    () => (categories.data ?? []).filter((c) => c.type === 'expense'),
    [categories.data],
  )
  const accountMap = Object.fromEntries((accounts.data ?? []).map((a) => [a.id, a]))
  const categoryMap = Object.fromEntries((categories.data ?? []).map((c) => [c.id, c]))

  const createCard = useCreateCard()
  const createRule = useCreateCashbackRule(selectedCardId ?? '')

  return (
    <>
      <section className="kpi-grid">
        <div className="kpi">
          <span className="label"><Sparkles size={14} /> Накопленный кэшбэк</span>
          <span className="value mono value-positive">{formatMoney(summary.data?.total_earned ?? 0)}</span>
          <span className="hint">за всё время</span>
        </div>
        <div className="kpi">
          <span className="label"><CreditCard size={14} /> Карт</span>
          <span className="value mono">{cards.data?.length ?? 0}</span>
        </div>
        <div className="kpi">
          <span className="label"><TrendingDown size={14} /> Упущено</span>
          <span className="value mono">{missed.data?.length ?? 0} операций</span>
          <span className="hint">кэшбэк недоступен</span>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>Карты</h2>
          <button className="btn btn-primary btn-sm" onClick={() => setCreateCardOpen(true)}>
            <Plus size={14} /> Добавить карту
          </button>
        </div>
        {!cards.data || cards.data.length === 0 ? (
          <EmptyState
            title="Пока нет карт"
            description="Добавьте карту, чтобы настроить правила кэшбэка"
            icon={<CreditCard size={36} />}
          />
        ) : (
          <div className="grid-3">
            {cards.data.map((c) => (
              <div
                key={c.id}
                className="card"
                style={{
                  cursor: 'pointer',
                  border: selectedCardId === c.id ? '1px solid rgba(124,92,255,0.55)' : '1px solid var(--border)',
                  background: selectedCardId === c.id ? 'rgba(124,92,255,0.08)' : 'var(--panel)',
                }}
                onClick={() => setSelectedCardId(c.id === selectedCardId ? null : c.id)}
              >
                <div className="row" style={{ gap: 12 }}>
                  <div style={{
                    width: 50, height: 32, borderRadius: 6,
                    background: 'linear-gradient(135deg, #7c5cff, #38bdf8)',
                  }} />
                  <div>
                    <div style={{ fontWeight: 600 }}>{c.name}</div>
                    <div className="dim">
                      {c.bank_name ?? 'Карта'}{c.last_digits ? ` • •••• ${c.last_digits}` : ''}
                    </div>
                  </div>
                </div>
                <div className="dim" style={{ marginTop: 10 }}>
                  Счёт: {accountMap[c.account_id]?.name ?? '—'}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {selectedCardId && (
        <section className="card">
          <div className="card-header">
            <h2>Правила кэшбэка</h2>
            <button className="btn btn-primary btn-sm" onClick={() => setRuleModalOpen(true)}>
              <Plus size={14} /> Добавить правило
            </button>
          </div>
          {!rules.data || rules.data.length === 0 ? (
            <div className="empty">
              <p>Правил пока нет — добавьте первое</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Категория</th>
                    <th>Процент</th>
                    <th>Мин. сумма</th>
                    <th>Месячный лимит</th>
                    <th>Период</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.data.map((r) => (
                    <tr key={r.id}>
                      <td>{categoryMap[r.category_id]?.name ?? '—'}</td>
                      <td className="mono">{Number(r.cashback_percent).toFixed(2)}%</td>
                      <td className="mono">
                        {r.min_purchase_amount ? formatMoney(r.min_purchase_amount) : '—'}
                      </td>
                      <td className="mono">{r.monthly_limit ? formatMoney(r.monthly_limit) : '—'}</td>
                      <td className="mono">
                        {formatDate(r.start_date)}
                        {r.end_date && ` — ${formatDate(r.end_date)}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      <section className="grid-2">
        <div className="card">
          <div className="card-header">
            <h2>Рекомендации</h2>
            <span className="card-subtitle">Лучшая карта для категории</span>
          </div>
          <div className="field">
            <label>Категория</label>
            <select className="select" value={recCategory} onChange={(e) => setRecCategory(e.target.value)}>
              <option value="">Выберите категорию</option>
              {expenseCategories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          {recCategory && (
            recs.isLoading ? (
              <div className="muted" style={{ marginTop: 14 }}>Загрузка…</div>
            ) : !recs.data || recs.data.length === 0 ? (
              <div className="empty"><p>Подходящих карт не найдено</p></div>
            ) : (
              <div className="col" style={{ marginTop: 14 }}>
                {recs.data.map((r) => (
                  <div key={r.best_card_id} className="row-between" style={{
                    padding: 12, background: 'rgba(45,212,191,0.08)', borderRadius: 10,
                  }}>
                    <div>
                      <div style={{ fontWeight: 500 }}>{r.best_card_name}</div>
                      <div className="dim">
                      Лучшая для этой категории
                      {r.min_purchase_amount
                        ? ` · от ${formatMoney(r.min_purchase_amount)}`
                        : ''}
                    </div>
                    </div>
                    <div className="badge badge-success">
                      <TrendingUp size={12} /> {Number(r.cashback_percent).toFixed(2)}%
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Упущенный кэшбэк</h2>
            <span className="card-subtitle">Где можно было получить больше</span>
          </div>
          {!missed.data || missed.data.length === 0 ? (
            <EmptyState title="Всё под контролем" description="Упущенных начислений не обнаружено" />
          ) : (
            <div className="col">
              {missed.data.slice(0, 6).map((m) => (
                <div key={m.id} className="row-between" style={{
                  padding: 10, background: 'rgba(239,71,97,0.06)', borderRadius: 10,
                }}>
                  <div>
                    <div style={{ fontWeight: 500 }}>{m.period_month}</div>
                    <div className="dim">Операция #{m.transaction_id.slice(0, 8)}</div>
                  </div>
                  <span className="badge badge-danger">−{formatMoney(m.amount)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {createCardOpen && <CreateCardModal
        onClose={() => setCreateCardOpen(false)}
        accounts={accounts.data ?? []}
        onSubmit={async (v) => {
          try {
            await createCard.mutateAsync(v)
            toast.success('Карта добавлена')
            setCreateCardOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={createCard.isPending}
      />}

      {ruleModalOpen && selectedCardId && <CreateRuleModal
        onClose={() => setRuleModalOpen(false)}
        categories={expenseCategories}
        onSubmit={async (v) => {
          try {
            await createRule.mutateAsync({
              category_id: v.category_id,
              cashback_percent: v.cashback_percent,
              monthly_limit: v.monthly_limit || null,
              min_purchase_amount: v.min_purchase_amount || null,
              start_date: v.start_date,
              end_date: v.end_date || null,
            })
            toast.success('Правило добавлено')
            setRuleModalOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={createRule.isPending}
      />}
    </>
  )
}

const cardSchema = z.object({
  account_id: z.string().min(1, 'Выберите счёт'),
  name: z.string().min(1, 'Введите название'),
  bank_name: z.string().optional().or(z.literal('')),
  last_digits: z.string().max(4).optional().or(z.literal('')),
})
type CardForm = z.infer<typeof cardSchema>

function CreateCardModal({
  onClose, accounts, onSubmit, submitting,
}: {
  onClose: () => void
  accounts: Array<{ id: string; name: string }>
  onSubmit: (v: CardForm) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, reset,
  } = useForm<CardForm>({
    resolver: zodResolver(cardSchema),
    defaultValues: { account_id: '', name: '', bank_name: '', last_digits: '' },
  })

  return (
    <Modal open onClose={() => { onClose(); reset() }} title="Новая карта">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Счёт</label>
          <select className="select" {...register('account_id')}>
            <option value="">Выберите счёт</option>
            {accounts.map((a) => (<option key={a.id} value={a.id}>{a.name}</option>))}
          </select>
          {errors.account_id && <span className="field-error">{errors.account_id.message}</span>}
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Название</label>
          <input className="input" placeholder="Например, Тинькофф Black" {...register('name')} />
          {errors.name && <span className="field-error">{errors.name.message}</span>}
        </div>
        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Банк</label>
            <input className="input" {...register('bank_name')} />
          </div>
          <div className="field">
            <label>Последние 4 цифры</label>
            <input className="input mono" maxLength={4} {...register('last_digits')} />
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

const ruleSchema = z.object({
  category_id: z.string().min(1, 'Выберите категорию'),
  cashback_percent: z.string().refine((v) => {
    const n = Number(v); return n > 0 && n <= 100
  }, 'От 0 до 100'),
  monthly_limit: z.string().optional().or(z.literal('')),
  min_purchase_amount: z.string().optional().or(z.literal('')),
  start_date: z.string().min(1),
  end_date: z.string().optional().or(z.literal('')),
})
type RuleForm = z.infer<typeof ruleSchema>

function CreateRuleModal({
  onClose, categories, onSubmit, submitting,
}: {
  onClose: () => void
  categories: Array<{ id: string; name: string }>
  onSubmit: (v: RuleForm) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, reset,
  } = useForm<RuleForm>({
    resolver: zodResolver(ruleSchema),
    defaultValues: {
      category_id: '', cashback_percent: '5', monthly_limit: '', min_purchase_amount: '',
      start_date: todayIso(), end_date: '',
    },
  })

  return (
    <Modal open onClose={() => { onClose(); reset() }} title="Правило кэшбэка">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Категория</label>
          <select className="select" {...register('category_id')}>
            <option value="">Выберите категорию</option>
            {categories.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
          </select>
          {errors.category_id && <span className="field-error">{errors.category_id.message}</span>}
        </div>
        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Процент</label>
            <input className="input mono" type="number" step="0.01" min="0.01" max="100" {...register('cashback_percent')} />
            {errors.cashback_percent && <span className="field-error">{errors.cashback_percent.message}</span>}
          </div>
          <div className="field">
            <label>Месячный лимит (опц.)</label>
            <input className="input mono" type="number" step="0.01" min="0" {...register('monthly_limit')} />
          </div>
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Мин. сумма покупки для кэшбэка (опц.)</label>
          <input
            className="input mono"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="Например, 2000 — только от этой суммы"
            {...register('min_purchase_amount')}
          />
          <span className="hint" style={{ display: 'block', marginTop: 6 }}>
            Пустое поле — кэшбэк на любую сумму в категории
          </span>
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
