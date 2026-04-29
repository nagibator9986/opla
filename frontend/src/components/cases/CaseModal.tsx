import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '../ui/Badge'
import { ChatLauncher } from '../chat/ChatLauncher'
import { getCase, type CaseDetail } from '../../api/cases'

const ACCENT_GRADIENT: Record<CaseDetail['accent'], string> = {
  emerald: 'from-emerald-400 to-emerald-600',
  sky: 'from-sky-400 to-indigo-500',
  amber: 'from-amber-400 to-orange-500',
  rose: 'from-rose-400 to-rose-600',
  violet: 'from-violet-400 to-purple-500',
  slate: 'from-slate-400 to-slate-600',
}

interface CaseModalProps {
  slug: string
  onClose: () => void
}

export function CaseModal({ slug, onClose }: CaseModalProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['case', slug],
    queryFn: () => getCase(slug),
    enabled: !!slug,
    retry: 1,
  })

  // Body scroll lock + Esc-to-close
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[1100] flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-0 sm:p-4 animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="case-modal-title"
    >
      <div
        className="relative w-full sm:max-w-3xl h-[92svh] sm:h-auto sm:max-h-[90vh] bg-white sm:rounded-3xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sticky close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 inline-flex items-center justify-center w-10 h-10 rounded-full bg-white/90 backdrop-blur text-ink-700 hover:text-ink-900 hover:bg-white shadow-lg ring-1 ring-ink-200 transition-colors"
          aria-label="Закрыть"
        >
          <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>

        <div className="flex-1 overflow-y-auto">
          {isLoading && <DetailSkeleton />}

          {isError && (
            <div className="py-20 px-6 text-center">
              <h2 className="text-xl font-bold text-ink-900 mb-2">Кейс не найден</h2>
              <p className="text-ink-600 mb-6">
                Возможно, он был снят с публикации.
              </p>
              <button
                onClick={onClose}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-ink-900 text-white font-semibold hover:bg-ink-800"
              >
                Закрыть
              </button>
            </div>
          )}

          {data && (
            <article className="animate-fade-in">
              {data.cover_url && (
                <div className="relative w-full aspect-[16/9] sm:aspect-[20/9] overflow-hidden bg-ink-100">
                  <img
                    src={data.cover_url}
                    alt={data.title}
                    className="w-full h-full object-cover"
                  />
                  <div
                    className="absolute inset-0 bg-gradient-to-t from-white/0 via-transparent to-transparent"
                    aria-hidden
                  />
                </div>
              )}

              <div className="p-6 sm:p-8 md:p-10">
                <header className="mb-7">
                  <div className="flex items-center gap-3 mb-4 flex-wrap">
                    {data.logo_url ? (
                      <img
                        src={data.logo_url}
                        alt={data.company_name || data.title}
                        className="max-h-8 max-w-[120px] object-contain"
                      />
                    ) : (
                      data.industry && <Badge variant="brand">{data.industry}</Badge>
                    )}
                    {data.company_name && (
                      <span className="text-sm text-ink-500 font-medium">
                        {data.company_name}
                      </span>
                    )}
                  </div>
                  <h2
                    id="case-modal-title"
                    className="text-2xl md:text-3xl lg:text-4xl font-bold text-ink-900 tracking-tight leading-[1.15]"
                  >
                    {data.title}
                  </h2>
                  {data.subtitle && (
                    <p className="mt-3 text-base md:text-lg text-ink-600 leading-relaxed">
                      {data.subtitle}
                    </p>
                  )}
                  {(data.metric || data.metric_label) && (
                    <div className="mt-6 p-5 md:p-6 rounded-2xl bg-gradient-to-br from-ink-50 to-white border border-ink-200/70">
                      <div className="flex items-end gap-3 flex-wrap">
                        {data.metric && (
                          <span
                            className={`text-4xl md:text-5xl font-bold bg-gradient-to-br ${ACCENT_GRADIENT[data.accent]} bg-clip-text text-transparent leading-none`}
                          >
                            {data.metric}
                          </span>
                        )}
                        {data.metric_label && (
                          <span className="text-sm md:text-base text-ink-600 mb-1">
                            {data.metric_label}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </header>

                <div className="prose prose-ink max-w-none text-ink-800 leading-relaxed whitespace-pre-wrap text-base">
                  {data.body || 'Полный текст кейса скоро появится.'}
                </div>

                <div className="mt-10 p-6 md:p-7 rounded-2xl bg-gradient-to-br from-ink-900 to-ink-950 text-white">
                  <h3 className="text-lg md:text-xl font-bold mb-2">
                    Хотите похожий результат?
                  </h3>
                  <p className="text-ink-300 text-sm mb-5">
                    Ответьте на несколько вопросов ассистенту Baqsy AI — подберём формат
                    аудита под вашу отрасль.
                  </p>
                  <ChatLauncher variant="secondary" size="md">
                    Обсудить мой бизнес
                  </ChatLauncher>
                </div>
              </div>
            </article>
          )}
        </div>
      </div>
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div className="animate-pulse p-6 sm:p-8 md:p-10 space-y-4">
      <div className="h-7 w-32 bg-ink-100 rounded" />
      <div className="h-10 bg-ink-100 rounded w-3/4" />
      <div className="h-5 bg-ink-100 rounded w-5/6" />
      <div className="h-24 bg-ink-100 rounded" />
      <div className="space-y-2 pt-3">
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded w-5/6" />
        <div className="h-4 bg-ink-100 rounded w-4/6" />
      </div>
    </div>
  )
}
