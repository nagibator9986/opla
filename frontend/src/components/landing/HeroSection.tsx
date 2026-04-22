import { Button } from '../ui/Button'
import { Container } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { ChatLauncher } from '../chat/ChatLauncher'

interface HeroSectionProps {
  content: Record<string, string>
}

export function HeroSection({ content }: HeroSectionProps) {
  const handleScroll = () => {
    document.getElementById('tariffs')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-ink-950 via-ink-900 to-ink-950 text-white">
      <div className="absolute inset-0 bg-grid-dark opacity-60" aria-hidden />
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgb(245_158_11_/_0.18),transparent_50%)]"
      />
      <div
        aria-hidden
        className="absolute -top-24 -left-24 w-[420px] h-[420px] rounded-full bg-brand-500/10 blur-[120px]"
      />
      <div
        aria-hidden
        className="absolute -bottom-32 -right-20 w-[480px] h-[480px] rounded-full bg-brand-500/8 blur-[140px]"
      />
      <div
        aria-hidden
        className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-ink-950 to-transparent"
      />

      <Container className="relative min-h-[620px] lg:min-h-[720px] flex items-center pt-28 pb-20 md:pt-32 md:pb-28">
        <div className="w-full grid lg:grid-cols-[1.1fr_1fr] gap-12 lg:gap-16 items-center">
          <div className="text-center lg:text-left animate-fade-in">
            <Badge variant="brand" className="backdrop-blur bg-brand-500/20 text-brand-200 ring-brand-400/30">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
              Профессиональный бизнес-аудит
            </Badge>
            <h1 className="mt-6 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05]">
              {content.hero_title ?? 'Аудит бизнеса, который ведёт к росту'}
            </h1>
            <p className="mt-6 text-base sm:text-lg md:text-xl text-ink-300 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
              {content.hero_subtitle ??
                'Ответьте на несколько вопросов ассистенту Baqsy AI — мы подберём формат аудита под вашу отрасль и пришлём именной PDF-отчёт за 3–5 дней.'}
            </p>

            <div className="mt-8 md:mt-10 flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
              <ChatLauncher variant="secondary" size="xl">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {content.hero_cta ?? 'Начать диалог'}
              </ChatLauncher>
              <Button variant="outline" size="xl" onClick={handleScroll} className="bg-white/5 border-white/15 text-white hover:bg-white/10">
                Посмотреть тарифы
                <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </Button>
            </div>

            <dl className="mt-10 md:mt-12 grid grid-cols-3 gap-4 sm:gap-6 max-w-lg mx-auto lg:mx-0">
              {[
                { k: '27', v: 'вопросов' },
                { k: '3–5', v: 'рабочих дней' },
                { k: '24', v: 'параметра' },
              ].map((s) => (
                <div key={s.v} className="text-center lg:text-left">
                  <dt className="text-3xl md:text-4xl font-bold text-white tracking-tight">{s.k}</dt>
                  <dd className="mt-1 text-[11px] md:text-xs text-ink-400 uppercase tracking-wide">{s.v}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="relative hidden lg:block">
            <HeroPreview />
          </div>
        </div>
      </Container>
    </section>
  )
}

function HeroPreview() {
  return (
    <div className="relative">
      <div
        className="absolute -inset-4 bg-gradient-to-br from-brand-500/30 via-transparent to-ink-900/0 rounded-[2.5rem] blur-2xl"
        aria-hidden
      />
      <div className="relative bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-400" />
            <span className="w-2.5 h-2.5 rounded-full bg-brand-400" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          </div>
          <span className="text-xs text-ink-300 font-mono">audit_report.pdf</span>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 shadow-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div>
              <p className="text-white font-semibold text-sm">Бизнес-аудит</p>
              <p className="text-ink-400 text-xs">ТОО «Пример»</p>
            </div>
          </div>

          {[
            { label: 'Маржинальность', value: 82, color: 'from-emerald-400 to-emerald-500' },
            { label: 'Операционка', value: 68, color: 'from-brand-400 to-brand-500' },
            { label: 'Команда', value: 74, color: 'from-sky-400 to-sky-500' },
            { label: 'Продажи', value: 56, color: 'from-rose-400 to-rose-500' },
          ].map((r, idx) => (
            <div key={r.label} style={{ animationDelay: `${200 + idx * 80}ms` }} className="animate-fade-in">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ink-300">{r.label}</span>
                <span className="text-white font-semibold tabular-nums">{r.value}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${r.color}`}
                  style={{ width: `${r.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 p-3 rounded-xl bg-white/5 border border-white/10">
          <p className="text-xs text-ink-300 leading-relaxed">
            <span className="text-brand-300 font-semibold">Рекомендация:</span> сократить цикл продаж
            и пересобрать KPI команды продаж.
          </p>
        </div>
      </div>
    </div>
  )
}
