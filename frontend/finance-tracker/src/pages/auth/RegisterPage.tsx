import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/context/AuthContext'
import { ApiException } from '@/lib/api'
import { toast } from 'sonner'

const schema = z
  .object({
    email: z.string().email('Некорректный email'),
    password: z.string().min(8, 'Минимум 8 символов').max(128),
    confirm: z.string(),
  })
  .refine((v) => v.password === v.confirm, {
    path: ['confirm'],
    message: 'Пароли не совпадают',
  })

type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const { register: signUp, login } = useAuth()
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormValues) {
    setSubmitting(true)
    try {
      await signUp(values.email, values.password)
      await login(values.email, values.password)
      toast.success('Аккаунт создан')
      navigate('/', { replace: true })
    } catch (e) {
      const msg = e instanceof ApiException ? e.message : 'Не удалось создать аккаунт'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>Создать аккаунт</h1>
      <p className="subtitle">Начните контролировать свои финансы</p>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Email</label>
          <input className="input" type="email" autoComplete="email" placeholder="you@example.com" {...register('email')} />
          {errors.email && <span className="field-error">{errors.email.message}</span>}
        </div>
        <div className="field">
          <label>Пароль</label>
          <input
            className="input"
            type="password"
            autoComplete="new-password"
            placeholder="Минимум 8 символов"
            {...register('password')}
          />
          {errors.password && <span className="field-error">{errors.password.message}</span>}
        </div>
        <div className="field">
          <label>Повторите пароль</label>
          <input
            className="input"
            type="password"
            autoComplete="new-password"
            {...register('confirm')}
          />
          {errors.confirm && <span className="field-error">{errors.confirm.message}</span>}
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Создаём…' : 'Зарегистрироваться'}
        </button>
      </form>
      <div className="switch">
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </div>
    </>
  )
}
