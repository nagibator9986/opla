import { Container, Section } from '../ui/Container'

const TRUST_ITEMS = [
  {
    title: 'Конфиденциальность',
    text: 'Ответы анкеты шифруются и доступны только эксперту, готовящему ваш отчёт. Никаких рассылок.',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="11" width="18" height="11" rx="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 11V7a5 5 0 0110 0v4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    title: 'Безопасная оплата',
    text: 'CloudPayments KZ с 3-D Secure и HMAC-подписью вебхуков. Реквизиты карты не хранятся на стороне сервиса.',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="5" width="18" height="14" rx="2" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="3" y1="10" x2="21" y2="10" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="7" y1="15" x2="11" y2="15" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    title: 'Именной отчёт',
    text: 'PDF оформлен в фирменном стиле с реквизитами вашей компании. Можно показывать команде и партнёрам.',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6M9 14l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    title: 'Поддержка',
    text: 'Живой менеджер в Telegram отвечает в течение часа в рабочее время и помогает довести анкету до конца.',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
]

export function TrustSection() {
  return (
    <Section background="white" className="!py-14 md:!py-20">
      <Container>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 md:gap-6">
          {TRUST_ITEMS.map((item) => (
            <div
              key={item.title}
              className="group flex flex-col gap-3 p-5 md:p-6 rounded-2xl bg-white border border-ink-200/70 hover:border-brand-300 hover:shadow-[0_6px_20px_rgb(15_23_42_/_0.06)] transition-all duration-300"
            >
              <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-700 group-hover:bg-brand-500 group-hover:text-white transition-colors flex items-center justify-center">
                {item.icon}
              </div>
              <div>
                <h3 className="font-bold text-ink-900 mb-1.5">{item.title}</h3>
                <p className="text-sm text-ink-600 leading-relaxed">{item.text}</p>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  )
}
