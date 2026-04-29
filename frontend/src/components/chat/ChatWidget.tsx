import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import {
  collectProfile,
  exchangeForTokens,
  getChatConfig,
  sendMessage,
  startChat,
  startQuestionnaire,
  type CollectedData,
  type QuestionPayload,
  type QuickReply,
} from '../../api/chat'
import { cn } from '../../lib/cn'
import { apiErrorMessage } from '../../lib/apiError'
import { useAuthStore } from '../../store/authStore'
import { useToast } from '../ui/toast-context'

type ChatMsg = { id: string; role: 'assistant' | 'user'; content: string }

interface ChatWidgetProps {
  open: boolean
  onClose: () => void
  /** If set, widget auto-starts the questionnaire for this submission. */
  autoStartQuestionnaireFor?: { sessionId: string; submissionId: string } | null
}

const STORAGE_KEY = 'baqsy_chat_session_id'

function saveSessionId(id: string | null) {
  if (id) localStorage.setItem(STORAGE_KEY, id)
  else localStorage.removeItem(STORAGE_KEY)
}
function loadSessionId(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

// ──────────────────────────────────────────────────────────────────────────
// Регистрация = Этап I (паспорт компании, 7) + Этап II (роль, 1).
// Шаг 0 — имя, далее 1..7 — Этап I, 8 — Этап II.
// ──────────────────────────────────────────────────────────────────────────

type StepType = 'text' | 'longtext' | 'choice'

interface RegStep {
  key: keyof CollectedData
  label: string
  prompt: string
  type: StepType
  choices?: string[]
  placeholder?: string
}

const REG_STEPS: RegStep[] = [
  {
    key: 'name',
    label: 'Имя',
    prompt: 'Здравствуйте! Давайте познакомимся. Как Вас зовут? (имя и фамилия)',
    type: 'text',
    placeholder: 'Например, Айдар Жунусов',
  },
  {
    key: 'company',
    label: 'Компания',
    prompt: 'Название компании или бренда?',
    type: 'text',
    placeholder: 'ТОО «Baqsy Audit»',
  },
  {
    key: 'company_website',
    label: 'Сайт',
    prompt: 'Ссылка на сайт или бизнес-аккаунт компании? Если нет — напишите «нет».',
    type: 'text',
    placeholder: 'https://example.com или нет',
  },
  {
    key: 'industry_field',
    label: 'Сфера деятельности',
    prompt: 'Сфера деятельности компании?',
    type: 'text',
    placeholder: 'Ритейл, IT, Производство, Услуги, F&B…',
  },
  {
    key: 'city',
    label: 'Локация',
    prompt: 'Локация компании (регион, город)?',
    type: 'text',
    placeholder: 'Алматы / Астана / РК, регион…',
  },
  {
    key: 'employees_count',
    label: 'Сотрудники',
    prompt: 'Количество сотрудников?',
    type: 'text',
    placeholder: '5 / 25 / 200…',
  },
  {
    key: 'company_age',
    label: 'Срок существования',
    prompt: 'Срок существования компании? (например, «5 лет» или «с 2019»)',
    type: 'text',
    placeholder: '5 лет / с 2019',
  },
  {
    key: 'parent_company',
    label: 'Головная компания',
    prompt:
      'Название головной компании? Если организация входит в холдинг — название холдинга. Если нет — просто повторите название компании.',
    type: 'text',
    placeholder: 'Название холдинга или той же компании',
  },
  {
    key: 'role',
    label: 'Уровень ответственности',
    prompt: 'Ваш уровень ответственности в системе?',
    type: 'choice',
    choices: ['Владелец / Совладелец', 'Топ-менеджер', 'Менеджер среднего / нижнего звена'],
  },
]

export function ChatWidget({ open, onClose, autoStartQuestionnaireFor }: ChatWidgetProps) {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const toast = useToast()
  const [sessionId, setSessionId] = useState<string | null>(loadSessionId())
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([])
  const [currentQuestion, setCurrentQuestion] = useState<QuestionPayload | null>(null)
  const [multichoicePicked, setMultichoicePicked] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  // Регистрация: -1 = не начата, 0..N = текущий шаг, N+1 = завершена
  const [regStep, setRegStep] = useState<number>(-1)
  const [regAnswers, setRegAnswers] = useState<Partial<CollectedData>>({})
  const listRef = useRef<HTMLDivElement>(null)
  const nextIdRef = useRef(0)
  const nextId = (prefix: string) => {
    nextIdRef.current += 1
    return `${prefix}-${nextIdRef.current}`
  }

  const { data: config } = useQuery({
    queryKey: ['chat-config'],
    queryFn: getChatConfig,
    staleTime: 5 * 60 * 1000,
  })

  const pushAssistant = (content: string) => {
    setMessages((prev) => [...prev, { id: nextId('a'), role: 'assistant', content }])
  }
  const pushUser = (text: string) => {
    setMessages((prev) => [...prev, { id: nextId('u'), role: 'user', content: text }])
  }

  // Bootstrap — start session if needed
  useEffect(() => {
    if (!open || sessionId !== null) return
    let cancelled = false
    ;(async () => {
      try {
        const resp = await startChat()
        if (cancelled) return
        setSessionId(resp.session_id)
        saveSessionId(resp.session_id)
        setMessages([{ id: nextId('greet'), role: 'assistant', content: resp.greeting }])
        setQuickReplies(resp.quick_replies)
      } catch (err) {
        console.error(err)
        toast.show({
          kind: 'error',
          title: 'Не удалось открыть чат',
          description: 'Попробуйте перезагрузить страницу или напишите info@baqsy.kz',
        })
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, sessionId])

  // Авто-запуск регистрации для гостя.
  // Открыли чат, sessionId есть, юзер НЕ авторизован, рег-флоу ещё не стартовал
  // и не идёт questionnaire — стартуем регистрацию автоматически (после greeting).
  useEffect(() => {
    if (!open || !sessionId || isAuthenticated) return
    if (regStep !== -1 || currentQuestion) return
    if (autoStartQuestionnaireFor) return
    const t = setTimeout(() => {
      // Проверим, что состояние всё ещё актуально к моменту таймаута
      setRegStep((prev) => {
        if (prev !== -1) return prev
        return 0
      })
      pushAssistant(REG_STEPS[0].prompt)
      setQuickReplies([])
    }, 600)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, sessionId, isAuthenticated, autoStartQuestionnaireFor])

  // Auto-start questionnaire
  useEffect(() => {
    if (!open || !autoStartQuestionnaireFor || !sessionId) return
    if (autoStartQuestionnaireFor.sessionId !== sessionId) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const resp = await startQuestionnaire(
          autoStartQuestionnaireFor.sessionId,
          autoStartQuestionnaireFor.submissionId,
        )
        if (cancelled) return
        pushAssistant(resp.intro)
        setQuickReplies([])
        if (resp.next_question) {
          pushAssistant(prefixStage(resp.next_question))
          setCurrentQuestion(resp.next_question)
        }
      } catch (err: unknown) {
        toast.show({
          kind: 'error',
          title: 'Ошибка',
          description: apiErrorMessage(err, 'Не удалось начать анкету.'),
        })
      } finally {
        setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, sessionId, autoStartQuestionnaireFor])

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [messages, loading])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // Запуск регистрации
  const startRegistration = () => {
    if (regStep !== -1) return
    setRegStep(0)
    pushAssistant(REG_STEPS[0].prompt)
    setQuickReplies([])
  }

  const sendContent = async (content: string | string[]) => {
    if (!sessionId || loading) return
    const display = Array.isArray(content) ? content.join(', ') : content
    if (!display.trim()) return
    pushUser(display)
    setInput('')
    setQuickReplies([])
    setMultichoicePicked([])
    setLoading(true)
    try {
      const resp = await sendMessage(sessionId, content)
      if (resp.reply?.content) pushAssistant(resp.reply.content)
      if (resp.next_question) {
        setCurrentQuestion(resp.next_question)
      } else if (resp.completed) {
        setCurrentQuestion(null)
      }
    } catch (err) {
      pushAssistant(apiErrorMessage(err, 'AI-ассистент временно недоступен.'))
    } finally {
      setLoading(false)
    }
  }

  const handleQuickReply = (qr: QuickReply) => {
    sendContent(qr.payload)
  }

  // Шаг регистрации: сохранить ответ → следующий вопрос → или финализировать
  const handleRegistrationAnswer = async (answer: string) => {
    if (regStep < 0 || regStep >= REG_STEPS.length || !sessionId) return
    const step = REG_STEPS[regStep]
    pushUser(answer)
    setInput('')
    const merged: Partial<CollectedData> = { ...regAnswers, [step.key]: answer }
    setRegAnswers(merged)

    const nextIdx = regStep + 1
    if (nextIdx < REG_STEPS.length) {
      setRegStep(nextIdx)
      pushAssistant(REG_STEPS[nextIdx].prompt)
      return
    }

    // Все шаги пройдены — отправляем профиль и выдаём JWT
    setRegStep(REG_STEPS.length)
    setLoading(true)
    try {
      const session = await collectProfile(sessionId, merged as CollectedData)
      pushAssistant(
        `Спасибо, ${session.collected_data?.name || answer}! Профиль создан, регистрация завершена.`,
      )
      try {
        const tokens = await exchangeForTokens(sessionId)
        setAuth(
          { id: tokens.client_profile_id, name: tokens.name },
          tokens.access,
          tokens.refresh,
        )
        toast.show({
          kind: 'success',
          title: 'Регистрация успешна',
          description: 'Открываем тарифы…',
        })
        navigate('/tariffs')
        onClose()
      } catch (err) {
        console.warn('auth-token failed', err)
        toast.show({
          kind: 'error',
          title: 'Не удалось завершить вход',
          description: apiErrorMessage(err, 'Попробуйте ещё раз позже.'),
        })
      }
    } catch (err) {
      toast.show({
        kind: 'error',
        title: 'Не удалось сохранить профиль',
        description: apiErrorMessage(err, 'Ошибка сохранения'),
      })
      // откатываем шаг — даём возможность переответить
      setRegStep(REG_STEPS.length - 1)
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  const isQuestionnaireMode = currentQuestion !== null
  const progress = currentQuestion?.progress
  const progressPct =
    progress && progress.total > 0 ? Math.round(((progress.done + 1) / progress.total) * 100) : 0

  // В режиме регистрации показываем тот же progress-bar
  const isRegistering = regStep >= 0 && regStep < REG_STEPS.length
  const regProgressPct = isRegistering
    ? Math.round(((regStep + 1) / REG_STEPS.length) * 100)
    : 0
  const regCurrentStep = isRegistering ? REG_STEPS[regStep] : null

  return (
    <div
      className="fixed inset-0 z-[1200] flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm p-0 sm:p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full sm:max-w-lg h-[100svh] sm:h-[min(700px,90vh)] bg-white sm:rounded-3xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex-shrink-0 flex items-center justify-between gap-3 px-5 py-4 border-b border-ink-100 bg-gradient-to-r from-ink-900 to-ink-800 text-white">
          <div className="flex items-center gap-3">
            <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-brand-600 shadow-lg">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 8V4H8" strokeLinecap="round" strokeLinejoin="round" />
                <rect x="4" y="8" width="16" height="12" rx="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 14h2M20 14h2M15 13v2M9 13v2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 ring-2 ring-ink-800" />
            </span>
            <div>
              <p className="text-sm font-semibold">{config?.name ?? 'Baqsy AI'}</p>
              <p className="text-xs text-ink-300">
                {isQuestionnaireMode
                  ? 'Анкета Digital Baqsylyq'
                  : isRegistering
                  ? 'Регистрация'
                  : 'Онлайн • отвечает мгновенно'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Закрыть"
          >
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </header>

        {isQuestionnaireMode && progress && (
          <div className="flex-shrink-0 px-5 py-2 bg-ink-50 border-b border-ink-100">
            <div className="flex justify-between text-[11px] font-semibold text-ink-600 uppercase tracking-wide mb-1">
              <span className="truncate pr-2">{currentQuestion?.stage || 'Вопрос'}</span>
              <span className="tabular-nums flex-shrink-0">
                {progress.done + 1} / {progress.total}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-ink-200 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-400 to-brand-600 rounded-full transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}

        {isRegistering && regCurrentStep && (
          <div className="flex-shrink-0 px-5 py-2 bg-ink-50 border-b border-ink-100">
            <div className="flex justify-between text-[11px] font-semibold text-ink-600 uppercase tracking-wide mb-1">
              <span className="truncate pr-2">{regCurrentStep.label}</span>
              <span className="tabular-nums flex-shrink-0">
                {regStep + 1} / {REG_STEPS.length}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-ink-200 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-400 to-brand-600 rounded-full transition-all duration-500"
                style={{ width: `${regProgressPct}%` }}
              />
            </div>
          </div>
        )}

        <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-5 space-y-3 bg-ink-50/40">
          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role}>
              {m.content}
            </MessageBubble>
          ))}
          {loading && (
            <MessageBubble role="assistant">
              <TypingDots />
            </MessageBubble>
          )}
        </div>

        {/* Quick replies — только в свободном чате до регистрации */}
        {!isQuestionnaireMode && !isRegistering && quickReplies.length > 0 && (
          <div className="flex-shrink-0 px-4 py-2 flex flex-wrap gap-2 bg-white border-t border-ink-100">
            {quickReplies.map((qr) => (
              <button
                key={qr.label}
                onClick={() => handleQuickReply(qr)}
                className="px-3 py-1.5 rounded-full text-xs font-semibold bg-ink-100 text-ink-700 hover:bg-brand-100 hover:text-brand-800 transition-colors"
              >
                {qr.label}
              </button>
            ))}
          </div>
        )}

        {/* Режим анкеты после оплаты */}
        {isQuestionnaireMode && currentQuestion && !loading && (
          <QuestionnaireInput
            question={currentQuestion}
            multichoicePicked={multichoicePicked}
            onMultichoiceChange={setMultichoicePicked}
            onSubmit={sendContent}
          />
        )}

        {/* Режим регистрации (Этапы I + II) */}
        {isRegistering && regCurrentStep && !loading && (
          <RegistrationInput
            step={regCurrentStep}
            onSubmit={handleRegistrationAnswer}
            input={input}
            setInput={setInput}
          />
        )}

        {/* CTA «Зарегистрироваться» — для гостей до старта рег-флоу */}
        {!isQuestionnaireMode && !isRegistering && !isAuthenticated && (
          <div className="flex-shrink-0 px-4 pt-3 pb-1 bg-white border-t border-ink-100">
            <button
              onClick={startRegistration}
              className="text-xs font-semibold text-brand-700 hover:text-brand-600 flex items-center gap-1"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" />
              </svg>
              Пройти регистрацию
            </button>
          </div>
        )}

        {/* Свободный чат — текстовый инпут */}
        {!isQuestionnaireMode && !isRegistering && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              sendContent(input)
            }}
            className="flex-shrink-0 flex gap-2 p-3 bg-white border-t border-ink-100"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Напишите сообщение…"
              disabled={loading}
              className="flex-1 px-4 py-2.5 rounded-xl border border-ink-200 text-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200 disabled:bg-ink-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-ink-900 text-white hover:bg-ink-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Отправить"
            >
              <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" />
              </svg>
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

function prefixStage(q: QuestionPayload): string {
  return q.stage ? `[${q.stage}] ${q.text}` : q.text
}

function RegistrationInput({
  step,
  onSubmit,
  input,
  setInput,
}: {
  step: RegStep
  onSubmit: (answer: string) => void
  input: string
  setInput: (v: string) => void
}) {
  if (step.type === 'choice') {
    return (
      <div className="flex-shrink-0 p-3 bg-white border-t border-ink-100 flex flex-wrap gap-2">
        {(step.choices ?? []).map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => onSubmit(c)}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-b from-brand-400 to-brand-500 text-ink-950 shadow-sm hover:from-brand-300 hover:to-brand-400 transition-colors"
          >
            {c}
          </button>
        ))}
      </div>
    )
  }
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        const v = input.trim()
        if (v) onSubmit(v)
      }}
      className="flex-shrink-0 flex gap-2 p-3 bg-white border-t border-ink-100"
    >
      <input
        type="text"
        autoFocus
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={step.placeholder || 'Ваш ответ…'}
        className="flex-1 px-4 py-2.5 rounded-xl border border-ink-200 text-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
      />
      <button
        type="submit"
        disabled={!input.trim()}
        className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-ink-900 text-white hover:bg-ink-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        aria-label="Ответить"
      >
        <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" />
        </svg>
      </button>
    </form>
  )
}

function QuestionnaireInput({
  question,
  multichoicePicked,
  onMultichoiceChange,
  onSubmit,
}: {
  question: QuestionPayload
  multichoicePicked: string[]
  onMultichoiceChange: (v: string[]) => void
  onSubmit: (content: string | string[]) => void
}) {
  const [text, setText] = useState('')

  // Reset local text when question changes — canonical useEffect use case:
  // syncing UI state with an external identity change.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setText('')
    onMultichoiceChange([])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question.question_id])

  const ft = question.field_type

  if (ft === 'choice') {
    return (
      <div className="flex-shrink-0 p-3 bg-white border-t border-ink-100 flex flex-wrap gap-2">
        {question.choices.map((c) => (
          <button
            key={c}
            onClick={() => onSubmit(c)}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-b from-brand-400 to-brand-500 text-ink-950 shadow-sm hover:from-brand-300 hover:to-brand-400 transition-colors"
          >
            {c}
          </button>
        ))}
      </div>
    )
  }

  if (ft === 'multichoice') {
    const toggle = (c: string) => {
      onMultichoiceChange(
        multichoicePicked.includes(c)
          ? multichoicePicked.filter((x) => x !== c)
          : [...multichoicePicked, c],
      )
    }
    return (
      <div className="flex-shrink-0 p-3 bg-white border-t border-ink-100 space-y-2">
        <div className="flex flex-wrap gap-2">
          {question.choices.map((c) => {
            const picked = multichoicePicked.includes(c)
            return (
              <button
                key={c}
                type="button"
                onClick={() => toggle(c)}
                className={cn(
                  'px-3 py-2 rounded-xl text-sm font-semibold transition-colors',
                  picked
                    ? 'bg-brand-500 text-white'
                    : 'bg-ink-100 text-ink-700 hover:bg-ink-200',
                )}
              >
                {picked ? '✓ ' : ''}
                {c}
              </button>
            )
          })}
        </div>
        <button
          type="button"
          disabled={multichoicePicked.length === 0}
          onClick={() => onSubmit(multichoicePicked)}
          className="w-full px-4 py-2.5 rounded-xl bg-ink-900 text-white text-sm font-semibold hover:bg-ink-800 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Ответить ({multichoicePicked.length} выбрано)
        </button>
      </div>
    )
  }

  const multiline = ft === 'longtext'
  const inputType = ft === 'number' ? 'number' : ft === 'url' ? 'url' : 'text'

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (text.trim()) onSubmit(text.trim())
      }}
      className="flex-shrink-0 flex gap-2 p-3 bg-white border-t border-ink-100"
    >
      {multiline ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={question.placeholder || 'Ваш ответ…'}
          rows={3}
          className="flex-1 px-4 py-2.5 rounded-xl border border-ink-200 text-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200 resize-none"
        />
      ) : (
        <input
          type={inputType}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={question.placeholder || 'Ваш ответ…'}
          className="flex-1 px-4 py-2.5 rounded-xl border border-ink-200 text-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
      )}
      <button
        type="submit"
        disabled={!text.trim()}
        className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-ink-900 text-white hover:bg-ink-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors self-end"
        aria-label="Ответить"
      >
        <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" />
        </svg>
      </button>
    </form>
  )
}

function MessageBubble({ role, children }: { role: 'user' | 'assistant'; children: React.ReactNode }) {
  const isUser = role === 'user'
  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[82%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap',
          isUser
            ? 'bg-ink-900 text-white rounded-br-md'
            : 'bg-white text-ink-900 border border-ink-100 rounded-bl-md shadow-sm',
        )}
      >
        {children}
      </div>
    </div>
  )
}

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-0.5">
      <span className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  )
}
