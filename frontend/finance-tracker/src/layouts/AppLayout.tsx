import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  BarChart3,
  Bell,
  Briefcase,
  CreditCard,
  Folder,
  Goal as GoalIcon,
  LayoutDashboard,
  LogOut,
  Menu,
  Receipt,
  RefreshCw,
  Tag,
  Sparkles,
  Target,
  Wallet,
  Wallet2,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { NotificationsBell } from '@/components/NotificationsBell'

const SECTIONS: Array<{
  title?: string
  items: Array<{ to: string; label: string; icon: typeof Wallet }>
}> = [
  {
    items: [{ to: '/', label: 'Дашборд', icon: LayoutDashboard }],
  },
  {
    title: 'Финансы',
    items: [
      { to: '/transactions', label: 'Транзакции', icon: Receipt },
      { to: '/accounts', label: 'Счета', icon: Wallet2 },
      { to: '/broker', label: 'Брокерский счёт', icon: Briefcase },
      { to: '/budgets', label: 'Бюджеты', icon: Target },
      { to: '/recurring', label: 'Подписки', icon: RefreshCw },
    ],
  },
  {
    title: 'Управление',
    items: [
      { to: '/categories', label: 'Категории', icon: Folder },
      { to: '/tags', label: 'Теги', icon: Tag },
      { to: '/cashback', label: 'Кэшбэк', icon: CreditCard },
      { to: '/goals', label: 'Цели', icon: GoalIcon },
    ],
  },
  {
    title: 'Прочее',
    items: [
      { to: '/analytics', label: 'Аналитика', icon: BarChart3 },
      { to: '/recommendations', label: 'ИИ-советы', icon: Sparkles },
      { to: '/notifications', label: 'Уведомления', icon: Bell },
    ],
  },
]

const TITLES: Record<string, string> = {
  '/': 'Дашборд',
  '/transactions': 'Транзакции',
  '/accounts': 'Счета',
  '/broker': 'Брокерский счёт',
  '/budgets': 'Бюджеты',
  '/recurring': 'Повторяющиеся операции',
  '/categories': 'Категории',
  '/tags': 'Теги',
  '/cashback': 'Кэшбэк',
  '/goals': 'Цели',
  '/analytics': 'Аналитика',
  '/recommendations': 'ИИ-советы',
  '/notifications': 'Уведомления',
}

export function AppLayout() {
  const { user, logout } = useAuth()
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const title = TITLES[loc.pathname] ?? 'Finance Tracker'

  useEffect(() => {
    setMobileOpen(false)
  }, [loc.pathname])

  return (
    <div className="app-shell">
      <div
        className={`drawer-backdrop ${mobileOpen ? 'open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Wallet size={18} /></div>
          <span>Finance Tracker</span>
        </div>

        {SECTIONS.map((section, sIdx) => (
          <div key={sIdx}>
            {section.title && <div className="nav-section">{section.title}</div>}
            {section.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </div>
        ))}

        <div className="user-card">
          <div className="avatar">
            {(user?.email ?? '?')[0]?.toUpperCase()}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div className="email" title={user?.email}>{user?.email}</div>
            <div className="dim">В сети</div>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={() => void logout()}
            title="Выйти"
            aria-label="Выйти"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="row" style={{ gap: 10 }}>
            <button
              type="button"
              className="hamburger"
              onClick={() => setMobileOpen(true)}
              aria-label="Меню"
            >
              <Menu size={20} />
            </button>
            <h1>{title}</h1>
          </div>
          <div className="actions">
            <NotificationsBell />
          </div>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
