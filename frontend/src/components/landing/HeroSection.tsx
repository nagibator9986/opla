import { Container } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { ChatLauncher } from '../chat/ChatLauncher'

interface HeroSectionProps {
  content: Record<string, string>
}

export function HeroSection({ content }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden text-white">
      {/* Rune-pattern background */}
      <div
        aria-hidden
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: 'url(/baqsy-runes-bg.jpg)' }}
      />
      {/* Дополнительный затемняющий слой и брендовое свечение */}
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
            Digital Baqsylyq · Код Вечного Иля
          </Badge>
          <h1 className="mt-6 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05]">
            {content.hero_title ?? 'Аудит бизнеса по Коду Вечного Иля'}
          </h1>
          <p className="mt-6 text-base sm:text-lg md:text-xl text-ink-200 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
            {content.hero_subtitle ??
              'Глубокая системная диагностика компании. AI-ассистент Baqsy задаёт вопросы — '
              + 'эксперт собирает консолидированный отчёт по 27 параметрам и присылает '
              + 'именной PDF в WhatsApp за 3–5 рабочих дней.'}
          </p>

          <div className="mt-8 md:mt-10 flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
            <ChatLauncher variant="secondary" size="xl">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {content.hero_cta ?? 'Открыть Baqsy AI'}
            </ChatLauncher>
            <a
              href="#packages"
              className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl border border-white/15 bg-white/5 text-white font-semibold hover:bg-white/10 transition-colors backdrop-blur"
            >
              Что входит в пакеты
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 3a.75.75 0 01.75.75v10.69l3.22-3.22a.75.75 0 111.06 1.06l-4.5 4.5a.75.75 0 01-1.06 0l-4.5-4.5a.75.75 0 111.06-1.06l3.22 3.22V3.75A.75.75 0 0110 3z"
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </div>

          <dl className="mt-10 md:mt-12 grid grid-cols-3 gap-4 sm:gap-6 max-w-lg mx-auto lg:mx-0">
            {[
              { k: '27', v: 'параметров' },
              { k: '3–5', v: 'рабочих дней' },
              { k: 'до 7', v: 'участников в группе' },
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
