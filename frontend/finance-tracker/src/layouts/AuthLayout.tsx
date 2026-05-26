import { Outlet } from 'react-router-dom'
import { Wallet } from 'lucide-react'

export function AuthLayout() {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand-large">
          <div className="mark"><Wallet size={20} /></div>
          <span>Finance Tracker</span>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
