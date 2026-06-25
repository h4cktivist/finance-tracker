import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useQueryClient } from '@tanstack/react-query'
import { Eye, EyeOff, ShieldCheck, Trash2 } from 'lucide-react'
import { brokerSettings } from '@/lib/brokerSettings'

const schema = z.object({
  token: z.string().min(1, 'Введите токен'),
  accountId: z.string().min(1, 'Введите номер счёта'),
})
type FormValues = z.infer<typeof schema>

export function SettingsPage() {
  const qc = useQueryClient()
  const [showToken, setShowToken] = useState(false)
  const saved = brokerSettings.get()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { token: saved?.token ?? '', accountId: saved?.accountId ?? '' },
  })

  function onSubmit(values: FormValues) {
    brokerSettings.set(values.token, values.accountId)
    qc.invalidateQueries({ queryKey: ['broker'] })
    toast.success('Настройки брокерского счёта сохранены')
  }

  function onClear() {
    brokerSettings.clear()
    reset({ token: '', accountId: '' })
    qc.invalidateQueries({ queryKey: ['broker'] })
    toast.success('Настройки брокерского счёта удалены')
  }

  return (
    <section className="card" style={{ maxWidth: 520 }}>
      <div className="card-header">
        <h2>Брокерский счёт (Финам)</h2>
      </div>
      <p className="muted" style={{ marginBottom: 16 }}>
        Токен создаётся на портале <a href='https://api.finam.ru/'>Finam Trade API</a> в разделе «Токены».
      </p>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Секретный токен</label>
          <div className="row" style={{ gap: 8 }}>
            <input
              className="input mono"
              type={showToken ? 'text' : 'password'}
              placeholder="tapi_sk_..."
              autoComplete="off"
              {...register('token')}
            />
            <button
              type="button"
              className="btn btn-ghost btn-icon"
              onClick={() => setShowToken((v) => !v)}
              aria-label={showToken ? 'Скрыть токен' : 'Показать токен'}
            >
              {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.token && <span className="field-error">{errors.token.message}</span>}
        </div>

        <div className="field" style={{ marginTop: 12 }}>
          <label>Номер счёта</label>
          <input className="input mono" placeholder="2015134" {...register('accountId')} />
          {errors.accountId && <span className="field-error">{errors.accountId.message}</span>}
        </div>

        <div className="row-between" style={{ marginTop: 20 }}>
          <button type="button" className="btn btn-ghost" onClick={onClear} disabled={!saved}>
            <Trash2 size={14} /> Удалить
          </button>
          <button type="submit" className="btn btn-primary">
            <ShieldCheck size={14} /> Сохранить
          </button>
        </div>
      </form>
    </section>
  )
}
