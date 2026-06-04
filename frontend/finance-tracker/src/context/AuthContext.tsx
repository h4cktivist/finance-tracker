import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { loginRaw, logoutRaw, registerRaw, setOnAuthLost } from '@/lib/api'
import { tokenStorage } from '@/lib/tokenStorage'
import type { User } from '@/lib/types'

type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  isInitializing: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function decodeUserFromToken(token: string): User | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1])) as Record<string, unknown>
    const sub = String(payload.sub ?? '')
    const email = String(payload.email ?? payload.sub ?? '')
    if (!sub) return null
    return {
      id: sub,
      email,
      is_active: true,
      is_verified: Boolean(payload.is_verified ?? true),
    }
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser())
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const token = tokenStorage.getAccess()
    if (token && !user) {
      const decoded = decodeUserFromToken(token)
      if (decoded) {
        setUser(decoded)
        tokenStorage.setUser(decoded)
      }
    }
    setIsInitializing(false)
  }, [user])

  useEffect(() => {
    setOnAuthLost(() => {
      tokenStorage.clear()
      setUser(null)
    })
    return () => setOnAuthLost(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginRaw(email, password)
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    const decoded = decodeUserFromToken(tokens.access_token) ?? {
      id: 'me',
      email,
      is_active: true,
      is_verified: true,
    }
    decoded.email = email
    setUser(decoded)
    tokenStorage.setUser(decoded)
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await registerRaw(email, password)
  }, [])

  const logout = useCallback(async () => {
    const refresh = tokenStorage.getRefresh()
    if (refresh) await logoutRaw(refresh)
    tokenStorage.clear()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      isInitializing,
      login,
      register,
      logout,
    }),
    [user, isInitializing, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
