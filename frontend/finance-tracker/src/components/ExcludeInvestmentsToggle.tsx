import { useAnalyticsPreferences } from '@/context/AnalyticsPreferencesContext'

export function ExcludeInvestmentsToggle() {
  const { excludeInvestments, setExcludeInvestments } = useAnalyticsPreferences()

  return (
    <label
      className="row"
      style={{
        gap: 10,
        cursor: 'pointer',
        padding: '10px 14px',
        background: 'rgba(11,16,32,0.35)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        flexWrap: 'wrap',
      }}
    >
      <input
        type="checkbox"
        checked={excludeInvestments}
        onChange={(e) => setExcludeInvestments(e.target.checked)}
      />
      <span style={{ fontWeight: 500 }}>Без категории «Инвестиции»</span>
      <span className="dim" style={{ fontSize: 13 }}>
        Исключить операции по покупке активов из расходов, графиков и коэффициентов
      </span>
    </label>
  )
}
