import { useTariffs } from '../../hooks/useTariffs'
import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { ChatLauncher } from '../chat/ChatLauncher'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/cn'

interface PackagesSectionProps {
  content: Record<string, string>
}

const PACKAGE_META: Record<
  string,
  { participants: string; usd?: string; tagline: string }
> = {
  ashide_1: {
    participants: '1 сотрудник',
    tagline: 'Личная диагностика — для индивидуальной работы',
  },
  ashide_2: {
    participants: '3–7 сотрудников',
    usd: '$729',
    tagline: 'Командный аудит — собственники и топ-команды',
  },
}

function formatPrice(price: string): string {
  return Number(price).toLocaleString('ru-RU')
}

export function PackagesSection({ content }: PackagesSectionProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
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
            {content.tariff_section_title ?? 'Два формата аудита'}
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            Доступ к пакетам открывается{' '}
            <span className="font-semibold text-ink-900">после регистрации</span>{' '}
            в Baqsy AI.
          </p>
        </div>

        <div className="relative">
          <div
            className={cn(
              'grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 max-w-4xl mx-auto transition-all duration-300',
              !isAuthenticated && 'pointer-events-none select-none',
            )}
            aria-hidden={!isAuthenticated}
          >
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
                  priceKzt={formatPrice(tariff.price_kzt)}
                  featured={tariff.code === 'ashide_2'}
                  blurred={!isAuthenticated}
                />
              ))
            )}
          </div>

          {/* Lock overlay when not authenticated */}
          {!isAuthenticated && (
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-ink-50/40 via-ink-50/85 to-ink-50 backdrop-blur-[2px] rounded-2xl">
              <div className="bg-white rounded-2xl shadow-xl border border-ink-200 p-7 md:p-8 max-w-md text-center mx-4">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-100 text-brand-700 mb-4">
                  <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M7 11V7a5 5 0 0110 0v4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-ink-900 mb-2">
                  Пакеты открываются после регистрации
                </h3>
                <p className="text-sm text-ink-600 mb-6 leading-relaxed">
                  Откройте Baqsy AI и заполните паспорт компании — это блок 1
                  анкеты, занимает 2 минуты. После этого вы увидите детали обоих
                  пакетов и сможете оформить аудит.
                </p>
                <ChatLauncher variant="primary" size="lg">
                  Открыть Baqsy AI
                </ChatLauncher>
              </div>
            </div>
          )}
        </div>
      </Container>
    </Section>
  )
}

function PackageCard({
  code,
  title,
  priceKzt,
  featured,
  blurred,
}: {
  code: string
  title: string
  priceKzt: string
  featured?: boolean
  blurred?: boolean
}) {
  const meta = PACKAGE_META[code] ?? { participants: '', tagline: '' }
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

      <div className={cn('relative flex flex-col flex-1', blurred && 'blur-[2px]')}>
        <h3
          className={cn(
            'text-xl md:text-2xl font-bold tracking-tight',
            featured ? 'text-white' : 'text-ink-900',
          )}
        >
          {title}
        </h3>
        <p
          className={cn(
            'text-sm leading-relaxed',
            featured ? 'text-ink-300' : 'text-ink-500',
          )}
        >
          {meta.tagline}
        </p>

        <p
          className={cn(
            'mt-5 text-base font-semibold',
            featured ? 'text-brand-300' : 'text-ink-700',
          )}
        >
          {meta.participants}
        </p>

        <div className="mt-6">
          {meta.usd ? (
            <>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span
                  className={cn(
                    'text-4xl md:text-5xl font-bold tracking-tight tabular-nums',
                    featured ? 'text-white' : 'text-ink-900',
                  )}
                >
                  {meta.usd}
                </span>
              </div>
              <p
                className={cn(
                  'text-xs mt-1.5',
                  featured ? 'text-ink-400' : 'text-ink-500',
                )}
              >
                ≈ {priceKzt} ₸ к оплате · единоразовый платёж
              </p>
            </>
          ) : (
            <>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span
                  className={cn(
                    'text-4xl md:text-5xl font-bold tracking-tight tabular-nums',
                    featured ? 'text-white' : 'text-ink-900',
                  )}
                >
                  {priceKzt}
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
                Единоразовый платёж
              </p>
            </>
          )}
        </div>
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
      <div className={cn('h-5 rounded w-1/3 mb-6', featured ? 'bg-ink-700' : 'bg-ink-200')} />
      <div className={cn('h-12 rounded w-1/2', featured ? 'bg-ink-700' : 'bg-ink-200')} />
    </div>
  )
}
