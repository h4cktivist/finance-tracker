import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

const STORAGE_KEY = 'exclude_investments_from_stats'

type AnalyticsPreferencesContextValue = {
  excludeInvestments: boolean
  setExcludeInvestments: (value: boolean) => void
}

const AnalyticsPreferencesContext = createContext<AnalyticsPreferencesContextValue | null>(null)

function readStored(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

export function AnalyticsPreferencesProvider({ children }: { children: ReactNode }) {
  const [excludeInvestments, setExcludeInvestmentsState] = useState(readStored)

  const setExcludeInvestments = useCallback((value: boolean) => {
    setExcludeInvestmentsState(value)
    try {
      localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [])

  const value = useMemo(
    () => ({ excludeInvestments, setExcludeInvestments }),
    [excludeInvestments, setExcludeInvestments],
  )

  return (
    <AnalyticsPreferencesContext.Provider value={value}>
      {children}
    </AnalyticsPreferencesContext.Provider>
  )
}

export function useAnalyticsPreferences() {
  const ctx = useContext(AnalyticsPreferencesContext)
  if (!ctx) {
    throw new Error('useAnalyticsPreferences must be used within AnalyticsPreferencesProvider')
  }
  return ctx
}
