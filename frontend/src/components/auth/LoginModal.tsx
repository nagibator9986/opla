import { useEffect, useState } from 'react'
import { requestLoginLink } from '../../api/auth'
import { apiErrorMessage } from '../../lib/apiError'
import { cn } from '../../lib/cn'

interface LoginModalProps {
  open: boolean
  onClose: () => void
}

export function LoginModal({ open, onClose }: LoginModalProps) {
  const [phone, setPhone] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [debugUrl, setDebugUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  // Reset on close
  useEffect(() => {
    if (open) return
    const t = setTimeout(() => {
      setPhone('')
      setDone(false)
      setDebugUrl(null)
      setError(null)
      setSubmitting(false)
    }, 300)
    return () => clearTimeout(t)
  }, [open])

  if (!open) return null

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (submitting) return
    setError(null)
    setSubmitting(true)
    try {
      const resp = await requestLoginLink(phone)
      setDone(true)
      setDebugUrl(resp.debug_url ?? null)
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось отправить ссылку. Попробуйте позже.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[1100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-title"
    >
      <div
        className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 inline-flex items-center justify-center w-9 h-9 rounded-full text-ink-500 hover:text-ink-900 hover:bg-ink-100 transition-colors"
          aria-label="Закрыть"
        >
          <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>

        <div className="p-7 md:p-8">
          {!done ? (
            <>
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-brand-100 text-brand-700 mb-4">
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h2 id="login-title" className="text-xl md:text-2xl font-bold text-ink-900 mb-2">
                Войти в кабинет
              </h2>
              <p className="text-sm text-ink-600 leading-relaxed mb-5">
                Введите номер WhatsApp, который вы указывали при регистрации. Мы
                отправим одноразовую ссылку для входа.
              </p>

              <form onSubmit={submit} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-ink-700 uppercase tracking-wide mb-1.5">
                    Номер WhatsApp
                  </label>
                  <input
                    type="tel"
                    inputMode="tel"
                    autoFocus
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+7 700 123 45 67"
                    className="w-full px-4 py-3 rounded-xl border border-ink-200 text-base focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
                    required
                  />
                </div>
                {error && (
                  <p className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">
                    {error}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={submitting || !phone.trim()}
                  className={cn(
                    'w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-ink-900 text-white text-base font-semibold hover:bg-ink-800 transition-colors',
                    (submitting || !phone.trim()) && 'opacity-50 cursor-not-allowed',
                  )}
                >
                  {submitting ? 'Отправляем…' : 'Получить ссылку в WhatsApp'}
                </button>
              </form>

              <p className="mt-5 text-xs text-ink-500">
                Если вы ещё не регистрировались — нажмите «Открыть Baqsy AI» и
                пройдите быструю анкету в чате.
              </p>
            </>
          ) : (
            <>
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 mb-4">
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M22 4L12 14.01l-3-3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-ink-900 mb-2">
                Если номер зарегистрирован — ссылка отправлена
              </h2>
              <p className="text-sm text-ink-600 leading-relaxed mb-5">
                Откройте WhatsApp на своём устройстве — придёт сообщение с
                кнопкой входа. Ссылка действует 15 минут.
              </p>
              {debugUrl && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 text-xs text-amber-900 break-all">
                  <p className="font-semibold mb-1">DEBUG fallback (WhatsApp канал не настроен):</p>
                  <a
                    href={debugUrl}
                    className="underline font-mono"
                  >
                    {debugUrl}
                  </a>
                </div>
              )}
              <button
                onClick={onClose}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-ink-100 text-ink-800 text-base font-semibold hover:bg-ink-200 transition-colors"
              >
                Закрыть
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
