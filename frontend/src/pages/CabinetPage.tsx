import { useNavigate } from 'react-router-dom'
import { Header } from '../components/layout/Header'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { StatusProgress } from '../components/cabinet/StatusProgress'
import { PdfDownloadButton } from '../components/cabinet/PdfDownloadButton'
import { UpsellCard } from '../components/cabinet/UpsellCard'
import { useSubmission } from '../hooks/useSubmission'
import { useAuthStore } from '../store/authStore'

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function CabinetPage() {
  const navigate = useNavigate()
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const clientProfile = useAuthStore((s) => s.clientProfile)
  const { data: submission, isLoading, isError } = useSubmission()

  const handleLogout = () => {
    clearAuth()
    navigate('/', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="max-w-3xl mx-auto px-4 pt-24 pb-12">
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Личный кабинет</h1>
            {clientProfile?.name && (
              <p className="text-slate-500 mt-1">Здравствуйте, {clientProfile.name}</p>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Выйти
          </Button>
        </div>

        {isLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-2xl p-6 animate-pulse">
                <div className="h-4 bg-slate-200 rounded w-1/3 mb-3" />
                <div className="h-4 bg-slate-200 rounded w-2/3" />
              </div>
            ))}
          </div>
        )}

        {!isLoading && (isError || !submission) && (
          <Card>
            <p className="text-slate-600 mb-3">Нет активных заказов. Начните с Telegram-бота.</p>
            <a href="https://t.me/baqsy_bot" className="text-amber-600 hover:text-amber-700 underline text-sm">
              Перейти в бот
            </a>
          </Card>
        )}

        {!isLoading && !isError && submission && (
          <div className="space-y-6">
            {/* Order info card */}
            <Card>
              <h2 className="text-base font-semibold text-slate-900 mb-3">Информация о заказе</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-500">Отрасль</dt>
                  <dd className="font-medium text-slate-900">{submission.industry_name || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Анкета</dt>
                  <dd className="font-medium text-slate-900">{submission.template_name || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Тариф</dt>
                  <dd className="font-medium text-slate-900">
                    {submission.tariff_code === 'ashide_1'
                      ? 'Ashide 1'
                      : submission.tariff_code === 'ashide_2'
                      ? 'Ashide 2'
                      : submission.tariff_code ?? '—'}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Дата создания</dt>
                  <dd className="font-medium text-slate-900">{formatDate(submission.created_at)}</dd>
                </div>
              </dl>
            </Card>

            {/* Status progress */}
            <Card>
              <h2 className="text-base font-semibold text-slate-900 mb-5">Статус заказа</h2>
              <StatusProgress status={submission.status} />
            </Card>

            {/* PDF download */}
            <Card>
              <h2 className="text-base font-semibold text-slate-900 mb-3">Ваш отчёт</h2>
              <PdfDownloadButton pdfUrl={submission.pdf_url} />
            </Card>

            {/* Upsell */}
            <UpsellCard
              submissionId={submission.id}
              tariffCode={submission.tariff_code}
              status={submission.status}
            />
          </div>
        )}
      </main>
    </div>
  )
}
