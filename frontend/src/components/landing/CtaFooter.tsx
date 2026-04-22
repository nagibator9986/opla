import { useLocation, Link } from 'react-router-dom'
import { Container } from '../ui/Container'
import { ChatLauncher } from '../chat/ChatLauncher'

export function CtaFooter() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

  return (
    <section className="relative overflow-hidden bg-ink-950 text-white">
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgb(245_158_11_/_0.2),transparent_60%)]"
      />
      <div className="absolute inset-0 bg-grid-dark opacity-40" aria-hidden />
      <Container className="relative py-20 md:py-28 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 shadow-xl mb-6">
          <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight leading-tight max-w-2xl mx-auto">
          Готовы увидеть бизнес под новым углом?
        </h2>
        <p className="mt-5 text-ink-300 text-base md:text-xl max-w-xl mx-auto leading-relaxed">
          Начните с ассистентом Baqsy AI — это 5 минут вопросов, дальше всё делаем мы.
          Отчёт придёт на WhatsApp за 3–5 дней.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
          <ChatLauncher variant="secondary" size="xl">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Начать диалог с AI
          </ChatLauncher>
          {isLanding ? (
            <a
              href="#tariffs"
              className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl border border-white/15 bg-white/5 text-white font-semibold hover:bg-white/10 transition-colors backdrop-blur"
            >
              Посмотреть тарифы
            </a>
          ) : (
            <Link
              to="/tariffs"
              className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl border border-white/15 bg-white/5 text-white font-semibold hover:bg-white/10 transition-colors backdrop-blur"
            >
              Посмотреть тарифы
            </Link>
          )}
        </div>
      </Container>
    </section>
  )
}
