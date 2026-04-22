import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Container } from '../components/ui/Container'
import { Badge } from '../components/ui/Badge'
import { ChatLauncher, FloatingChatButton } from '../components/chat/ChatLauncher'
import { getCase, type CaseDetail } from '../api/cases'

const ACCENT_GRADIENT: Record<CaseDetail['accent'], string> = {
  emerald: 'from-emerald-400 to-emerald-600',
  sky: 'from-sky-400 to-indigo-500',
  amber: 'from-amber-400 to-orange-500',
  rose: 'from-rose-400 to-rose-600',
  violet: 'from-violet-400 to-purple-500',
  slate: 'from-slate-400 to-slate-600',
}

export function CaseDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['case', slug],
    queryFn: () => getCase(slug!),
    enabled: !!slug,
    retry: 1,
  })

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header variant="solid" />
      <main className="flex-1 pt-24 pb-16 md:pt-28">
        <Container size="sm">
          <Link to="/#cases" className="inline-flex items-center gap-1 text-sm font-semibold text-ink-600 hover:text-ink-900 transition-colors mb-6">
            <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Все кейсы
          </Link>

          {isLoading && <DetailSkeleton />}
          {(isError || (!isLoading && !data)) && (
            <div className="py-20 text-center">
              <h1 className="text-2xl font-bold text-ink-900 mb-2">Кейс не найден</h1>
              <p className="text-ink-600 mb-6">
                Возможно, он был снят с публикации или ссылка устарела.
              </p>
              <Link
                to="/"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-ink-900 text-white font-semibold hover:bg-ink-800 transition-colors"
              >
                На главную
              </Link>
            </div>
          )}

          {data && (
            <article className="animate-fade-in">
              <header className="mb-8">
                <div className="flex items-center gap-3 mb-4 flex-wrap">
                  {data.industry && <Badge variant="brand">{data.industry}</Badge>}
                  {data.company_name && (
                    <span className="text-sm text-ink-500">{data.company_name}</span>
                  )}
                </div>
                <h1 className="text-3xl md:text-5xl font-bold text-ink-900 tracking-tight leading-[1.1]">
                  {data.title}
                </h1>
                {data.subtitle && (
                  <p className="mt-4 text-lg md:text-xl text-ink-600 leading-relaxed">
                    {data.subtitle}
                  </p>
                )}
                {(data.metric || data.metric_label) && (
                  <div className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-ink-50 to-white border border-ink-200/70">
                    <div className="flex items-end gap-3">
                      <span
                        className={`text-5xl md:text-6xl font-bold bg-gradient-to-br ${ACCENT_GRADIENT[data.accent]} bg-clip-text text-transparent leading-none`}
                      >
                        {data.metric}
                      </span>
                      <span className="text-sm md:text-base text-ink-600 mb-2">
                        {data.metric_label}
                      </span>
                    </div>
                  </div>
                )}
              </header>

              {data.cover_url && (
                <img
                  src={data.cover_url}
                  alt={data.title}
                  className="w-full rounded-2xl mb-10 object-cover"
                />
              )}

              <div className="prose prose-ink max-w-none text-ink-800 leading-relaxed whitespace-pre-wrap text-base md:text-lg">
                {data.body || 'Полный текст кейса скоро появится.'}
              </div>

              <div className="mt-16 p-8 rounded-3xl bg-gradient-to-br from-ink-900 to-ink-950 text-white">
                <h2 className="text-2xl md:text-3xl font-bold mb-3">Хотите похожий результат?</h2>
                <p className="text-ink-300 mb-6 max-w-xl">
                  Ответьте на несколько вопросов ассистенту Baqsy AI — подберём формат аудита под вашу отрасль.
                </p>
                <ChatLauncher variant="secondary" size="lg">
                  Обсудить мой бизнес
                </ChatLauncher>
              </div>
            </article>
          )}
        </Container>
      </main>
      <Footer />
      <FloatingChatButton />
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div className="animate-pulse py-6 space-y-4">
      <div className="h-6 w-24 bg-ink-100 rounded" />
      <div className="h-12 bg-ink-100 rounded w-3/4" />
      <div className="h-5 bg-ink-100 rounded w-5/6" />
      <div className="h-64 bg-ink-100 rounded" />
      <div className="space-y-2">
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded w-5/6" />
      </div>
    </div>
  )
}
