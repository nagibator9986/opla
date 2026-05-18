import { useState } from 'react'
import { ChatWidget } from '../chat/ChatWidget'

interface Props {
  submissionId: string
}

/** Большая CTA в кабинете — открывает чат сразу в режиме questionnaire.
 *
 * sessionId здесь намеренно НЕ читается из localStorage. ChatWidget сам
 * на bootstrap создаст свежую сессию (через /chat/start/) и привяжет её
 * к авторизованному юзеру — backend перевяжет session.client к владельцу
 * submission, и start-questionnaire пройдёт без 403 «Заявка не
 * принадлежит этой сессии».
 */
export function ContinueQuestionnaireButton({ submissionId }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="w-full inline-flex items-center justify-center gap-2 px-6 py-4 rounded-2xl bg-ink-900 text-white text-base font-semibold hover:bg-ink-800 transition-colors shadow-lg"
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Открыть чат и продолжить
        <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
          <path
            fillRule="evenodd"
            d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
      <ChatWidget
        open={open}
        onClose={() => setOpen(false)}
        autoStartQuestionnaireFor={{ submissionId }}
      />
    </>
  )
}
