import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'

interface MethodSectionProps {
  content: Record<string, string>
}

const steps = [
  {
    num: '01',
    label: 'Регистрация',
    desc: 'Напишите Telegram-боту. Мы задаём 5 коротких вопросов, чтобы понять, какая отрасль и анкета подойдут.',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 2L11 13" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    num: '02',
    label: 'Анкетирование',
    desc: 'Отраслевая анкета из 27 вопросов. Можно прерывать и возвращаться — бот сохранит прогресс.',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 11l3 3L22 4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    num: '03',
    label: 'Аудит и отчёт',
    desc: 'Наши эксперты пишут именной отчёт. Готовый PDF приходит в Telegram и WhatsApp за 3–5 дней.',
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
]

export function MethodSection({ content }: MethodSectionProps) {
  return (
    <Section id="method" background="ink-50">
      <Container>
        <div className="max-w-2xl mx-auto text-center mb-12 md:mb-16">
          <Badge variant="neutral" className="mb-4">
            Как это работает
          </Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
            {content.method_title ?? 'Наш метод'}
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            {content.method_text ??
              'Три простых шага от первого сообщения в Telegram до готового отчёта с разбором ключевых параметров бизнеса.'}
          </p>
        </div>

        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          <div
            aria-hidden
            className="hidden md:block absolute top-[3.75rem] left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-transparent via-ink-300 to-transparent"
          />

          {steps.map((step, idx) => (
            <div
              key={step.num}
              className="relative group bg-white rounded-2xl p-6 md:p-7 border border-ink-200/70 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)] hover:shadow-[0_10px_30px_rgb(15_23_42_/_0.1)] hover:-translate-y-1 transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${idx * 80}ms` }}
            >
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-5">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-md flex items-center justify-center ring-4 ring-white">
                    {step.icon}
                  </div>
                  <span className="text-5xl font-bold text-ink-100 group-hover:text-brand-100 transition-colors leading-none select-none">
                    {step.num}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-ink-900 mb-2">{step.label}</h3>
                <p className="text-ink-600 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  )
}
