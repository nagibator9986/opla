/**
 * Карточка-уведомление, которая показывается клиенту сразу после завершения
 * анкеты (status = 'completed' | 'under_audit'). Сообщает, что эксперт
 * готовит отчёт и пришлёт его в WhatsApp в течение 3–5 рабочих дней.
 *
 * Текст и срок берутся из ContentBlock'ов:
 *   • processing_title      — заголовок
 *   • processing_message    — основной текст
 *   • processing_eta        — ETA доставки (например, «3–5 рабочих дней»)
 *
 * При отсутствии (например пока API не настроен) — fallback значения ниже.
 */
import { useContentBlocks } from '../../hooks/useContentBlocks'
import { SafeHtml } from '../ui/SafeHtml'

export function ProcessingCard() {
  const { data: content } = useContentBlocks()
  const c = content ?? {}

  const title = c.processing_title ?? 'Анкета принята — отчёт в работе'
  const message =
    c.processing_message ??
    'Наш эксперт уже изучает ваши ответы и собирает именной forensic-отчёт. ' +
      'Готовый PDF мы пришлём в WhatsApp на указанный номер.'
  const eta = c.processing_eta ?? '3–5 рабочих дней'

  return (
    <div className="rounded-2xl border border-sky-200 bg-gradient-to-br from-white via-sky-50/40 to-blue-50/60 p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-sky-500 text-white flex items-center justify-center shadow-sm">
          {/* «hourglass / processing» иконка */}
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 22h14M5 2h14M6 22v-3a6 6 0 0 1 4-5.66M18 22v-3a6 6 0 0 0-4-5.66M6 2v3a6 6 0 0 0 4 5.66M18 2v3a6 6 0 0 1-4 5.66" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-bold text-ink-900">{title}</h3>
          <SafeHtml html={message} className="mt-1.5 text-sm text-ink-600 leading-relaxed" />
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sky-100 text-sky-900 text-xs font-semibold">
            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9 4a1 1 0 011 1v4l3 1.5a1 1 0 11-1 1.732l-3.5-2A1 1 0 018 9.5V5a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            <span>Срок: {eta}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
