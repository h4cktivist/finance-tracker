import { toast } from 'sonner'
import { ApiException } from './api'

export function handleApiError(e: unknown, fallback = 'Что-то пошло не так') {
  const msg = e instanceof ApiException ? e.message : (e as Error)?.message || fallback
  toast.error(msg)
}
