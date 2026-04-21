import { Container } from '../ui/Container'
import { Logo } from '../ui/Logo'

const sections = [
  {
    title: 'Продукт',
    links: [
      { label: 'Метод', href: '/#method' },
      { label: 'Тарифы', href: '/#tariffs' },
      { label: 'Кейсы', href: '/#cases' },
      { label: 'FAQ', href: '/#faq' },
    ],
  },
  {
    title: 'Контакты',
    links: [
      { label: 'info@baqsy.kz', href: 'mailto:info@baqsy.kz' },
      { label: 'Telegram-бот', href: 'https://t.me/Baqsysystembot', external: true },
      { label: 'WhatsApp', href: 'https://wa.me/77000000000', external: true },
    ],
  },
  {
    title: 'Компания',
    links: [
      { label: 'Публичная оферта', href: '/offer' },
      { label: 'Политика конфиденциальности', href: '/privacy' },
    ],
  },
]

export function Footer() {
  return (
    <footer className="bg-ink-950 text-ink-300 pt-16 pb-8">
      <Container>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-10 pb-12 border-b border-white/10">
          <div className="col-span-2 md:col-span-1">
            <Logo variant="light" />
            <p className="mt-4 text-sm text-ink-400 leading-relaxed max-w-xs">
              Персональный бизнес-аудит для компаний Казахстана. Отчёт в Telegram и WhatsApp за 3–5 дней.
            </p>
          </div>

          {sections.map((section) => (
            <div key={section.title}>
              <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
                {section.title}
              </h4>
              <ul className="space-y-2.5">
                {section.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      target={'external' in link && link.external ? '_blank' : undefined}
                      rel={'external' in link && link.external ? 'noopener noreferrer' : undefined}
                      className="text-sm text-ink-400 hover:text-white transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-ink-500">
            &copy; {new Date().getFullYear()} Baqsy System. Все права защищены.
          </p>
          <div className="flex items-center gap-4">
            <a
              href="https://t.me/Baqsysystembot"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-white/5 text-ink-300 hover:bg-white/10 hover:text-white transition-colors"
              aria-label="Telegram"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z" />
              </svg>
            </a>
            <span className="text-xs text-ink-500">Оплата через CloudPayments KZ</span>
          </div>
        </div>
      </Container>
    </footer>
  )
}
