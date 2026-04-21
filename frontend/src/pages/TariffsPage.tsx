import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { useTariffs } from '../hooks/useTariffs'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Container } from '../components/ui/Container'
import { Badge } from '../components/ui/Badge'
import { TariffCard, TariffSkeleton } from '../components/tariff/TariffCard'
import api from '../api/axios'
import type { Submission } from '../types/api'

export function TariffsPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { data: tariffs, isLoading: tariffsLoading } = useTariffs()

  const { data: submission } = useQuery<Submission | null>({
    queryKey: ['my-submission'],
    queryFn: async () => {
      try {
        const { data } = await api.get<Submission>('/submissions/my/')
        return data
      } catch {
        return null
      }
    },
    enabled: isAuthenticated,
  })

  const visibleTariffs = tariffs?.filter((t) => t.code !== 'upsell') ?? []

  return (
    <div className="flex flex-col min-h-screen bg-ink-50">
      <Header variant="solid" />
      <main className="flex-1 pt-24 pb-16 md:pt-28">
        <Container size="md">
          <div className="text-center mb-10 md:mb-14">
            <Badge variant="brand" className="mb-4">Тарифы</Badge>
            <h1 className="text-3xl md:text-5xl font-bold text-ink-900 tracking-tight">
              Выберите глубину аудита
            </h1>
            <p className="mt-4 text-ink-600 text-base md:text-lg max-w-2xl mx-auto leading-relaxed">
              Базовый формат для быстрого старта или полный разбор для глубокого понимания бизнеса.
            </p>

            {!isAuthenticated && (
              <div className="mt-8 inline-flex flex-col sm:flex-row items-start sm:items-center gap-3 px-5 py-4 rounded-2xl bg-white border border-amber-200 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] max-w-xl mx-auto">
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
                  <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <p className="text-sm text-left text-ink-700">
                  Для оплаты сначала пройдите онбординг в{' '}
                  <a
                    href="https://t.me/Baqsysystembot"
                    className="font-semibold text-brand-700 hover:text-brand-600 underline underline-offset-2"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Telegram-боте @Baqsysystembot
                  </a>
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 max-w-4xl mx-auto">
            {tariffsLoading ? (
              <>
                <TariffSkeleton />
                <TariffSkeleton featured />
              </>
            ) : (
              visibleTariffs.map((tariff) => (
                <TariffCard
                  key={tariff.id}
                  tariff={tariff}
                  featured={tariff.code === 'ashide_2'}
                  submission={submission}
                />
              ))
            )}
          </div>

          <div className="mt-12 grid md:grid-cols-3 gap-4">
            {[
              {
                icon: (
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="5" width="18" height="14" rx="2" strokeLinecap="round" strokeLinejoin="round" />
                    <line x1="3" y1="10" x2="21" y2="10" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ),
                title: 'Безопасная оплата',
                text: 'CloudPayments KZ — лицензированный провайдер. 3-D Secure, HMAC-подпись.',
              },
              {
                icon: (
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
                    <polyline points="12 6 12 12 16 14" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ),
                title: 'Срок 3–5 дней',
                text: 'Эксперт готовит отчёт индивидуально под вашу отрасль и цели.',
              },
              {
                icon: (
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
                    <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ),
                title: 'Возврат денег',
                text: 'Если аудит не оправдал ожиданий — возвращаем 100% в течение 14 дней.',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-3 p-5 rounded-2xl bg-white border border-ink-200/70"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center">
                  {item.icon}
                </div>
                <div>
                  <p className="font-semibold text-sm text-ink-900">{item.title}</p>
                  <p className="text-sm text-ink-600 mt-0.5">{item.text}</p>
                </div>
              </div>
            ))}
          </div>
        </Container>
      </main>
      <Footer />
    </div>
  )
}
