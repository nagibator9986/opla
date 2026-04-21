import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'

interface CasesSectionProps {
  content: Record<string, string>
}

interface CaseMeta {
  industry: string
  metric: string
  metricLabel: string
  accent: string
}

const CASE_META: CaseMeta[] = [
  {
    industry: 'Ритейл',
    metric: '+15%',
    metricLabel: 'маржинальности',
    accent: 'from-emerald-400 to-emerald-600',
  },
  {
    industry: 'IT-стартап',
    metric: '×2',
    metricLabel: 'скорость найма',
    accent: 'from-sky-400 to-indigo-500',
  },
]

export function CasesSection({ content }: CasesSectionProps) {
  const cases = [
    { title: content.case_1_title, text: content.case_1_text, meta: CASE_META[0] },
    { title: content.case_2_title, text: content.case_2_text, meta: CASE_META[1] },
  ].filter((c) => c.title)

  return (
    <Section id="cases" background="ink-50">
      <Container>
        <div className="max-w-2xl mx-auto text-center mb-12 md:mb-16">
          <Badge variant="neutral" className="mb-4">Кейсы</Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
            {content.cases_title ?? 'Результаты наших клиентов'}
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            Реальные цифры из реальных компаний. Имена клиентов скрыты по запросу.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
          {cases.map((c, i) => (
            <article
              key={i}
              className="group relative overflow-hidden bg-white rounded-2xl p-7 md:p-8 border border-ink-200/70 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] hover:shadow-[0_10px_30px_rgb(15_23_42_/_0.1)] hover:-translate-y-1 transition-all duration-300"
            >
              <div
                aria-hidden
                className={`absolute -top-24 -right-24 w-48 h-48 rounded-full bg-gradient-to-br ${c.meta.accent} opacity-10 group-hover:opacity-20 transition-opacity blur-2xl`}
              />
              <div className="relative">
                <div className="flex items-center justify-between mb-5">
                  <Badge variant="neutral" size="sm">{c.meta.industry}</Badge>
                  <svg className="w-8 h-8 text-ink-200" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2H4c-1.25 0-2 .75-2 2v4c0 1.25.75 2 2 2h2s.73 2.66-2.66 4c-.48.15-.35.85.66.85zm14 0c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2h-4c-1.25 0-2 .75-2 2v4c0 1.25.75 2 2 2h2s.73 2.66-2.66 4c-.48.15-.35.85.66.85z" />
                  </svg>
                </div>
                <h3 className="text-xl md:text-2xl font-bold text-ink-900 mb-3">{c.title}</h3>
                <p className="text-ink-600 leading-relaxed mb-6">{c.text}</p>
                <div className="flex items-end gap-3 pt-5 border-t border-ink-100">
                  <span className={`text-4xl md:text-5xl font-bold bg-gradient-to-br ${c.meta.accent} bg-clip-text text-transparent leading-none`}>
                    {c.meta.metric}
                  </span>
                  <span className="text-sm text-ink-500 mb-1">{c.meta.metricLabel}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </Container>
    </Section>
  )
}
