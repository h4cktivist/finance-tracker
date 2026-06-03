import { useState } from 'react'
import { Bell, CheckCheck } from 'lucide-react'
import {
  useMarkAllRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/hooks/useQueries'
import { EmptyState } from '@/components/EmptyState'
import { formatRelative } from '@/lib/format'
import type { NotificationType } from '@/lib/types'

const TYPE_LABELS: Record<NotificationType, string> = {
  budget_warning: 'Бюджет',
  budget_exceeded: 'Превышен бюджет',
  recurring_created: 'Подписка',
  goal_deadline: 'Дедлайн цели',
  cashback_available: 'Кэшбэк',
}

const TYPE_VARIANT: Record<NotificationType, string> = {
  budget_warning: 'warning',
  budget_exceeded: 'danger',
  recurring_created: 'info',
  goal_deadline: 'primary',
  cashback_available: 'success',
}

export function NotificationsPage() {
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [page, setPage] = useState(1)
  const { data, isLoading } = useNotifications(unreadOnly, page, 30)
  const markRead = useMarkNotificationRead()
  const markAll = useMarkAllRead()

  const items = data?.items ?? []

  return (
    <>
      <div className="row-between page-toolbar">
        <div className="row" style={{ background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 12, padding: 4 }}>
          <button
            className={`btn btn-sm ${!unreadOnly ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => { setUnreadOnly(false); setPage(1) }}
          >
            Все
          </button>
          <button
            className={`btn btn-sm ${unreadOnly ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => { setUnreadOnly(true); setPage(1) }}
          >
            Непрочитанные
          </button>
        </div>
        <button className="btn btn-secondary" onClick={() => markAll.mutate()}>
          <CheckCheck size={14} /> Отметить все прочитанными
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {isLoading ? (
          <div className="muted" style={{ padding: 20 }}>Загрузка…</div>
        ) : items.length === 0 ? (
          <EmptyState
            title={unreadOnly ? 'Нет непрочитанных' : 'Пока нет уведомлений'}
            description="Здесь будут уведомления о бюджетах, подписках, целях и кэшбэке"
            icon={<Bell size={36} />}
          />
        ) : (
          <div>
            {items.map((n) => {
              const variant = TYPE_VARIANT[n.type] ?? 'muted'
              return (
                <div
                  key={n.id}
                  className={`notif-item ${!n.read_at ? 'unread' : ''}`}
                  onClick={() => { if (!n.read_at) markRead.mutate(n.id) }}
                  style={{ padding: '16px 20px' }}
                >
                  <div className="row-between">
                    <div className="row" style={{ gap: 10 }}>
                      {!n.read_at && <span className="dot" />}
                      <span className={`badge badge-${variant}`}>{TYPE_LABELS[n.type] ?? n.type}</span>
                      <span style={{ fontWeight: 500 }}>{n.title}</span>
                    </div>
                    <span className="dim">{formatRelative(n.created_at)}</span>
                  </div>
                  <div className="muted" style={{ marginTop: 6 }}>{n.body}</div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {data && data.pages > 1 && (
        <div className="row-between">
          <span className="muted">Всего: {data.total}</span>
          <div className="row" style={{ gap: 6 }}>
            <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              ← Назад
            </button>
            <span className="muted">{page} / {data.pages}</span>
            <button className="btn btn-ghost btn-sm" disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>
              Вперёд →
            </button>
          </div>
        </div>
      )}
    </>
  )
}
