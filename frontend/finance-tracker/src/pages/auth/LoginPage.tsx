import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/context/AuthContext'
import { ApiException } from '@/lib/api'
import { toast } from 'sonner'

const schema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(1, 'Введите пароль'),
})

type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const { login } = useAuth()
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
      await login(values.email, values.password)
      toast.success('Добро пожаловать!')
      navigate('/', { replace: true })
    } catch (e) {
      const msg = e instanceof ApiException ? e.message : 'Не удалось войти'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>С возвращением</h1>
      <p className="subtitle">Войдите в свой аккаунт, чтобы продолжить</p>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Email</label>
          <input
            className="input"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            {...register('email')}
          />
          {errors.email && <span className="field-error">{errors.email.message}</span>}
        </div>
        <div className="field">
          <label>Пароль</label>
          <input
            className="input"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            {...register('password')}
          />
          {errors.password && <span className="field-error">{errors.password.message}</span>}
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Входим…' : 'Войти'}
        </button>
      </form>
      <div className="switch">
        Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        <div style={{ marginTop: 6 }}>
          <Link to="/reset-password">Забыли пароль?</Link>
        </div>
      </div>
    </>
  )
}
