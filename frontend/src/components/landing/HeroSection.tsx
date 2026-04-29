import { Link } from 'react-router-dom'
import { Container } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/cn'

interface HeroSectionProps {
  content: Record<string, string>
}

export function HeroSection({ content }: HeroSectionProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const ctaText = content.hero_pkg_cta_authed ?? 'Заказать аудит →'

  return (
    <section className="relative overflow-hidden text-white">
      <div
        aria-hidden
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: 'url(/baqsy-runes-bg.jpg)' }}
      />
      <div aria-hidden className="absolute inset-0 bg-ink-950/45" />
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgb(245_158_11_/_0.16),transparent_55%)]"
      />
      <div
        aria-hidden
        className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-ink-950 to-transparent"
      />

      <Container className="relative min-h-[640px] lg:min-h-[720px] flex items-center pt-28 pb-20 md:pt-32 md:pb-28">
        <div className="w-full max-w-3xl mx-auto lg:mx-0 text-center lg:text-left animate-fade-in">
          <Badge
            variant="brand"
            className="backdrop-blur bg-brand-500/20 text-brand-200 ring-brand-400/30"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
            {content.hero_badge ?? 'Digital Baqsylyq · Код Вечного Иля'}
          </Badge>
          <h1 className="mt-6 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05]">
            {content.hero_title ?? 'Аудит бизнеса по Коду Вечного Иля'}
          </h1>
          <p className="mt-6 text-base sm:text-lg md:text-xl text-ink-200 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
            {content.hero_subtitle ??
              'Заполните анкету, выберите тариф и получите именной PDF-отчёт с '
              + 'анализом ключевых параметров за 1–2 дней.'}
          </p>

          <div
            className="mt-8 md:mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto lg:mx-0"
            role="presentation"
            aria-label="Доступные пакеты аудита"
          >
            <PackageCard
              label={content.hero_pkg1_label ?? 'Пакет 1'}
              title={content.hero_pkg1_title ?? 'Ashide 1 (1 сотрудник)'}
              price={content.hero_pkg1_price ?? '199$'}
              isAuthenticated={isAuthenticated}
              ctaText={ctaText}
              focus="ashide_1"
            />
            <PackageCard
              label={content.hero_pkg2_label ?? 'Пакет 2'}
              title={content.hero_pkg2_title ?? 'Ashino + Ashide (3–7 сотрудников)'}
              price={content.hero_pkg2_price ?? '799$'}
              isAuthenticated={isAuthenticated}
              ctaText={ctaText}
              focus="ashide_2"
            />
          </div>

          <dl className="mt-10 md:mt-12 grid grid-cols-3 gap-4 sm:gap-6 max-w-lg mx-auto lg:mx-0">
            {[
              { k: content.hero_stat1_value ?? '27', v: content.hero_stat1_label ?? 'параметров' },
              { k: content.hero_stat2_value ?? '3–5', v: content.hero_stat2_label ?? 'рабочих дней' },
              { k: content.hero_stat3_value ?? 'до 7', v: content.hero_stat3_label ?? 'участников в группе' },
            ].map((s) => (
              <div key={s.v} className="text-center lg:text-left">
                <dt className="text-3xl md:text-4xl font-bold text-white tracking-tight">{s.k}</dt>
                <dd className="mt-1 text-[11px] md:text-xs text-ink-300 uppercase tracking-wide">
                  {s.v}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </Container>
    </section>
  )
}

function PackageCard({
  label,
  title,
  price,
  isAuthenticated,
  ctaText,
  focus,
}: {
  label: string
  title: string
  price: string
  isAuthenticated: boolean
  ctaText: string
  focus: string
}) {
  const baseStyle = cn(
    'rounded-xl px-6 py-4 border bg-white/5 text-white backdrop-blur transition-all duration-200',
    isAuthenticated
      ? 'border-brand-400/40 hover:border-brand-300 hover:bg-white/10 hover:-translate-y-0.5 hover:shadow-[0_14px_40px_rgb(245_158_11_/_0.2)] cursor-pointer'
      : 'border-white/15',
  )

  const inner = (
    <>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-brand-300">
        {label}
      </div>
      <div className="mt-1 text-base md:text-lg font-bold leading-tight">{title}</div>
      <div className="mt-1 text-2xl md:text-3xl font-extrabold tracking-tight tabular-nums">
        {price}
      </div>
      {isAuthenticated && (
        <div className="mt-2 text-xs font-semibold text-brand-300 group-hover:text-brand-200 transition-colors">
          {ctaText}
        </div>
      )}
    </>
  )

  if (isAuthenticated) {
    return (
      <Link
        to={`/tariffs?focus=${encodeURIComponent(focus)}`}
        className={cn(baseStyle, 'group block')}
        aria-label={`Заказать ${title}`}
      >
        {inner}
      </Link>
    )
  }
  return <div className={baseStyle}>{inner}</div>
}
