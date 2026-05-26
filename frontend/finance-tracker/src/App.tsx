import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import type { JSX } from 'react'
import { AuthLayout } from './layouts/AuthLayout'
import { AppLayout } from './layouts/AppLayout'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage'
import { DashboardPage } from './pages/DashboardPage'
import { AccountsPage } from './pages/AccountsPage'
import { CategoriesPage } from './pages/CategoriesPage'
import { TagsPage } from './pages/TagsPage'
import { TransactionsPage } from './pages/TransactionsPage'
import { BudgetsPage } from './pages/BudgetsPage'
import { RecurringPage } from './pages/RecurringPage'
import { CashbackPage } from './pages/CashbackPage'
import { GoalsPage } from './pages/GoalsPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'

function Protected({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isInitializing } = useAuth()
  if (isInitializing) {
    return <div className="auth-shell"><div className="muted">Загрузка…</div></div>
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function GuestOnly({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isInitializing } = useAuth()
  if (isInitializing) return <div className="auth-shell"><div className="muted">Загрузка…</div></div>
  if (isAuthenticated) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route
        element={
          <GuestOnly>
            <AuthLayout />
          </GuestOnly>
        }
      >
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>

      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/tags" element={<TagsPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/budgets" element={<BudgetsPage />} />
        <Route path="/recurring" element={<RecurringPage />} />
        <Route path="/cashback" element={<CashbackPage />} />
        <Route path="/goals" element={<GoalsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
