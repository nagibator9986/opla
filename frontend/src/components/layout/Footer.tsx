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
      { label: 'WhatsApp', href: 'https://wa.me/77002259184', external: true },
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
              Персональный бизнес-аудит для компаний Казахстана.
              Живой эксперт, именной PDF, доставка в WhatsApp за 3–5 дней.
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
            <span className="text-xs text-ink-500">Оплата через CloudPayments KZ • Powered by OpenAI</span>
          </div>
        </div>
      </Container>
    </footer>
  )
}
