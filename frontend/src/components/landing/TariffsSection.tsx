import { useTariffs } from '../../hooks/useTariffs'
import { useAuthStore } from '../../store/authStore'
import { openPaymentWidget } from '../payment/openPaymentWidget'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import type { Tariff } from '../../types/api'

interface TariffsSectionProps {
  content: Record<string, string>
}

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
}

function TariffCard({ tariff, highlight = false }: TariffCardProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const clientProfile = useAuthStore((s) => s.clientProfile)

  const handlePay = () => {
    if (!isAuthenticated) {
      alert('Для оплаты начните с Telegram-бота: @baqsy_bot')
      return
    }
    openPaymentWidget(
      {
        publicId: import.meta.env.VITE_CLOUDPAYMENTS_PUBLIC_ID ?? '',
        amount: Number(tariff.price_kzt),
        currency: 'KZT',
        invoiceId: `tariff-${tariff.code}-${clientProfile?.id ?? 'unknown'}`,
        description: tariff.title,
        accountId: String(clientProfile?.id ?? ''),
        data: { tariff_code: tariff.code },
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

export function TariffsSection({ content }: TariffsSectionProps) {
  const { data: tariffs, isLoading } = useTariffs()

  return (
    <section id="tariffs" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900">
            {content.tariff_section_title}
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          {isLoading ? (
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
              />
            ))
          )}
        </div>
      </div>
    </section>
  )
}
