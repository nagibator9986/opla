import { useLocation, Link } from 'react-router-dom'
import { Container } from '../ui/Container'

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
            <path d="M22 2L11 13" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight leading-tight max-w-2xl mx-auto">
          Готовы увидеть бизнес под новым углом?
        </h2>
        <p className="mt-5 text-ink-300 text-base md:text-xl max-w-xl mx-auto leading-relaxed">
          Начните в Telegram — это займёт несколько минут. Отчёт придёт в мессенджер за 3–5 дней.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
          <a
            href="https://t.me/Baqsysystembot"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl bg-gradient-to-b from-brand-400 to-brand-500 text-ink-950 font-semibold shadow-lg hover:from-brand-300 hover:to-brand-400 transition-all active:scale-[0.98]"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z" />
            </svg>
            Начать в Telegram
          </a>
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
