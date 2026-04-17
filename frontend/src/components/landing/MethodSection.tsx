interface MethodSectionProps {
  content: Record<string, string>
}

const steps = [
  { num: '01', label: 'Регистрация', desc: 'Начните с Telegram-бота для базовой категоризации' },
  { num: '02', label: 'Анкетирование', desc: 'Заполните отраслевую анкету из 27 вопросов' },
  { num: '03', label: 'Аудит', desc: 'Наши эксперты анализируют ваш бизнес за 3-5 дней' },
]

export function MethodSection({ content }: MethodSectionProps) {
  return (
    <section id="method" className="py-20 bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            {content.method_title}
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">{content.method_text}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step) => (
            <div key={step.num} className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-500 text-white text-xl font-bold mb-4">
                {step.num}
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">{step.label}</h3>
              <p className="text-slate-600">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
