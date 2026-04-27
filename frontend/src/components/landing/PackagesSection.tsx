import { useTariffs } from '../../hooks/useTariffs'
import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { cn } from '../../lib/cn'

interface PackagesSectionProps {
  content: Record<string, string>
}

const PACKAGE_FEATURES: Record<string, { tagline: string; bullets: string[] }> = {
  ashide_1: {
    tagline: 'Базовая диагностика — для индивидуальной работы',
    bullets: [
      'Анализ 7–9 ключевых параметров системы',
      'Отраслевая анкета — 25–38 вопросов',
      'Именной PDF-отчёт в фирменном стиле',
      'Доставка в WhatsApp · 3–5 рабочих дней',
    ],
  },
  ashide_2: {
    tagline: 'Глубокий командный аудит — для собственников и топ-команд',
    bullets: [
      'Полный анализ по 18–24 параметрам',
      'Группа из 3–7 сотрудников проходит анкету',
      'AI собирает консолидированную картину системы',
      'Подарочная книга «Вечный Иль» в составе пакета',
      'Приоритетная подготовка отчёта · 3 дня',
    ],
  },
}

function formatPrice(price: string): string {
  return Number(price).toLocaleString('ru-RU')
}

export function PackagesSection({ content }: PackagesSectionProps) {
  const { data: tariffs, isLoading } = useTariffs()
  const packages = (tariffs ?? []).filter((t) => t.code !== 'upsell')

  return (
    <Section id="packages" background="ink-50">
      <Container>
        <div className="max-w-2xl mx-auto text-center mb-12 md:mb-16">
          <Badge variant="brand" className="mb-4">
            Пакеты
          </Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
            {content.tariff_section_title ?? 'Два уровня глубины'}
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            Базовая личная диагностика или полный командный аудит с групповой
            точкой сборки. Оплата и сама работа происходят внутри{' '}
            <span className="font-semibold text-ink-900">Baqsy AI</span>.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 max-w-4xl mx-auto">
          {isLoading ? (
            <>
              <PackageSkeleton />
              <PackageSkeleton featured />
            </>
          ) : (
            packages.map((tariff) => (
              <PackageCard
                key={tariff.id}
                code={tariff.code}
                title={tariff.title}
                price={formatPrice(tariff.price_kzt)}
                description={tariff.description}
                featured={tariff.code === 'ashide_2'}
              />
            ))
          )}
        </div>

        <p className="mt-10 text-center text-sm text-ink-500">
          Чтобы оформить пакет, откройте чат{' '}
          <span className="font-semibold text-ink-700">Baqsy AI</span>{' '}
          справа внизу — он проведёт регистрацию и оплату.
        </p>
      </Container>
    </Section>
  )
}

function PackageCard({
  code,
  title,
  price,
  description,
  featured,
}: {
  code: string
  title: string
  price: string
  description?: string
  featured?: boolean
}) {
  const meta = PACKAGE_FEATURES[code] ?? { tagline: description ?? '', bullets: [] }
  return (
    <div
      className={cn(
        'relative flex flex-col rounded-3xl p-7 md:p-9 transition-all duration-300 h-full',
        featured
          ? 'bg-gradient-to-br from-ink-900 via-ink-800 to-ink-900 text-white shadow-[0_20px_40px_rgb(15_23_42_/_0.3)] ring-1 ring-brand-500/40'
          : 'bg-white border border-ink-200 shadow-[0_4px_14px_rgb(15_23_42_/_0.06)]',
      )}
    >
      {featured && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
          <Badge variant="brand" size="md" className="shadow-lg">
            <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Командный аудит
          </Badge>
        </div>
      )}
      {featured && (
        <div
          aria-hidden
          className="absolute inset-0 rounded-3xl bg-[radial-gradient(circle_at_top_right,rgb(245_158_11_/_0.18),transparent_60%)] pointer-events-none"
        />
      )}

      <div className="relative flex flex-col flex-1">
        <h3
          className={cn(
            'text-xl md:text-2xl font-bold tracking-tight',
            featured ? 'text-white' : 'text-ink-900',
          )}
        >
          {title}
        </h3>
        <p className={cn('text-sm mb-6 leading-relaxed', featured ? 'text-ink-300' : 'text-ink-500')}>
          {meta.tagline}
        </p>

        <div className="mb-6">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span
              className={cn(
                'text-4xl md:text-5xl font-bold tracking-tight tabular-nums',
                featured ? 'text-white' : 'text-ink-900',
              )}
            >
              {price}
            </span>
            <span
              className={cn(
                'text-lg font-semibold',
                featured ? 'text-brand-300' : 'text-ink-500',
              )}
            >
              ₸
            </span>
          </div>
          <p
            className={cn(
              'text-xs mt-1.5',
              featured ? 'text-ink-400' : 'text-ink-500',
            )}
          >
            Единоразовый платёж · оплата через Baqsy AI
          </p>
        </div>

        <ul
          className={cn(
            'space-y-3 mb-2 flex-1',
            featured ? 'text-ink-100' : 'text-ink-700',
          )}
        >
          {meta.bullets.map((b) => (
            <li key={b} className="flex items-start gap-3 text-sm">
              <span
                className={cn(
                  'flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full mt-0.5',
                  featured
                    ? 'bg-brand-400/20 text-brand-300'
                    : 'bg-emerald-100 text-emerald-600',
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
              <span className="leading-relaxed">{b}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function PackageSkeleton({ featured = false }: { featured?: boolean }) {
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
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className={cn('h-4 rounded w-full', featured ? 'bg-ink-700' : 'bg-ink-200')} />
        ))}
      </div>
    </div>
  )
}
