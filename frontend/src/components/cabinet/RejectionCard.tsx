/**
 * Карточка вежливого отказа в обработке аудита.
 *
 * Показывается клиенту в кабинете, если он не прошёл фильтр квалификации:
 *   • количество сотрудников < 10, ИЛИ
 *   • среднемесячный оборот < 50 млн ₸.
 *
 * Текст приходит с backend в `submission.rejection_reason` — он же
 * записывается в чате как последнее сообщение от AI. Здесь — просто
 * визуальное оформление карточки.
 */
interface RejectionCardProps {
  reason: string
}

export function RejectionCard({ reason }: RejectionCardProps) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-gradient-to-br from-white via-amber-50/40 to-orange-50/60 p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-sm">
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-bold text-ink-900">Не подошли по критериям</h3>
          <p className="mt-3 text-sm text-ink-700 leading-relaxed whitespace-pre-line">
            {reason}
          </p>
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-100 text-amber-900 text-xs font-semibold">
            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
            </svg>
            <span>Спасибо, что нашли время</span>
          </div>
        </div>
      </div>
    </div>
  )
}
