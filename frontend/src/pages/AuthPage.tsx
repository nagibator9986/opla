import { useEffect, useState } from 'react'
import { AxiosError } from 'axios'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { exchangeDeeplink } from '../api/auth'
import { Logo } from '../components/ui/Logo'
import { Button } from '../components/ui/Button'

type AuthStatus = 'loading' | 'error' | 'network_error' | 'invalid_link'

export function AuthPage() {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [status, setStatus] = useState<AuthStatus>(uuid ? 'loading' : 'invalid_link')

  useEffect(() => {
    if (!uuid) return
    exchangeDeeplink(uuid)
      .then(({ access, refresh, client_profile_id, name }) => {
        setAuth({ id: client_profile_id, name }, access, refresh)
        navigate('/cabinet', { replace: true })
      })
      .catch((err: unknown) => {
        if (err instanceof AxiosError) {
          if (!err.response) {
            setStatus('network_error')
            return
          }
          if (err.response.status === 404) {
            setStatus('invalid_link')
            return
          }
        }
        setStatus('error')
      })
  }, [uuid, setAuth, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-ink-50 via-white to-brand-50 px-4 relative overflow-hidden">
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgb(245_158_11_/_0.08),transparent_50%)]"
      />
      <div className="relative w-full max-w-md">
        <div className="flex justify-center mb-8">
          <Logo variant="dark" />
        </div>
        <div className="bg-white rounded-2xl shadow-[0_10px_20px_rgb(15_23_42_/_0.05),0_24px_48px_rgb(15_23_42_/_0.1)] p-8 text-center border border-ink-100">
          {status === 'loading' && <LoadingView />}
          {status === 'invalid_link' && <InvalidLinkView />}
          {status === 'network_error' && <NetworkErrorView onRetry={() => window.location.reload()} />}
          {status === 'error' && <GenericErrorView />}
        </div>
        <p className="mt-6 text-center text-xs text-ink-500">
          &copy; {new Date().getFullYear()} Baqsy System
        </p>
      </div>
    </div>
  )
}

function LoadingView() {
  return (
    <>
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-100 text-brand-600 mb-5">
        <svg className="animate-spin w-7 h-7" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-ink-900 mb-2">Входим в кабинет…</h1>
      <p className="text-ink-500 text-sm">Проверяем ссылку и подготавливаем доступ.</p>
    </>
  )
}

function InvalidLinkView() {
  return (
    <>
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-rose-100 text-rose-600 mb-5">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-ink-900 mb-2">Ссылка недействительна</h1>
      <p className="text-ink-600 text-sm mb-6">
        Срок действия ссылки — 30 минут. Запросите новую в Telegram-боте.
      </p>
      <a href="https://t.me/Baqsysystembot" target="_blank" rel="noopener noreferrer">
        <Button variant="primary" fullWidth>
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z" />
          </svg>
          Запросить новую ссылку
        </Button>
      </a>
    </>
  )
}

function NetworkErrorView({ onRetry }: { onRetry: () => void }) {
  return (
    <>
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-100 text-amber-600 mb-5">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="1" y1="1" x2="23" y2="23" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M16.72 11.06A10.94 10.94 0 0119 12.55" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M5 12.55a10.94 10.94 0 015.17-2.39" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="12" y1="20" x2="12.01" y2="20" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-ink-900 mb-2">Нет соединения</h1>
      <p className="text-ink-600 text-sm mb-6">
        Проверьте интернет и попробуйте снова.
      </p>
      <Button variant="primary" fullWidth onClick={onRetry}>
        Попробовать снова
      </Button>
    </>
  )
}

function GenericErrorView() {
  return (
    <>
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-rose-100 text-rose-600 mb-5">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="12" y1="9" x2="12" y2="13" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="12" y1="17" x2="12.01" y2="17" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-ink-900 mb-2">Что-то пошло не так</h1>
      <p className="text-ink-600 text-sm mb-6">
        Попробуйте запросить новую ссылку в Telegram-боте.
      </p>
      <a href="https://t.me/Baqsysystembot" target="_blank" rel="noopener noreferrer">
        <Button variant="primary" fullWidth>
          Перейти в Telegram-бот
        </Button>
      </a>
    </>
  )
}
