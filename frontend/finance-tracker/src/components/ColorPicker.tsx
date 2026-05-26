import { useEffect, useRef, useState } from 'react'
import { HexColorPicker } from 'react-colorful'
import { Check, X } from 'lucide-react'

const PRESETS = [
  '#7c5cff', '#9a82ff', '#a78bfa', '#38bdf8', '#22d3ee', '#06b6d4',
  '#2dd4bf', '#34d399', '#10b981', '#84cc16', '#facc15', '#f5b450',
  '#fb923c', '#f97316', '#ef4761', '#e11d48', '#ec4899', '#d946ef',
  '#8b5cf6', '#64748b', '#94a3b8', '#0ea5e9', '#14b8a6', '#dc2626',
]

type Props = {
  value: string | null | undefined
  onChange: (color: string | null) => void
  label?: string
  allowEmpty?: boolean
}

function isValidHex(s: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(s) || /^#[0-9a-fA-F]{3}$/.test(s)
}

export function ColorPicker({ value, onChange, label, allowEmpty = true }: Props) {
  const [open, setOpen] = useState(false)
  const [hexInput, setHexInput] = useState(value ?? '')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setHexInput(value ?? '')
  }, [value])

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  const current = value && isValidHex(value) ? value : '#7c5cff'

  return (
    <div className="field" ref={ref} style={{ position: 'relative' }}>
      {label && <label>{label}</label>}
      <div className="row" style={{ gap: 10, alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="color-trigger"
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: value || 'transparent',
            border: '1px solid var(--border-strong)',
            cursor: 'pointer',
            backgroundImage: !value
              ? 'repeating-conic-gradient(rgba(120,134,200,0.2) 0% 25%, transparent 0% 50%) 50% / 12px 12px'
              : undefined,
          }}
          aria-label="Выбрать цвет"
        />
        <div className="muted mono" style={{ fontSize: 13 }}>
          {value || 'не задан'}
        </div>
        {allowEmpty && value && (
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
        <div className="color-popover">
          <HexColorPicker color={current} onChange={(c) => onChange(c)} />

          <div className="color-presets">
            {PRESETS.map((c) => (
              <button
                key={c}
                type="button"
                className="color-preset"
                onClick={() => onChange(c)}
                style={{ background: c }}
                aria-label={c}
              >
                {value?.toLowerCase() === c.toLowerCase() && <Check size={12} />}
              </button>
            ))}
          </div>

          <div className="color-hex-row">
            <span className="dim">HEX</span>
            <input
              className="input mono"
              value={hexInput}
              onChange={(e) => {
                const v = e.target.value
                setHexInput(v)
                if (isValidHex(v)) onChange(v)
              }}
              placeholder="#7c5cff"
            />
            <button type="button" className="btn btn-primary btn-sm" onClick={() => setOpen(false)}>
              Готово
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
