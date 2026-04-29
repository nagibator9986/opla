import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

/**
 * Безопасный рендер сообщения от ассистента/пользователя:
 *
 * - `**жирный**` → <strong>жирный</strong>
 * - внутренние пути `/tariffs`, `/cabinet`, `/cases` → <Link to="…"> (подсвечен)
 * - внешние ссылки `https://example.com` → <a target="_blank">
 *
 * Никакого dangerouslySetInnerHTML — всё через React-узлы. XSS невозможен.
 */
const URL_REGEX = /(https?:\/\/[^\s)]+)|(\/(?:tariffs|cabinet|cases|blog|invite)(?:\/[a-zA-Z0-9\-_/]*)?)/g
const BOLD_REGEX = /\*\*([^*\n]+)\*\*/g

interface MessagePart {
  kind: 'text' | 'bold' | 'internal' | 'external'
  content: string
  href?: string
}

function tokenize(input: string): MessagePart[] {
  // Сначала находим bold-сегменты, потом внутри текстовых сегментов — ссылки.
  const parts: MessagePart[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null
  // Reset state for global regex
  BOLD_REGEX.lastIndex = 0
  while ((match = BOLD_REGEX.exec(input)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ kind: 'text', content: input.slice(lastIndex, match.index) })
    }
    parts.push({ kind: 'bold', content: match[1] })
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < input.length) {
    parts.push({ kind: 'text', content: input.slice(lastIndex) })
  }

  // Сейчас в parts могут быть text-сегменты с URL внутри. Разворачиваем их.
  const out: MessagePart[] = []
  for (const p of parts) {
    if (p.kind !== 'text') {
      out.push(p)
      continue
    }
    let cursor = 0
    URL_REGEX.lastIndex = 0
    let m: RegExpExecArray | null
    while ((m = URL_REGEX.exec(p.content)) !== null) {
      if (m.index > cursor) {
        out.push({ kind: 'text', content: p.content.slice(cursor, m.index) })
      }
      const matched = m[0]
      if (matched.startsWith('/')) {
        // strip trailing punctuation that should belong to text, not the URL
        const cleaned = matched.replace(/[.,;:!?)\]]+$/, '')
        const trail = matched.slice(cleaned.length)
        out.push({ kind: 'internal', content: cleaned, href: cleaned })
        if (trail) out.push({ kind: 'text', content: trail })
      } else {
        const cleaned = matched.replace(/[.,;:!?)\]]+$/, '')
        const trail = matched.slice(cleaned.length)
        out.push({ kind: 'external', content: cleaned, href: cleaned })
        if (trail) out.push({ kind: 'text', content: trail })
      }
      cursor = m.index + matched.length
    }
    if (cursor < p.content.length) {
      out.push({ kind: 'text', content: p.content.slice(cursor) })
    }
  }

  return out
}

export function renderMessage(text: string): ReactNode {
  if (!text) return null
  const parts = tokenize(text)
  return parts.map((p, i) => {
    if (p.kind === 'bold') {
      return (
        <strong key={i} className="font-semibold">
          {p.content}
        </strong>
      )
    }
    if (p.kind === 'internal' && p.href) {
      return (
        <Link
          key={i}
          to={p.href}
          className="font-semibold text-brand-700 hover:text-brand-600 underline underline-offset-2 decoration-brand-300/60 hover:decoration-brand-500 transition-colors"
        >
          {p.content}
        </Link>
      )
    }
    if (p.kind === 'external' && p.href) {
      return (
        <a
          key={i}
          href={p.href}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-brand-700 hover:text-brand-600 underline underline-offset-2 decoration-brand-300/60 hover:decoration-brand-500 transition-colors"
        >
          {p.content}
        </a>
      )
    }
    return <Fragment key={i}>{p.content}</Fragment>
  })
}
