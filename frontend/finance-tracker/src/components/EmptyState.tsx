import type { ReactNode } from 'react'

type Props = {
  title: string
  description?: string
  action?: ReactNode
  icon?: ReactNode
}

export function EmptyState({ title, description, action, icon }: Props) {
  return (
    <div className="empty">
      {icon && <div style={{ marginBottom: 12, opacity: 0.6, display: 'flex', justifyContent: 'center' }}>{icon}</div>}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action && <div style={{ marginTop: 14, display: 'flex', justifyContent: 'center' }}>{action}</div>}
    </div>
  )
}
