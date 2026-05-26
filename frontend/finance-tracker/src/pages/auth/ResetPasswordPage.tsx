import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import { toast } from 'sonner'

const requestSchema = z.object({ email: z.string().email('Некорректный email') })
const resetSchema = z.object({
  email: z.string().email('Некорректный email'),
  reset_token: z.string().min(1, 'Введите токен'),
  new_password: z.string().min(8, 'Минимум 8 символов').max(128),
})

type RequestValues = z.infer<typeof requestSchema>
type ResetValues = z.infer<typeof resetSchema>

export function ResetPasswordPage() {
  const [step, setStep] = useState<'request' | 'reset'>('request')
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)

  const requestForm = useForm<RequestValues>({ resolver: zodResolver(requestSchema) })
  const resetForm = useForm<ResetValues>({ resolver: zodResolver(resetSchema) })

  async function onRequest(values: RequestValues) {
    setSubmitting(true)
    try {
      const res = await axios.post('/api/v1/auth/reset-password', { email: values.email })
      const msg = (res.data as { message?: string }).message
      toast.success(msg || 'Если email зарегистрирован, токен отправлен')
      resetForm.setValue('email', values.email)
      setStep('reset')
    } catch (e) {
      const msg =
        (axios.isAxiosError(e) && e.response?.data?.error?.message) ||
        'Не удалось отправить запрос'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  async function onReset(values: ResetValues) {
    setSubmitting(true)
    try {
      await axios.post('/api/v1/auth/reset-password', values)
      toast.success('Пароль обновлён')
      navigate('/login', { replace: true })
    } catch (e) {
      const msg =
        (axios.isAxiosError(e) && e.response?.data?.error?.message) ||
        'Не удалось сменить пароль'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>Сброс пароля</h1>
      <p className="subtitle">
        {step === 'request'
          ? 'Введите email — мы вышлем токен для смены пароля'
          : 'Введите токен и новый пароль'}
      </p>

      {step === 'request' ? (
        <form onSubmit={requestForm.handleSubmit(onRequest)}>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" {...requestForm.register('email')} />
            {requestForm.formState.errors.email && (
              <span className="field-error">{requestForm.formState.errors.email.message}</span>
            )}
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Отправляем…' : 'Получить токен'}
          </button>
        </form>
      ) : (
        <form onSubmit={resetForm.handleSubmit(onReset)}>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" {...resetForm.register('email')} />
            {resetForm.formState.errors.email && (
              <span className="field-error">{resetForm.formState.errors.email.message}</span>
            )}
          </div>
          <div className="field">
            <label>Токен сброса</label>
            <input className="input" type="text" {...resetForm.register('reset_token')} />
            {resetForm.formState.errors.reset_token && (
              <span className="field-error">{resetForm.formState.errors.reset_token.message}</span>
            )}
          </div>
          <div className="field">
            <label>Новый пароль</label>
            <input className="input" type="password" {...resetForm.register('new_password')} />
            {resetForm.formState.errors.new_password && (
              <span className="field-error">{resetForm.formState.errors.new_password.message}</span>
            )}
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Сохраняем…' : 'Сменить пароль'}
          </button>
        </form>
      )}

      <div className="switch">
        <Link to="/login">← Назад ко входу</Link>
      </div>
    </>
  )
}
