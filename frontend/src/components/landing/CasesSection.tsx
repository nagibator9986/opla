import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { listCases, type CaseSummary } from '../../api/cases'

interface CasesSectionProps {
  content: Record<string, string>
}

const ACCENT_GRADIENT: Record<CaseSummary['accent'], string> = {
  emerald: 'from-emerald-400 to-emerald-600',
  sky: 'from-sky-400 to-indigo-500',
  amber: 'from-amber-400 to-orange-500',
  rose: 'from-rose-400 to-rose-600',
  violet: 'from-violet-400 to-purple-500',
  slate: 'from-slate-400 to-slate-600',
}

export function CasesSection({ content }: CasesSectionProps) {
  const { data: cases, isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: listCases,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <Section id="cases" background="ink-50">
      <Container>
        <div className="max-w-2xl mx-auto text-center mb-12 md:mb-16">
          <Badge variant="neutral" className="mb-4">Кейсы</Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
            {content.cases_title ?? 'Результаты наших клиентов'}
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            Реальные цифры из реальных компаний. Некоторые имена скрыты по запросу клиентов.
          </p>
        </div>

        {isLoading ? (
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
              <Link
                key={c.slug}
                to={`/cases/${c.slug}`}
                className="group relative overflow-hidden bg-white rounded-2xl p-7 md:p-8 border border-ink-200/70 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] hover:shadow-[0_10px_30px_rgb(15_23_42_/_0.1)] hover:-translate-y-1 transition-all duration-300 flex flex-col"
              >
                <div
                  aria-hidden
                  className={`absolute -top-24 -right-24 w-48 h-48 rounded-full bg-gradient-to-br ${ACCENT_GRADIENT[c.accent]} opacity-10 group-hover:opacity-20 transition-opacity blur-2xl`}
                />
                <div className="relative flex flex-col flex-1">
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
                    <svg className="w-8 h-8 text-ink-200" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2H4c-1.25 0-2 .75-2 2v4c0 1.25.75 2 2 2h2s.73 2.66-2.66 4c-.48.15-.35.85.66.85zm14 0c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2h-4c-1.25 0-2 .75-2 2v4c0 1.25.75 2 2 2h2s.73 2.66-2.66 4c-.48.15-.35.85.66.85z" />
                    </svg>
                  </div>
                  <h3 className="text-xl md:text-2xl font-bold text-ink-900 mb-3">{c.title}</h3>
                  <p className="text-ink-600 leading-relaxed mb-6 flex-1">
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
                        <span className="text-sm text-ink-500 mb-1">{c.metric_label}</span>
                      )}
                      <span className="ml-auto inline-flex items-center gap-1 text-sm font-semibold text-brand-700 group-hover:text-brand-600 mb-0.5">
                        Подробнее
                        <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </span>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </Container>
    </Section>
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
