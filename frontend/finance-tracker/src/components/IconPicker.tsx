import { useEffect, useMemo, useRef, useState } from 'react'
import { Folder, Search, X } from 'lucide-react'
import { ICON_MAP, ICON_NAMES, getIcon } from '@/lib/icons'

type Props = {
  value: string | null | undefined
  onChange: (icon: string | null) => void
  label?: string
}

export function IconPicker({ value, onChange, label }: Props) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    if (!q) return ICON_NAMES
    return ICON_NAMES.filter((n) => n.toLowerCase().includes(q))
  }, [query])

  const CurrentIcon = getIcon(value) ?? Folder

  return (
    <div className="field" ref={ref} style={{ position: 'relative' }}>
      {label && <label>{label}</label>}
      <div className="row" style={{ gap: 10, alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: 'rgba(11,16,32,0.6)',
            border: '1px solid var(--border-strong)',
            cursor: 'pointer',
            display: 'grid',
            placeItems: 'center',
            color: value ? 'var(--text)' : 'var(--text-dim)',
          }}
          aria-label="Выбрать иконку"
        >
          <CurrentIcon size={18} />
        </button>
        <div className="muted" style={{ fontSize: 13 }}>{value || 'не задана'}</div>
        {value && (
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-sm"
            onClick={() => onChange(null)}
            title="Очистить"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {open && (
        <div className="icon-popover">
          <div className="icon-search">
            <Search size={14} className="muted" />
            <input
              className="input"
              placeholder="Поиск иконки…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
          </div>
          <div className="icon-grid">
            {filtered.length === 0 ? (
              <div className="dim" style={{ padding: 16, gridColumn: '1 / -1', textAlign: 'center' }}>
                Ничего не найдено
              </div>
            ) : (
              filtered.map((name) => {
                const Icon = ICON_MAP[name]
                const active = value === name
                return (
                  <button
                    key={name}
                    type="button"
                    className={`icon-item ${active ? 'active' : ''}`}
                    onClick={() => { onChange(name); setOpen(false) }}
                    title={name}
                  >
                    <Icon size={18} />
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
