import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { useTariffs } from '../hooks/useTariffs'
import { openPaymentWidget } from '../components/payment/openPaymentWidget'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import api from '../api/axios'
import type { Submission, Tariff } from '../types/api'

function formatPrice(price: string): string {
  return Number(price).toLocaleString('ru-RU') + ' ₸'
}

function TariffSkeleton() {
  return (
    <div className="rounded-2xl p-6 md:p-8 bg-white shadow-lg border border-slate-200 animate-pulse">
      <div className="h-6 bg-slate-200 rounded w-3/4 mb-4" />
      <div className="h-10 bg-slate-200 rounded w-1/2 mb-4" />
      <div className="h-4 bg-slate-200 rounded mb-2" />
      <div className="h-4 bg-slate-200 rounded w-5/6 mb-6" />
      <div className="h-12 bg-slate-200 rounded" />
    </div>
  )
}

interface TariffCardProps {
  tariff: Tariff
  highlight?: boolean
  submission?: Submission | null
}

function TariffCard({ tariff, highlight = false, submission }: TariffCardProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const clientProfile = useAuthStore((s) => s.clientProfile)

  const handlePay = () => {
    if (!isAuthenticated) {
      alert('Для оплаты начните с Telegram-бота: @baqsy_bot')
      return
    }
    const invoiceId = submission?.id ?? `tariff-${tariff.code}-${clientProfile?.id ?? 'unknown'}`
    openPaymentWidget(
      {
        publicId: import.meta.env.VITE_CLOUDPAYMENTS_PUBLIC_ID ?? '',
        amount: Number(tariff.price_kzt),
        currency: 'KZT',
        invoiceId,
        description: tariff.title,
        accountId: String(clientProfile?.id ?? ''),
        data: { tariff_code: tariff.code, submission_id: submission?.id },
      },
      () => {
        alert('Оплата прошла успешно! Перейдите в Telegram-бот для продолжения.')
      },
      (reason) => {
        console.error('Payment failed:', reason)
      },
    )
  }

  return (
    <Card highlight={highlight} className="flex flex-col">
      {highlight && (
        <div className="inline-flex items-center px-3 py-1 rounded-full bg-amber-500 text-white text-xs font-semibold mb-4 w-fit">
          Рекомендуем
        </div>
      )}
      <h3 className={`text-xl font-bold mb-2 ${highlight ? 'text-white' : 'text-slate-900'}`}>
        {tariff.title}
      </h3>
      <p className={`text-3xl font-bold mb-4 ${highlight ? 'text-amber-400' : 'text-slate-900'}`}>
        {formatPrice(tariff.price_kzt)}
      </p>
      <p className={`text-sm mb-6 flex-1 ${highlight ? 'text-slate-300' : 'text-slate-600'}`}>
        {tariff.description}
      </p>
      <Button
        variant={highlight ? 'secondary' : 'primary'}
        size="md"
        className="w-full"
        onClick={handlePay}
      >
        Оплатить
      </Button>
    </Card>
  )
}

export function TariffsPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { data: tariffs, isLoading: tariffsLoading } = useTariffs()

  const { data: submission } = useQuery<Submission | null>({
    queryKey: ['my-submission'],
    queryFn: async () => {
      const { data } = await api.get<Submission>('/submissions/my/')
      return data
    },
    enabled: isAuthenticated,
  })

  return (
    <div>
      <Header />
      <main className="pt-16 min-h-screen bg-slate-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center mb-14">
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Выберите тариф</h1>
            {!isAuthenticated && (
              <p className="text-slate-600 bg-amber-50 border border-amber-200 rounded-lg px-6 py-4 inline-block mt-4">
                Для оплаты начните с{' '}
                <a
                  href="https://t.me/baqsy_bot"
                  className="text-amber-600 font-semibold hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Telegram-бота @baqsy_bot
                </a>
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {tariffsLoading ? (
              <>
                <TariffSkeleton />
                <TariffSkeleton />
              </>
            ) : (
              tariffs?.map((tariff) => (
                <TariffCard
                  key={tariff.id}
                  tariff={tariff}
                  highlight={tariff.code === 'ashide_2'}
                  submission={submission}
                />
              ))
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}
