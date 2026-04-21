import { Link, useNavigate } from 'react-router-dom'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Container } from '../components/ui/Container'
import { Badge } from '../components/ui/Badge'
import { StatusProgress } from '../components/cabinet/StatusProgress'
import { PdfDownloadButton } from '../components/cabinet/PdfDownloadButton'
import { UpsellCard } from '../components/cabinet/UpsellCard'
import { useSubmission } from '../hooks/useSubmission'
import { useAuthStore } from '../store/authStore'

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function tariffLabel(code: string | null): string {
  if (!code) return '—'
  if (code === 'ashide_1') return 'Ashide 1 (базовый)'
  if (code === 'ashide_2') return 'Ashide 2 (полный)'
  return code
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

  const answered = submission?.answered_count ?? 0
  const total = submission?.total_questions ?? 0
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0

  return (
    <div className="flex flex-col min-h-screen bg-ink-50">
      <Header variant="solid" />
      <main className="flex-1 pt-24 pb-16 md:pt-28">
        <Container size="md">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
            <div className="min-w-0">
              <Badge variant="neutral" size="sm" className="mb-2">Личный кабинет</Badge>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink-900 tracking-tight break-words">
                {clientProfile?.name ? `Здравствуйте, ${clientProfile.name}!` : 'Добро пожаловать'}
              </h1>
              <p className="mt-1 text-sm md:text-base text-ink-500">
                Следите за статусом заказа и скачайте отчёт, когда он будет готов.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={handleLogout} className="flex-shrink-0 self-start">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 4.25A2.25 2.25 0 015.25 2h5.5A2.25 2.25 0 0113 4.25v2a.75.75 0 01-1.5 0v-2a.75.75 0 00-.75-.75h-5.5a.75.75 0 00-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 00.75-.75v-2a.75.75 0 011.5 0v2A2.25 2.25 0 0110.75 18h-5.5A2.25 2.25 0 013 15.75V4.25z" clipRule="evenodd" />
                <path fillRule="evenodd" d="M19 10a.75.75 0 00-.22-.53l-2.5-2.5a.75.75 0 10-1.06 1.06l1.22 1.22H9a.75.75 0 000 1.5h7.44l-1.22 1.22a.75.75 0 101.06 1.06l2.5-2.5A.75.75 0 0019 10z" clipRule="evenodd" />
              </svg>
              Выйти
            </Button>
          </div>

          {isLoading && <LoadingState />}

          {!isLoading && (isError || !submission) && <EmptyState />}

          {!isLoading && !isError && submission && (
            <div className="space-y-6 animate-fade-in">
              <Card padding="lg">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold text-ink-900">Статус заказа</h2>
                    <p className="text-sm text-ink-500">
                      Средний срок выполнения аудита — 3–5 рабочих дней
                    </p>
                  </div>
                  <Badge variant="brand" size="md">
                    <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                    </svg>
                    Активный
                  </Badge>
                </div>
                <StatusProgress status={submission.status} />
              </Card>

              {submission.status === 'in_progress_full' && total > 0 && (
                <Card>
                  <div className="flex items-center justify-between gap-3 mb-3">
                    <div className="min-w-0">
                      <h3 className="text-base font-bold text-ink-900">Прогресс анкеты</h3>
                      <p className="text-sm text-ink-500">Отвечайте в Telegram-боте</p>
                    </div>
                    <span className="text-2xl font-bold text-brand-600 tabular-nums flex-shrink-0">
                      {answered}<span className="text-ink-300">/</span>{total}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-ink-100 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-brand-400 to-brand-500 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <a
                    href="https://t.me/Baqsysystembot"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-600 transition-colors"
                  >
                    Продолжить в Telegram
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </a>
                </Card>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <h3 className="text-base font-bold text-ink-900 mb-4">Информация о заказе</h3>
                  <dl className="space-y-3 text-sm">
                    <InfoRow label="Отрасль" value={submission.industry_name || '—'} />
                    <InfoRow label="Анкета" value={submission.template_name || '—'} />
                    <InfoRow label="Тариф" value={tariffLabel(submission.tariff_code)} />
                    <InfoRow label="Создан" value={formatDate(submission.created_at)} />
                    {submission.completed_at && (
                      <InfoRow label="Анкета завершена" value={formatDate(submission.completed_at)} />
                    )}
                  </dl>
                </Card>

                <Card>
                  <h3 className="text-base font-bold text-ink-900 mb-4">Ваш отчёт</h3>
                  <PdfDownloadButton pdfUrl={submission.pdf_url} />
                </Card>
              </div>

              <UpsellCard
                submissionId={submission.id}
                tariffCode={submission.tariff_code}
                status={submission.status}
              />
            </div>
          )}
        </Container>
      </main>
      <Footer />
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-ink-500">{label}</dt>
      <dd className="font-medium text-ink-900 text-right break-words">{value}</dd>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-white border border-ink-200 p-7 animate-pulse">
        <div className="h-5 bg-ink-200 rounded w-1/3 mb-4" />
        <div className="h-2 bg-ink-100 rounded-full mb-6" />
        <div className="grid grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 bg-ink-100 rounded" />
          ))}
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <div key={i} className="rounded-2xl bg-white border border-ink-200 p-6 animate-pulse">
            <div className="h-4 bg-ink-200 rounded w-1/2 mb-5" />
            <div className="space-y-2.5">
              <div className="h-4 bg-ink-100 rounded" />
              <div className="h-4 bg-ink-100 rounded w-5/6" />
              <div className="h-4 bg-ink-100 rounded w-4/6" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <Card padding="lg" className="text-center py-12">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-100 text-brand-700 mb-5">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 11l3 3L22 4" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h2 className="text-xl md:text-2xl font-bold text-ink-900 mb-2">
        Профиль создан. Осталось выбрать тариф.
      </h2>
      <p className="text-ink-600 mb-7 max-w-md mx-auto leading-relaxed">
        После оплаты Telegram-бот пришлёт первый вопрос отраслевой анкеты.
        Прохождение займёт 15–25 минут, можно прерывать и возвращаться.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link to="/tariffs">
          <Button variant="primary" size="lg" fullWidth>
            Выбрать тариф
            <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </Button>
        </Link>
        <a href="https://t.me/Baqsysystembot" target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="lg" fullWidth>
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z" />
            </svg>
            Открыть бот
          </Button>
        </a>
      </div>
    </Card>
  )
}
