import { useState } from 'react'
import { useContentBlocks } from '../../hooks/useContentBlocks'
import { SafeHtml } from '../ui/SafeHtml'

/**
 * Карточка-донат, показывается клиенту в кабинете когда отчёт выдан (delivered).
 *
 * Все тексты + номер карты редактируются админом через `/admin/content/contentblock/`:
 *   • donation_title          — заголовок
 *   • donation_message        — основной текст
 *   • donation_card_number    — номер карты (форматированный)
 *   • donation_card_holder    — опционально, имя держателя
 *   • donation_card_bank      — опционально, банк
 */
export function DonationBlock() {
  const { data: content } = useContentBlocks()
  const c = content ?? {}

  const title = c.donation_title ?? 'Ваш forensic-отчёт сформирован и выдан'
  const message =
    c.donation_message ??
    'На текущем этапе калибровки Digital Baqsy платежные шлюзы находятся в режиме отладки.\n\n' +
      'Если Вы хотите поддержать команду разработчиков, можете отправить любую комфортную для вас сумму (донат) по реквизитам ниже. Ваш вклад ускорит развитие Системы.'
  const cardNumber = c.donation_card_number ?? '4904 7298 1111 9463'
  const cardHolder = c.donation_card_holder ?? ''
  const cardBank = c.donation_card_bank ?? ''

  const [copied, setCopied] = useState(false)

  // Чистый номер для копирования (без пробелов — удобнее вставлять в банковское приложение)
  const cleanCard = cardNumber.replace(/\s+/g, '')

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(cleanCard)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback для старых браузеров (HTTP / отсутствие clipboard API)
      const ta = document.createElement('textarea')
      ta.value = cleanCard
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      try {
        document.execCommand('copy')
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } finally {
        document.body.removeChild(ta)
      }
    }
  }

  return (
    <div className="rounded-2xl overflow-hidden border border-brand-200 bg-gradient-to-br from-white via-brand-50/30 to-amber-50/40 shadow-sm">
      <div className="px-6 py-5 border-b border-brand-100/70 bg-gradient-to-r from-brand-50 to-transparent">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-brand-500 text-white flex items-center justify-center shadow-sm">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="min-w-0">
            <h3 className="text-base font-bold text-ink-900 leading-snug">{title}</h3>
            <p className="text-xs text-brand-700 font-semibold mt-1 uppercase tracking-wider">
              Поддержать команду разработчиков
            </p>
          </div>
        </div>
      </div>

      <div className="px-6 py-5">
        <SafeHtml html={message} className="text-sm text-ink-700 leading-relaxed" />

        <div className="mt-5 rounded-xl border-2 border-dashed border-brand-300/70 bg-white/60 backdrop-blur-sm p-4">
          <div className="flex items-center justify-between gap-3 mb-2">
            <span className="text-xs font-semibold text-ink-500 uppercase tracking-wider">
              Номер карты
            </span>
            <button
              type="button"
              onClick={handleCopy}
              aria-label="Скопировать номер карты"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                copied
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-brand-500 hover:bg-brand-600 text-white shadow-sm hover:shadow'
              }`}
            >
              {copied ? (
                <>
                  <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                  </svg>
                  Скопировано
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M7 3a1 1 0 011-1h6a1 1 0 011 1v1h1a2 2 0 012 2v10a2 2 0 01-2 2h-2v1a2 2 0 01-2 2H4a2 2 0 01-2-2V7a2 2 0 012-2h2V3z" />
                  </svg>
                  Скопировать
                </>
              )}
            </button>
          </div>
          <div className="font-mono text-xl md:text-2xl font-semibold text-ink-900 tabular-nums tracking-wider select-all">
            {cardNumber}
          </div>
          {(cardHolder || cardBank) && (
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-500">
              {cardHolder && (
                <span>
                  <span className="font-medium text-ink-400">Держатель:</span> {cardHolder}
                </span>
              )}
              {cardBank && (
                <span>
                  <span className="font-medium text-ink-400">Банк:</span> {cardBank}
                </span>
              )}
            </div>
          )}
        </div>

        <p className="mt-3 text-[11px] text-ink-400 leading-relaxed">
          Перевод по этим реквизитам — добровольный донат. Платёж не является оплатой
          обязательного характера и не отражается в бухгалтерии Baqsy как доход от услуг.
        </p>
      </div>
    </div>
  )
}
