import { useMemo } from 'react'
import DOMPurify, { type Config } from 'dompurify'

import { cn } from '../../lib/cn'

/**
 * Безопасный рендер контента из админки (CKEditor 5).
 *
 * Два режима, выбираются автоматически:
 *  1. Если строка содержит HTML-теги → очищаем через DOMPurify (второй слой
 *     защиты поверх backend-санитайза nh3) и выводим как форматированный HTML
 *     внутри `.prose` (типографика Tailwind).
 *  2. Если тегов нет (легаси-блоки с обычным текстом и переносами `\n`) →
 *     выводим как простой текст с `white-space: pre-line`. Полная обратная
 *     совместимость со старым контентом.
 *
 * XSS невозможен: на сервере хранится уже очищенный HTML, на клиенте —
 * повторная очистка перед вставкой.
 */

// Теги, которые может породить наша панель CKEditor (см. CKEDITOR_5_CONFIGS).
const HTML_TAG_RE =
  /<\/?(?:p|br|hr|strong|b|em|i|u|s|h[1-6]|ul|ol|li|a|blockquote|table|thead|tbody|tr|th|td|code|pre|span)\b/i

const PURIFY_CONFIG: Config = {
  ALLOWED_TAGS: [
    'p', 'br', 'hr',
    'strong', 'b', 'em', 'i', 'u', 's',
    'h2', 'h3', 'h4',
    'ul', 'ol', 'li',
    'a',
    'blockquote',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'code', 'pre',
    'span',
  ],
  ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
}

interface SafeHtmlProps {
  html?: string | null
  /** Классы контейнера. По умолчанию — типографика `.prose`. */
  className?: string
  /** Текст-заглушка, если контент пуст. */
  fallback?: string
}

export function SafeHtml({ html, className, fallback }: SafeHtmlProps) {
  const raw = (html ?? '').trim()
  const isHtml = HTML_TAG_RE.test(raw)

  const clean = useMemo(
    () => (isHtml ? DOMPurify.sanitize(raw, PURIFY_CONFIG) : ''),
    [raw, isHtml],
  )

  if (!raw) {
    return fallback ? <div className={className}>{fallback}</div> : null
  }

  if (isHtml) {
    return (
      <div
        className={cn('prose max-w-none', className)}
        dangerouslySetInnerHTML={{ __html: clean }}
      />
    )
  }

  // Легаси: простой текст с сохранением переносов строк.
  return (
    <div className={className} style={{ whiteSpace: 'pre-line' }}>
      {raw}
    </div>
  )
}
