import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Container, Section } from '../components/ui/Container'
import { Badge } from '../components/ui/Badge'
import { ChatLauncher, DockedChatPanel } from '../components/chat/ChatLauncher'
import { CaseModal } from '../components/cases/CaseModal'
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
  const [searchParams, setSearchParams] = useSearchParams()
  const openSlug = searchParams.get('case')

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

  const openCase = (slug: string) => {
    setSearchParams({ case: slug }, { replace: false })
  }
  const closeCase = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('case')
    setSearchParams(next, { replace: false })
  }

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
              <CaseListSkeleton />
            ) : (cases ?? []).length === 0 ? (
              <p className="text-center text-ink-500">
                Кейсы появятся совсем скоро — мы готовим первые публикации.
              </p>
            ) : (
              <CaseList cases={cases!} onOpen={openCase} />
            )}
          </Container>
        </Section>
      </main>
      <Footer />
      <DockedChatPanel />
      {openSlug && <CaseModal slug={openSlug} onClose={closeCase} />}
    </div>
  )
}

// Компактный список: одна строка на кейс. На 35–50 кейсов занимает в разы
// меньше места, чем сетка квадратных карточек, и остаётся сканируемым.
// Клик по строке открывает модалку кейса (тот же ?case=slug).
function CaseList({ cases, onOpen }: { cases: CaseSummary[]; onOpen: (slug: string) => void }) {
  return (
    <div className="max-w-3xl mx-auto rounded-2xl border border-ink-200 bg-white shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] overflow-hidden">
      <ul className="divide-y divide-ink-100">
        {cases.map((c) => (
          <li key={c.slug}>
            <button
              type="button"
              onClick={() => onOpen(c.slug)}
              className="group w-full flex items-center gap-3 sm:gap-4 px-4 sm:px-5 py-3.5 text-left hover:bg-ink-50/70 transition-colors cursor-pointer"
              aria-label={`Открыть кейс ${c.title}`}
            >
              {/* Лого / инициалы с акцентной подложкой */}
              <span className="relative flex-shrink-0 w-11 h-11 rounded-xl bg-ink-50 border border-ink-200/70 flex items-center justify-center overflow-hidden">
                <span
                  aria-hidden
                  className={`absolute inset-0 bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} opacity-10 group-hover:opacity-20 transition-opacity`}
                />
                {c.logo_url ? (
                  <img
                    src={c.logo_url}
                    alt={c.company_name || c.title}
                    className="relative max-h-7 max-w-[80%] object-contain grayscale group-hover:grayscale-0 transition-all duration-300"
                  />
                ) : (
                  <span className="relative text-sm font-bold text-ink-700">
                    {(c.company_name || c.title).slice(0, 2).toUpperCase()}
                  </span>
                )}
              </span>

              {/* Заголовок + подзаголовок */}
              <span className="min-w-0 flex-1">
                <span className="block font-semibold text-ink-900 text-sm sm:text-base truncate">
                  {c.company_name || c.title}
                </span>
                <span className="block text-xs sm:text-sm text-ink-500 truncate">
                  {c.subtitle || c.title}
                </span>
              </span>

              {/* Отрасль — только на десктопе */}
              {c.industry && (
                <span className="hidden md:inline-flex flex-shrink-0 px-2.5 py-1 rounded-full bg-ink-100 text-ink-600 text-xs font-medium">
                  {c.industry}
                </span>
              )}

              {/* Метрика */}
              {c.metric && (
                <span
                  className={`flex-shrink-0 text-sm font-bold bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} bg-clip-text text-transparent tabular-nums`}
                >
                  {c.metric}
                </span>
              )}

              {/* Шеврон */}
              <svg
                className="flex-shrink-0 w-4 h-4 text-ink-300 group-hover:text-ink-500 group-hover:translate-x-0.5 transition-all"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden
              >
                <path
                  fillRule="evenodd"
                  d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function CaseListSkeleton() {
  return (
    <div className="max-w-3xl mx-auto rounded-2xl border border-ink-200 bg-white overflow-hidden">
      <ul className="divide-y divide-ink-100">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <li key={i} className="flex items-center gap-4 px-4 sm:px-5 py-3.5 animate-pulse">
            <span className="flex-shrink-0 w-11 h-11 rounded-xl bg-ink-100" />
            <span className="flex-1 space-y-2">
              <span className="block h-3.5 w-1/3 bg-ink-100 rounded" />
              <span className="block h-3 w-2/3 bg-ink-100 rounded" />
            </span>
            <span className="flex-shrink-0 w-10 h-4 bg-ink-100 rounded" />
          </li>
        ))}
      </ul>
    </div>
  )
}
