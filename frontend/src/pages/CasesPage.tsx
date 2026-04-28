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
                  Примеры применения метода Baqsy на известных компаниях.
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
                    <rect
                      x="3"
                      y="11"
                      width="18"
                      height="11"
                      rx="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M7 11V7a5 5 0 0110 0v4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                <CaseSkeleton />
                <CaseSkeleton />
              </div>
            ) : (cases ?? []).length === 0 ? (
              <p className="text-center text-ink-500">
                Кейсы появятся совсем скоро — мы готовим первые публикации.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                {cases!.map((c) => (
                  <article
                    key={c.slug}
                    className="group relative overflow-hidden bg-white rounded-2xl p-7 md:p-8 border border-ink-200/70 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] hover:shadow-[0_10px_30px_rgb(15_23_42_/_0.08)] transition-shadow"
                  >
                    <div
                      aria-hidden
                      className={`absolute -top-24 -right-24 w-48 h-48 rounded-full bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} opacity-10 blur-2xl`}
                    />
                    <div className="relative">
                      <div className="flex items-center justify-between mb-5">
                        {c.logo_url ? (
                          <img
                            src={c.logo_url}
                            alt={c.company_name || c.title}
                            className="max-h-9 max-w-[120px] object-contain"
                          />
                        ) : (
                          <Badge variant="neutral" size="sm">
                            {c.industry || '—'}
                          </Badge>
                        )}
                        <svg
                          className="w-8 h-8 text-ink-200"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                        >
                          <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2H4c-1.25 0-2 .75-2 2v4c0 1.25.75 2 2 2h2s.73 2.66-2.66 4c-.48.15-.35.85.66.85zm14 0c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2h-4c-1.25 0-2 .75-2 2v4c0 1.25.75 2 2 2h2s.73 2.66-2.66 4c-.48.15-.35.85.66.85z" />
                        </svg>
                      </div>
                      <h3 className="text-xl md:text-2xl font-bold text-ink-900 mb-3">
                        {c.title}
                      </h3>
                      <p className="text-ink-600 leading-relaxed mb-6">
                        {c.short_text || c.subtitle}
                      </p>
                      {(c.metric || c.metric_label) && (
                        <div className="flex items-end gap-3 pt-5 border-t border-ink-100">
                          {c.metric && (
                            <span
                              className={`text-4xl md:text-5xl font-bold bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} bg-clip-text text-transparent leading-none`}
                            >
                              {c.metric}
                            </span>
                          )}
                          {c.metric_label && (
                            <span className="text-sm text-ink-500 mb-1">
                              {c.metric_label}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    <Link
                      to={`/cases/${c.slug}`}
                      className="absolute inset-0"
                      aria-label={`Открыть кейс ${c.title}`}
                    />
                  </article>
                ))}
              </div>
            )}
          </Container>
        </Section>
      </main>
      <Footer />
      <DockedChatPanel />
    </div>
  )
}

function CaseSkeleton() {
  return (
    <div className="rounded-2xl bg-white border border-ink-200 p-7 md:p-8 animate-pulse">
      <div className="flex items-center justify-between mb-5">
        <div className="h-8 w-24 bg-ink-100 rounded" />
        <div className="h-8 w-8 bg-ink-100 rounded" />
      </div>
      <div className="h-6 bg-ink-100 rounded w-3/4 mb-3" />
      <div className="space-y-2 mb-6">
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded w-5/6" />
      </div>
      <div className="h-10 bg-ink-100 rounded w-1/2" />
    </div>
  )
}
