import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { AlertTriangle, X } from 'lucide-react'

type Props = {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  children: ReactNode
  size?: 'md' | 'lg' | 'xl'
}

export function Modal({ open, onClose, title, subtitle, children, size = 'md' }: Props) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="modal-overlay" onMouseDown={onClose}>
      <div
        className={`modal ${size === 'lg' ? 'modal-lg' : ''} ${size === 'xl' ? 'modal-xl' : ''}`}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="row-between modal-header" style={{ marginBottom: 4 }}>
          <h3>{title}</h3>
          <button type="button" className="btn btn-ghost btn-icon" onClick={onClose} aria-label="Закрыть">
            <X size={16} />
          </button>
        </div>
        {subtitle && <p className="modal-subtitle">{subtitle}</p>}
        {children}
      </div>
    </div>,
    document.body,
  )
}

type ConfirmDialogProps = {
  open: boolean
  title: string
  message?: string
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Удалить',
  onConfirm,
  onCancel,
  loading = false,
}: ConfirmDialogProps) {
  return (
    <Modal open={open} onClose={onCancel} title="">
      <div style={{ textAlign: 'center', padding: '8px 0 4px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 48, height: 48, borderRadius: '50%',
          background: 'rgba(239,71,97,0.12)', marginBottom: 16,
        }}>
          <AlertTriangle size={22} color="#ef4761" />
        </div>
        <div style={{ fontWeight: 600, fontSize: 16, marginBottom: message ? 8 : 0 }}>{title}</div>
        {message && <div className="dim" style={{ fontSize: 14 }}>{message}</div>}
      </div>
      <div className="modal-actions" style={{ marginTop: 24 }}>
        <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={loading}>
          Отмена
        </button>
        <button type="button" className="btn btn-danger" onClick={onConfirm} disabled={loading}>
          {loading ? '…' : confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
