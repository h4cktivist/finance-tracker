import { useEffect, useRef, useState } from 'react'
import { Bell, CheckCheck } from 'lucide-react'
import { useMarkAllRead, useMarkNotificationRead, useNotifications } from '@/hooks/useQueries'
import { formatRelative } from '@/lib/format'
import { Link } from 'react-router-dom'

export function NotificationsBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const { data } = useNotifications(false, 1, 10)
  const markRead = useMarkNotificationRead()
  const markAll = useMarkAllRead()

  const unread = data?.items.filter((n) => !n.read_at).length ?? 0

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  return (
    <div className="dropdown" ref={ref}>
      <button
        type="button"
        className="btn btn-ghost btn-icon"
        onClick={() => setOpen((v) => !v)}
        aria-label="Уведомления"
      >
        <span className="bell-wrap">
          <Bell size={18} />
          {unread > 0 && <span className="bell-badge">{unread > 99 ? '99+' : unread}</span>}
        </span>
      </button>

      {open && (
        <div className="dropdown-panel">
          <header>
            <span>Уведомления</span>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => markAll.mutate()}
              disabled={unread === 0}
            >
              <CheckCheck size={14} />
              Прочитать всё
            </button>
          </header>
          <div className="dropdown-body">
            {!data || data.items.length === 0 ? (
              <div className="empty">
                <p>Пока пусто</p>
              </div>
            ) : (
              data.items.map((n) => (
                <div
                  key={n.id}
                  className={`notif-item ${!n.read_at ? 'unread' : ''}`}
                  onClick={() => {
                    if (!n.read_at) markRead.mutate(n.id)
                  }}
                >
                  <div className="title">
                    {!n.read_at && <span className="dot" />}
                    {n.title}
                  </div>
                  <div className="body">{n.body}</div>
                  <div className="time">{formatRelative(n.created_at)}</div>
                </div>
              ))
            )}
          </div>
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', textAlign: 'center' }}>
            <Link to="/notifications" onClick={() => setOpen(false)} style={{ fontSize: 13 }}>
              Все уведомления →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
