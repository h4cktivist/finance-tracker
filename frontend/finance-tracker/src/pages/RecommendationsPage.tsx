import { useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { ChevronLeft, ChevronRight, Loader2, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import { EmptyState } from '@/components/EmptyState'
import { useAiRecommendations } from '@/hooks/useQueries'
import { handleApiError } from '@/lib/errors'

function currentMonthYm(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function shiftMonth(ym: string, delta: number): string {
  const [y, m] = ym.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function formatMonthLabel(ym: string): string {
  const [y, m] = ym.split('-').map(Number)
  const d = new Date(y, m - 1, 1)
  return format(d, 'LLLL yyyy', { locale: ru })
}

export function RecommendationsPage() {
  const [month, setMonth] = useState(currentMonthYm)
  const [content, setContent] = useState<string | null>(null)
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null)
  const generate = useAiRecommendations()

  useEffect(() => {
    setContent(null)
    setGeneratedAt(null)
  }, [month])

  const monthLabel = useMemo(() => formatMonthLabel(month), [month])
  const isFutureMonth = useMemo(() => {
    const [y, m] = month.split('-').map(Number)
    const selected = new Date(y, m - 1, 1)
    const now = new Date()
    const current = new Date(now.getFullYear(), now.getMonth(), 1)
    return selected > current
  }, [month])

  const handleGenerate = async () => {
    if (isFutureMonth) {
      toast.error('Нельзя запросить рекомендации для будущего месяца')
      return
    }
    try {
      const result = await generate.mutateAsync(month)
      setContent(result.content)
      setGeneratedAt(new Date())
    } catch (err) {
      handleApiError(err, 'Не удалось получить рекомендации')
    }
  }

  return (
    <>
      <section className="card ai-toolbar">
        <p className="ai-toolbar-desc">
          ИИ анализирует ваши транзакции за выбранный месяц и предлагает персональные рекомендации
          по управлению финансами.
        </p>
        <div className="ai-month-controls">
          <button
            type="button"
            className="btn btn-secondary btn-icon"
            onClick={() => setMonth((m) => shiftMonth(m, -1))}
            aria-label="Предыдущий месяц"
          >
            <ChevronLeft size={18} />
          </button>
          <div className="field ai-month-field">
            <label htmlFor="ai-month">Месяц</label>
            <input
              id="ai-month"
              className="input"
              type="month"
              value={month}
              max={currentMonthYm()}
              onChange={(e) => setMonth(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-icon"
            onClick={() => setMonth((m) => shiftMonth(m, 1))}
            disabled={month >= currentMonthYm()}
            aria-label="Следующий месяц"
          >
            <ChevronRight size={18} />
          </button>
          <button
            type="button"
            className="btn btn-primary ai-generate-btn"
            onClick={() => void handleGenerate()}
            disabled={generate.isPending || isFutureMonth}
          >
            {generate.isPending ? (
              <>
                <Loader2 size={16} className="spin" /> Анализ…
              </>
            ) : (
              <>
                <Sparkles size={16} /> Получить рекомендации
              </>
            )}
          </button>
        </div>
      </section>

      {generate.isPending && !content && (
        <section className="card ai-loading">
          <Loader2 size={28} className="spin" />
          <p>ИИ изучает транзакции за {monthLabel}…</p>
          <p className="hint dim">Это может занять до минуты</p>
        </section>
      )}

      {!generate.isPending && content === null && (
        <EmptyState
          icon={<Sparkles size={32} />}
          title="Рекомендации ещё не сформированы"
          description={`Выберите месяц и нажмите «Получить рекомендации», чтобы ИИ проанализировал ваши операции за ${monthLabel}.`}
        />
      )}

      {content !== null && (
        <section className="card ai-recommendations">
          <div className="card-header">
            <h2>Рекомендации за {monthLabel}</h2>
            {generatedAt && (
              <span className="hint dim">
                Обновлено {format(generatedAt, 'dd MMM yyyy, HH:mm', { locale: ru })}
              </span>
            )}
          </div>
          <article className="ai-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </article>
        </section>
      )}
    </>
  )
}
