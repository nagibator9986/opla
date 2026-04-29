import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Container, Section } from '../components/ui/Container'
import { Badge } from '../components/ui/Badge'
import { ChatLauncher, DockedChatPanel } from '../components/chat/ChatLauncher'
import { listCases, type CaseSummary } from '../api/cases'
import { useAuthStore } from '../store/authStore'

const ACCENT_GRADIENT: Record<CaseSummary['accent'], string> = {
  emerald: 'from-emerald-400 to-emerald-600',
  sky: 'from-sky-400 to-indigo-500',
  amber: 'from-amber-400 to-orange-500',
  rose: 'from-rose-400 to-rose-600',
  violet: 'from-violet-400 to-purple-500',
  slate: 'from-slate-400 to-slate-600',
}

export function CasesPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { data: cases, isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: listCases,
    staleTime: 5 * 60 * 1000,
    enabled: isAuthenticated,
  })

  // Scroll to top on navigate to /cases (browser-router doesn't do this by default)
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }, [])

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1">
        <Section background="ink-50">
          <Container>
            <div className="max-w-2xl mx-auto text-center mb-10 md:mb-12">
              <Badge variant="neutral" className="mb-4">
                Кейсы мировых компаний
              </Badge>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
                {isAuthenticated
                  ? 'Разборы по Коду Вечного Иля'
                  : 'Раздел открывается после регистрации'}
              </h1>
              {isAuthenticated && (
                <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
                  Выберите компанию — откроется детальный разбор по методу Baqsy.
                </p>
              )}
            </div>

            {!isAuthenticated ? (
              <div className="max-w-md mx-auto bg-white rounded-2xl shadow-xl border border-ink-200 p-7 md:p-8 text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-100 text-brand-700 mb-4">
                  <svg
                    className="w-7 h-7"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M7 11V7a5 5 0 0110 0v4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <p className="text-sm text-ink-600 mb-6 leading-relaxed">
                  Чтобы ознакомиться с информацией, пройдите, пожалуйста,
                  регистрацию.
                </p>
                <ChatLauncher variant="primary" size="lg">
                  Чтобы ознакомиться с информацией, пройдите, пожалуйста,
                  регистрацию
                </ChatLauncher>
              </div>
            ) : isLoading ? (
              <LogoGridSkeleton />
            ) : (cases ?? []).length === 0 ? (
              <p className="text-center text-ink-500">
                Кейсы появятся совсем скоро — мы готовим первые публикации.
              </p>
            ) : (
              <LogoGrid cases={cases!} />
            )}
          </Container>
        </Section>
      </main>
      <Footer />
      <DockedChatPanel />
    </div>
  )
}

function LogoGrid({ cases }: { cases: CaseSummary[] }) {
  return (
    <ul className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6 max-w-5xl mx-auto">
      {cases.map((c) => (
        <li key={c.slug}>
          <Link
            to={`/cases/${c.slug}`}
            className="group relative block aspect-square rounded-2xl bg-white border border-ink-200/70 hover:border-brand-300 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] hover:shadow-[0_14px_40px_rgb(15_23_42_/_0.12)] transition-all duration-300 overflow-hidden hover:-translate-y-1"
            aria-label={`Открыть кейс ${c.title}`}
          >
            <div
              aria-hidden
              className={`absolute -top-16 -right-16 w-40 h-40 rounded-full bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} opacity-10 blur-2xl group-hover:opacity-20 transition-opacity`}
            />
            <div className="relative h-full flex flex-col items-center justify-center p-6 text-center">
              {c.logo_url ? (
                <img
                  src={c.logo_url}
                  alt={c.company_name || c.title}
                  className="max-h-14 md:max-h-16 max-w-[70%] object-contain grayscale group-hover:grayscale-0 transition-all duration-300"
                />
              ) : (
                <span className="text-2xl md:text-3xl font-bold text-ink-700 group-hover:text-ink-900 tracking-tight">
                  {(c.company_name || c.title).slice(0, 2).toUpperCase()}
                </span>
              )}
              <span className="mt-3 text-xs md:text-sm font-semibold text-ink-700 line-clamp-1">
                {c.company_name || c.title}
              </span>
              {c.metric && (
                <span
                  className={`mt-1 text-xs font-bold bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} bg-clip-text text-transparent`}
                >
                  {c.metric}
                </span>
              )}
            </div>
          </Link>
        </li>
      ))}
    </ul>
  )
}

function LogoGridSkeleton() {
  return (
    <ul className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6 max-w-5xl mx-auto">
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
        <li
          key={i}
          className="aspect-square rounded-2xl bg-white border border-ink-200 animate-pulse"
        />
      ))}
    </ul>
  )
}
