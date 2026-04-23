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

export function ChatWidget({ open, onClose, autoStartQuestionnaireFor }: ChatWidgetProps) {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const toast = useToast()
  const [sessionId, setSessionId] = useState<string | null>(loadSessionId())
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([])
  const [currentQuestion, setCurrentQuestion] = useState<QuestionPayload | null>(null)
  const [multichoicePicked, setMultichoicePicked] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [formVisible, setFormVisible] = useState(false)
  const [form, setForm] = useState<CollectedData>({})
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
        const msg = err instanceof Error ? err.message : 'Не удалось начать анкету.'
        toast.show({ kind: 'error', title: 'Ошибка', description: msg })
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

  const pushUser = (text: string) => {
    setMessages((prev) => [...prev, { id: nextId('u'), role: 'user', content: text }])
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
      const message = err instanceof Error ? err.message : 'AI-ассистент временно недоступен.'
      pushAssistant(message)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickReply = (qr: QuickReply) => {
    sendContent(qr.payload)
  }

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sessionId) return
    if (!form.name || !form.company) {
      toast.show({
        kind: 'info',
        title: 'Заполните имя и компанию',
        description: 'Остальные поля можно оставить пустыми — уточним в чате.',
      })
      return
    }
    setLoading(true)
    try {
      const session = await collectProfile(sessionId, form)
      pushAssistant(
        `Спасибо, ${session.collected_data.name}! Профиль создан. Сейчас я выдам ссылку для оплаты.`,
      )
      setFormVisible(false)
      try {
        const tokens = await exchangeForTokens(sessionId)
        setAuth(
          { id: tokens.client_profile_id, name: tokens.name },
          tokens.access,
          tokens.refresh,
        )
        toast.show({ kind: 'success', title: 'Профиль создан', description: 'Выбираем тариф…' })
        navigate('/tariffs')
        onClose()
      } catch (err) {
        console.warn('auth-token failed', err)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка'
      toast.show({ kind: 'error', title: 'Не удалось сохранить', description: message })
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  const isQuestionnaireMode = currentQuestion !== null
  const progress = currentQuestion?.progress
  const progressPct =
    progress && progress.total > 0 ? Math.round(((progress.done + 1) / progress.total) * 100) : 0

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
                {isQuestionnaireMode ? 'Анкета Digital Baqsylyq' : 'Онлайн • отвечает мгновенно'}
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

        {!formVisible && !isQuestionnaireMode && quickReplies.length > 0 && (
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

        {isQuestionnaireMode && currentQuestion && !loading && (
          <QuestionnaireInput
            question={currentQuestion}
            multichoicePicked={multichoicePicked}
            onMultichoiceChange={setMultichoicePicked}
            onSubmit={sendContent}
          />
        )}

        {!isQuestionnaireMode && formVisible && (
          <form
            onSubmit={handleFormSubmit}
            className="flex-shrink-0 p-4 border-t border-ink-100 bg-white space-y-3"
          >
            <p className="text-sm font-semibold text-ink-900">Давайте заполним профиль</p>
            <div className="grid grid-cols-2 gap-2">
              <FormField label="Имя *" value={form.name ?? ''} onChange={(v) => setForm({ ...form, name: v })} />
              <FormField label="Компания *" value={form.company ?? ''} onChange={(v) => setForm({ ...form, company: v })} />
              <FormField label="Город" value={form.city ?? ''} onChange={(v) => setForm({ ...form, city: v })} />
              <FormField label="WhatsApp" value={form.phone_wa ?? ''} onChange={(v) => setForm({ ...form, phone_wa: v })} placeholder="+7 777…" />
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFormVisible(false)}
                className="flex-1 px-4 py-2.5 rounded-xl border border-ink-200 text-sm font-semibold text-ink-700 hover:bg-ink-50"
              >
                Назад
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2.5 rounded-xl bg-ink-900 text-white text-sm font-semibold hover:bg-ink-800 disabled:opacity-50"
              >
                Сохранить и к тарифу
              </button>
            </div>
          </form>
        )}

        {!isQuestionnaireMode && !formVisible && (
          <>
            <div className="flex-shrink-0 px-4 pt-3 pb-1 bg-white border-t border-ink-100">
              <button
                onClick={() => setFormVisible(true)}
                className="text-xs font-semibold text-brand-700 hover:text-brand-600 flex items-center gap-1"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" />
                </svg>
                Быстро заполнить профиль и перейти к оплате
              </button>
            </div>
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
          </>
        )}
      </div>
    </div>
  )
}

function prefixStage(q: QuestionPayload): string {
  return q.stage ? `[${q.stage}] ${q.text}` : q.text
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

function FormField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold text-ink-600 uppercase tracking-wide mb-1">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-lg border border-ink-200 text-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
      />
    </label>
  )
}
