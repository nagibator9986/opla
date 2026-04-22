import type { Tariff, Submission } from '../../types/api'
import { useAuthStore } from '../../store/authStore'
import { openPaymentWidget } from '../payment/openPaymentWidget'
import { useToast } from '../ui/toast-context'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { cn } from '../../lib/cn'

interface TariffCardProps {
  tariff: Tariff
  featured?: boolean
  submission?: Submission | null
  features?: string[]
  onSuccess?: () => void
}

function formatPrice(price: string): string {
  return Number(price).toLocaleString('ru-RU')
}

const DEFAULT_FEATURES: Record<string, string[]> = {
  ashide_1: [
    'Анализ 7–9 ключевых параметров',
    'Отраслевая анкета из 27 вопросов',
    'Отчёт в PDF в фирменном стиле',
    'Доставка в Telegram и WhatsApp',
    'Подготовка за 3–5 рабочих дней',
  ],
  ashide_2: [
    'Полный анализ по 18–24 параметрам',
    'Глубокий разбор каждого блока',
    'Персональные рекомендации эксперта',
    'Финансовая модель и прогноз',
    'Доставка в Telegram и WhatsApp',
    'Приоритетная подготовка за 3 дня',
  ],
}

const CheckIcon = ({ featured }: { featured?: boolean }) => (
  <span
    className={cn(
      'flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full mt-0.5',
      featured ? 'bg-brand-400/20 text-brand-300' : 'bg-emerald-100 text-emerald-600',
    )}
  >
    <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
        clipRule="evenodd"
      />
    </svg>
  </span>
)

export function TariffCard({ tariff, featured = false, submission, features, onSuccess }: TariffCardProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const clientProfile = useAuthStore((s) => s.clientProfile)
  const toast = useToast()

  const items = features ?? DEFAULT_FEATURES[tariff.code] ?? []

  const handlePay = () => {
    if (!isAuthenticated) {
      toast.show({
        kind: 'info',
        title: 'Сначала заполните профиль',
        description: 'Нажмите «Начать диалог» — ассистент Baqsy AI соберёт данные и откроет оплату.',
      })
      return
    }
    const publicId = import.meta.env.VITE_CLOUDPAYMENTS_PUBLIC_ID ?? ''
    if (!publicId) {
      toast.show({
        kind: 'error',
        title: 'Оплата временно недоступна',
        description: 'Платёжный модуль настраивается. Напишите на info@baqsy.kz — оформим заказ вручную.',
      })
      return
    }
    const invoiceId = submission?.id ?? `tariff-${tariff.code}-${clientProfile?.id ?? 'unknown'}`
    openPaymentWidget(
      {
        publicId,
        amount: Number(tariff.price_kzt),
        currency: 'KZT',
        invoiceId,
        description: tariff.title,
        accountId: String(clientProfile?.id ?? ''),
        data: { tariff_code: tariff.code, submission_id: submission?.id },
      },
      () => {
        toast.show({
          kind: 'success',
          title: 'Оплата прошла',
          description: 'Продолжайте анкету в Telegram-боте — мы уже ждём вас.',
        })
        onSuccess?.()
      },
      (reason) => {
        toast.show({
          kind: 'error',
          title: 'Оплата не прошла',
          description: reason || 'Попробуйте ещё раз или выберите другую карту.',
        })
      },
    )
  }

  return (
    <div
      className={cn(
        'relative flex flex-col rounded-3xl p-7 md:p-9 transition-all duration-300 h-full',
        featured
          ? 'bg-gradient-to-br from-ink-900 via-ink-800 to-ink-900 text-white shadow-[0_20px_40px_rgb(15_23_42_/_0.3)] ring-1 ring-brand-500/40'
          : 'bg-white border border-ink-200 shadow-[0_4px_14px_rgb(15_23_42_/_0.06)] hover:shadow-[0_10px_30px_rgb(15_23_42_/_0.1)] hover:-translate-y-1',
      )}
    >
      {featured && (
        <>
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
            <Badge variant="brand" size="md" className="shadow-lg">
              <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Рекомендуем
            </Badge>
          </div>
          <div
            aria-hidden
            className="absolute inset-0 rounded-3xl bg-[radial-gradient(circle_at_top_right,rgb(245_158_11_/_0.18),transparent_60%)] pointer-events-none"
          />
        </>
      )}

      <div className="relative flex flex-col flex-1">
        <div className="flex items-start justify-between gap-3 mb-1">
          <h3 className={cn('text-xl md:text-2xl font-bold tracking-tight', featured ? 'text-white' : 'text-ink-900')}>
            {tariff.title}
          </h3>
        </div>
        <p className={cn('text-sm mb-6 leading-relaxed', featured ? 'text-ink-300' : 'text-ink-500')}>
          {tariff.description ||
            (tariff.code === 'ashide_1'
              ? 'Базовый аудит для быстрого старта'
              : 'Полный аудит с максимальной глубиной')}
        </p>

        <div className="mb-6">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className={cn('text-4xl md:text-5xl font-bold tracking-tight tabular-nums', featured ? 'text-white' : 'text-ink-900')}>
              {formatPrice(tariff.price_kzt)}
            </span>
            <span className={cn('text-lg font-semibold', featured ? 'text-brand-300' : 'text-ink-500')}>₸</span>
          </div>
          <p className={cn('text-xs mt-1.5', featured ? 'text-ink-400' : 'text-ink-500')}>
            Единоразовый платёж. Без подписок и скрытых комиссий.
          </p>
        </div>

        <ul className={cn('space-y-3 mb-8 flex-1', featured ? 'text-ink-100' : 'text-ink-700')}>
          {items.map((item) => (
            <li key={item} className="flex items-start gap-3 text-sm">
              <CheckIcon featured={featured} />
              <span className="leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>

        <Button variant={featured ? 'secondary' : 'primary'} size="lg" fullWidth onClick={handlePay}>
          Оплатить
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </Button>
        <p className={cn('mt-3 text-center text-[11px]', featured ? 'text-ink-400' : 'text-ink-500')}>
          3-D Secure • CloudPayments KZ
        </p>
      </div>
    </div>
  )
}

export function TariffSkeleton({ featured = false }: { featured?: boolean }) {
  return (
    <div
      className={cn(
        'rounded-3xl p-7 md:p-9 animate-pulse h-full',
        featured ? 'bg-ink-800' : 'bg-white border border-ink-200',
      )}
    >
      <div className={cn('h-6 rounded w-3/4 mb-4', featured ? 'bg-ink-700' : 'bg-ink-200')} />
      <div className={cn('h-4 rounded w-2/3 mb-8', featured ? 'bg-ink-700' : 'bg-ink-200')} />
      <div className={cn('h-12 rounded w-1/2 mb-8', featured ? 'bg-ink-700' : 'bg-ink-200')} />
      <div className="space-y-3 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className={cn('h-4 rounded w-full', featured ? 'bg-ink-700' : 'bg-ink-200')} />
        ))}
      </div>
      <div className={cn('h-12 rounded-xl', featured ? 'bg-ink-700' : 'bg-ink-200')} />
    </div>
  )
}
