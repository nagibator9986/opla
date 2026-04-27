import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Container } from '../components/ui/Container'
import { Logo } from '../components/ui/Logo'
import {
  getInviteContext,
  submitInviteAnswer,
  type InviteContext,
  type InviteQuestion,
} from '../api/invite'
import { cn } from '../lib/cn'

export function InvitePage() {
  const { token } = useParams<{ token: string }>()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['invite', token],
    queryFn: () => getInviteContext(token!),
    enabled: !!token,
    retry: 1,
  })

  if (isLoading) {
    return <FullScreen><PageSkeleton /></FullScreen>
  }
  if (isError || !data) {
    return (
      <FullScreen>
        <ErrorBlock
          title="Ссылка недействительна"
          message="Возможно, она была отозвана или истёк срок. Попросите инициатора прислать новую."
        />
      </FullScreen>
    )
  }

  // Уже завершено?
  if (data.completed && data.participant.status === 'completed') {
    return (
      <FullScreen>
        <SuccessBlock
          title="Спасибо! Анкета уже отправлена."
          message={
            data.thanks ??
            'Ваши ответы сохранены. Эксперт Baqsy использует их для составления отчёта.'
          }
        />
      </FullScreen>
    )
  }

  return <Runner token={token!} initial={data} />
}

function Runner({ token, initial }: { token: string; initial: InviteContext }) {
  const [current, setCurrent] = useState<InviteQuestion | null>(
    initial.next_question ?? initial.first_question ?? null,
  )
  const [progress, setProgress] = useState(initial.progress)
  const [intro, setIntro] = useState<string | null>(initial.intro ?? null)
  const [completed, setCompleted] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [errorText, setErrorText] = useState<string | null>(null)

  if (completed) {
    return (
      <FullScreen>
        <SuccessBlock
          title="Анкета завершена"
          message={completed}
        />
      </FullScreen>
    )
  }

  const submit = async (raw: string | string[]) => {
    if (!current) return
    setSubmitting(true)
    setErrorText(null)
    try {
      const payload =
        Array.isArray(raw)
          ? { question_id: current.question_id, values: raw }
          : { question_id: current.question_id, value: raw }
      const resp = await submitInviteAnswer(token, payload)
      setIntro(null)
      if (resp.completed && resp.thanks) {
        setCompleted(resp.thanks)
        return
      }
      if (resp.next_question) {
        setCurrent(resp.next_question)
        setProgress(resp.next_question.progress)
      } else if (resp.completed) {
        setCompleted('Спасибо! Ваши ответы сохранены.')
      }
    } catch (err: unknown) {
      setErrorText(
        err instanceof Error
          ? err.message
          : 'Не удалось сохранить ответ. Проверьте интернет и попробуйте ещё раз.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  const totalDone = progress.done
  const totalAll = progress.total || 1
  const pct = Math.round(((totalDone + 1) / totalAll) * 100)

  return (
    <div className="min-h-screen bg-ink-50 flex flex-col">
      <header className="bg-gradient-to-r from-ink-900 to-ink-800 text-white">
        <Container className="flex items-center justify-between py-4">
          <Logo variant="light" />
          <div className="text-right">
            <p className="text-xs text-ink-300 uppercase tracking-wide">Участник</p>
            <p className="text-sm font-semibold">{initial.participant.name}</p>
          </div>
        </Container>
      </header>

      <Container size="sm" className="py-10 flex-1">
        {intro && (
          <div className="mb-8 p-5 rounded-2xl bg-white border border-ink-200 shadow-sm">
            <p className="text-ink-700 leading-relaxed whitespace-pre-wrap">{intro}</p>
          </div>
        )}

        {current && (
          <div className="bg-white rounded-2xl border border-ink-200 p-6 md:p-8 shadow-sm">
            <div className="flex justify-between text-[11px] font-semibold text-ink-500 uppercase tracking-wide mb-2">
              <span className="truncate pr-2">{current.stage || 'Вопрос'}</span>
              <span className="tabular-nums flex-shrink-0">
                {totalDone + 1} / {totalAll}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-ink-100 overflow-hidden mb-6">
              <div
                className="h-full bg-gradient-to-r from-brand-400 to-brand-600 rounded-full transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>

            <h2 className="text-xl md:text-2xl font-bold text-ink-900 leading-snug mb-6">
              {current.text}
            </h2>

            {errorText && (
              <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
                {errorText}
              </div>
            )}

            <Input
              key={current.question_id}
              question={current}
              submitting={submitting}
              onSubmit={submit}
            />
          </div>
        )}

        <div className="mt-8 text-center text-xs text-ink-500 leading-relaxed">
          Ваши ответы конфиденциальны и используются только для составления
          консолидированного отчёта по компании. Эксперты Baqsy не передают
          индивидуальные ответы инициатору группы.
        </div>
      </Container>

      <footer className="py-6 border-t border-ink-200 bg-white">
        <Container className="text-center text-xs text-ink-500">
          © {new Date().getFullYear()} Baqsy System · Digital Baqsylyq
        </Container>
      </footer>
    </div>
  )
}

function Input({
  question,
  submitting,
  onSubmit,
}: {
  question: InviteQuestion
  submitting: boolean
  onSubmit: (raw: string | string[]) => void
}) {
  const [value, setValue] = useState('')
  const [multiPicked, setMultiPicked] = useState<string[]>([])
  const onMultiToggle = (c: string) =>
    setMultiPicked((prev) => (prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]))
  const ft = question.field_type

  if (ft === 'choice') {
    return (
      <div className="grid sm:grid-cols-2 gap-2">
        {question.choices.map((c) => (
          <button
            key={c}
            disabled={submitting}
            onClick={() => onSubmit(c)}
            className="px-4 py-3 rounded-xl text-sm font-semibold bg-gradient-to-b from-brand-400 to-brand-500 text-ink-950 shadow-sm hover:from-brand-300 hover:to-brand-400 disabled:opacity-50"
          >
            {c}
          </button>
        ))}
      </div>
    )
  }

  if (ft === 'multichoice') {
    return (
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {question.choices.map((c) => {
            const picked = multiPicked.includes(c)
            return (
              <button
                key={c}
                type="button"
                onClick={() => onMultiToggle(c)}
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
          disabled={multiPicked.length === 0 || submitting}
          onClick={() => onSubmit(multiPicked)}
          className="w-full px-4 py-3 rounded-xl bg-ink-900 text-white text-sm font-semibold hover:bg-ink-800 disabled:opacity-40"
        >
          Ответить ({multiPicked.length} выбрано)
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
        if (value.trim()) onSubmit(value.trim())
      }}
      className="space-y-3"
    >
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={question.placeholder || 'Ваш ответ…'}
          rows={5}
          className="w-full px-4 py-3 rounded-xl border border-ink-200 text-base focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200 resize-none"
        />
      ) : (
        <input
          type={inputType}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={question.placeholder || 'Ваш ответ…'}
          className="w-full px-4 py-3 rounded-xl border border-ink-200 text-base focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
      )}
      <button
        type="submit"
        disabled={!value.trim() || submitting}
        className="w-full px-4 py-3 rounded-xl bg-ink-900 text-white text-sm font-semibold hover:bg-ink-800 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting ? 'Сохраняем…' : 'Ответить и продолжить'}
      </button>
    </form>
  )
}

function FullScreen({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-ink-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">{children}</div>
    </div>
  )
}

function PageSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-6 bg-ink-200 rounded w-32 mx-auto" />
      <div className="h-10 bg-ink-200 rounded" />
      <div className="h-5 bg-ink-200 rounded w-3/4" />
      <div className="h-32 bg-ink-200 rounded" />
    </div>
  )
}

function ErrorBlock({ title, message }: { title: string; message: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-xl border border-rose-100 p-8 text-center">
      <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-rose-100 text-rose-600 mb-4">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-ink-900 mb-2">{title}</h1>
      <p className="text-ink-600 leading-relaxed">{message}</p>
    </div>
  )
}

function SuccessBlock({ title, message }: { title: string; message: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-xl border border-emerald-100 p-8 text-center">
      <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-600 mb-4">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-ink-900 mb-2">{title}</h1>
      <p className="text-ink-600 leading-relaxed">{message}</p>
    </div>
  )
}
