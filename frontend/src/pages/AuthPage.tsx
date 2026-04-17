import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { exchangeDeeplink } from '../api/auth'

export function AuthPage() {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!uuid) {
      setError('Неверная ссылка.')
      setLoading(false)
      return
    }
    exchangeDeeplink(uuid)
      .then(({ access, refresh, client_profile_id, name }) => {
        setAuth({ id: client_profile_id, name }, access, refresh)
        navigate('/cabinet', { replace: true })
      })
      .catch(() => {
        setError('Ссылка истекла или недействительна. Запросите новую в боте.')
        setLoading(false)
      })
  }, [uuid, setAuth, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full mx-4 text-center">
        {loading && !error && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto mb-4" />
            <p className="text-slate-600 text-lg">Авторизация...</p>
          </>
        )}
        {error && (
          <>
            <div className="text-red-500 text-5xl mb-4">!</div>
            <p className="text-slate-800 text-lg mb-4">{error}</p>
            <a href="https://t.me/baqsy_bot" className="text-amber-600 hover:text-amber-700 underline">
              Перейти в бот
            </a>
          </>
        )}
      </div>
    </div>
  )
}
