import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { tokenStorage } from './tokenStorage'
import type { ApiError, ApiResponse, TokenResponse } from './types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api/v1'

export class ApiException extends Error {
  code: string
  details?: Record<string, unknown> | null
  status: number

  constructor(message: string, code: string, status: number, details?: Record<string, unknown> | null) {
    super(message)
    this.code = code
    this.status = status
    this.details = details
  }
}

let isRefreshing = false
let pending: Array<(token: string | null) => void> = []
let onAuthLost: (() => void) | null = null

export function setOnAuthLost(handler: (() => void) | null) {
  onAuthLost = handler
}

const rawClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess()
  if (token) {
    cfg.headers.set('Authorization', `Bearer ${token}`)
  }
  return cfg
})

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStorage.getRefresh()
  if (!refresh) return null
  try {
    const res = await rawClient.post<ApiResponse<TokenResponse>>('/auth/refresh', {
      refresh_token: refresh,
    })
    const data = res.data.data
    if (!data) return null
    tokenStorage.setTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    return null
  }
}

client.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiError>) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const status = error.response?.status ?? 0

    if (status === 401 && original && !original._retry && !original.url?.includes('/auth/')) {
      original._retry = true

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pending.push((token) => {
            if (token) {
              original.headers.set('Authorization', `Bearer ${token}`)
              resolve(client.request(original))
            } else {
              reject(error)
            }
          })
        })
      }

      isRefreshing = true
      const newToken = await refreshAccessToken()
      isRefreshing = false
      pending.forEach((cb) => cb(newToken))
      pending = []

      if (newToken) {
        original.headers.set('Authorization', `Bearer ${newToken}`)
        return client.request(original)
      }

      tokenStorage.clear()
      onAuthLost?.()
      return Promise.reject(error)
    }

    const payload = error.response?.data
    if (payload && 'error' in payload) {
      const err = payload.error
      return Promise.reject(new ApiException(err.message, err.code, status, err.details ?? null))
    }
    return Promise.reject(
      new ApiException(error.message || 'Network error', 'NETWORK_ERROR', status),
    )
  },
)

async function unwrap<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const res = await promise
  if (!res.data.success) {
    throw new ApiException(res.data.message || 'Request failed', 'UNKNOWN', 0)
  }
  return res.data.data as T
}

export const api = {
  get<T>(url: string, params?: Record<string, unknown>, headers?: Record<string, string>) {
    return unwrap<T>(client.get(url, { params, headers }))
  },
  post<T>(url: string, body?: unknown, headers?: Record<string, string>) {
    return unwrap<T>(client.post(url, body, { headers }))
  },
  patch<T>(url: string, body?: unknown) {
    return unwrap<T>(client.patch(url, body))
  },
  put<T>(url: string, body?: unknown) {
    return unwrap<T>(client.put(url, body))
  },
  delete<T>(url: string) {
    return unwrap<T>(client.delete(url))
  },
  raw: client,
}

export async function loginRaw(email: string, password: string) {
  const res = await rawClient.post<ApiResponse<TokenResponse>>('/auth/login', { email, password })
  if (!res.data.success || !res.data.data) {
    throw new ApiException('Invalid credentials', 'AUTH_FAILED', 401)
  }
  return res.data.data
}

export async function registerRaw(email: string, password: string) {
  const res = await rawClient.post<ApiResponse<unknown>>('/auth/register', { email, password })
  if (!res.data.success) {
    throw new ApiException(res.data.message || 'Registration failed', 'REGISTRATION_FAILED', 0)
  }
}

export async function logoutRaw(refreshToken: string) {
  try {
    await rawClient.post('/auth/logout', { refresh_token: refreshToken })
  } catch {
    /* ignore */
  }
}

rawClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError<ApiError>) => {
    const status = error.response?.status ?? 0
    const payload = error.response?.data
    if (payload && 'error' in payload) {
      return Promise.reject(
        new ApiException(payload.error.message, payload.error.code, status, payload.error.details ?? null),
      )
    }
    return Promise.reject(new ApiException(error.message || 'Network error', 'NETWORK_ERROR', status))
  },
)
