import { useAnalyticsPreferences } from '@/context/AnalyticsPreferencesContext'

export function ExcludeInvestmentsToggle() {
  const { excludeInvestments, setExcludeInvestments } = useAnalyticsPreferences()

  return (
    <label className="exclude-investments-toggle">
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
