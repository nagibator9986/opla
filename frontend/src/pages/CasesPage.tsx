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

// Минималистичный список: ТОЛЬКО кликабельные заголовки кейсов — без значков,
// подзаголовков, отраслей и метрик (по просьбе клиента: «значки не нужны»,
// «только заголовки кликабельные, чтобы места меньше занимало»). Все детали
// (метрика, разбор) открываются в модалке по клику. Стрелка проявляется лишь
// при наведении, поэтому по умолчанию — чистый список заголовков.
function CaseList({ cases, onOpen }: { cases: CaseSummary[]; onOpen: (slug: string) => void }) {
  return (
    <ul className="max-w-2xl mx-auto border-t border-ink-100">
      {cases.map((c) => (
        <li key={c.slug} className="border-b border-ink-100">
          <button
            type="button"
            onClick={() => onOpen(c.slug)}
            className="group w-full flex items-center gap-3 py-3 text-left cursor-pointer"
            aria-label={`Открыть кейс ${c.company_name || c.title}`}
          >
            <span className="flex-1 min-w-0 truncate font-medium text-ink-700 group-hover:text-brand-700 transition-colors">
              {c.company_name || c.title}
            </span>
            <svg
              className="flex-shrink-0 w-4 h-4 text-ink-300 opacity-0 group-hover:opacity-100 group-hover:text-brand-500 group-hover:translate-x-0.5 transition-all"
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
  )
}

function CaseListSkeleton() {
  return (
    <ul className="max-w-2xl mx-auto border-t border-ink-100">
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
        <li key={i} className="border-b border-ink-100 py-3">
          <span
            className="block h-4 bg-ink-100 rounded animate-pulse"
            style={{ width: `${50 + (i % 4) * 12}%` }}
          />
        </li>
      ))}
    </ul>
  )
}
