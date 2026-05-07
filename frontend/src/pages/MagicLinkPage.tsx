import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'

import { Header } from '../components/layout/Header'
import { Container } from '../components/ui/Container'
import { verifyMagicLink } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { apiErrorMessage } from '../lib/apiError'

type State = 'loading' | 'success' | 'error'

export function MagicLinkPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [state, setState] = useState<State>('loading')
  const [error, setError] = useState<string>('')

  useEffect(() => {
    let cancelled = false
    if (!token) {
      // Async-set чтобы не нарушать react-hooks/set-state-in-effect.
      Promise.resolve().then(() => {
        if (cancelled) return
        setState('error')
        setError('Не указан токен ссылки.')
      })
      return () => {
        cancelled = true
      }
    }
    ;(async () => {
      try {
        const resp = await verifyMagicLink(token)
        if (cancelled) return
        setAuth(
          { id: resp.client_profile_id, name: resp.name },
          resp.access,
          resp.refresh,
        )
        setState('success')
        setTimeout(() => {
          if (!cancelled) navigate('/cabinet', { replace: true })
        }, 1200)
      } catch (err) {
        if (cancelled) return
        setState('error')
        setError(apiErrorMessage(err, 'Ссылка недействительна или устарела.'))
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token, navigate, setAuth])

  return (
    <div className="flex flex-col min-h-screen bg-ink-50">
      <Header variant="solid" />
      <main className="flex-1 pt-24 pb-16 md:pt-28 flex items-center">
        <Container size="sm">
          <div className="bg-white rounded-3xl shadow-xl border border-ink-200 p-8 md:p-10 text-center max-w-md mx-auto">
            {state === 'loading' && (
              <>
                <div className="w-12 h-12 mx-auto rounded-full border-4 border-ink-200 border-t-brand-500 animate-spin mb-5" />
                <h1 className="text-xl font-bold text-ink-900 mb-2">
                  Проверяем ссылку…
                </h1>
                <p className="text-sm text-ink-600">Подождите пару секунд.</p>
              </>
            )}

            {state === 'success' && (
              <>
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-700 mb-4">
                  <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h1 className="text-xl md:text-2xl font-bold text-ink-900 mb-2">
                  Вы успешно вошли
                </h1>
                <p className="text-sm text-ink-600">
                  Перенаправляем в личный кабинет…
                </p>
              </>
            )}

            {state === 'error' && (
              <>
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-rose-100 text-rose-700 mb-4">
                  <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
                    <line x1="12" y1="8" x2="12" y2="12" strokeLinecap="round" strokeLinejoin="round" />
                    <line x1="12" y1="16" x2="12.01" y2="16" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h1 className="text-xl md:text-2xl font-bold text-ink-900 mb-2">
                  Не получилось войти
                </h1>
                <p className="text-sm text-ink-600 mb-6">{error}</p>
                <Link
                  to="/"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-ink-900 text-white text-sm font-semibold hover:bg-ink-800 transition-colors"
                >
                  На главную
                </Link>
              </>
            )}
          </div>
        </Container>
      </main>
    </div>
  )
}
