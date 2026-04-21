import { useState } from 'react'

const navLinks = [
  { label: 'Метод', href: '#method' },
  { label: 'Тарифы', href: '#tariffs' },
  { label: 'Кейсы', href: '#cases' },
  { label: 'FAQ', href: '#faq' },
]

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="fixed top-0 w-full z-50 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="/" className="text-xl font-bold text-slate-900 flex-shrink-0">
            Baqsy System
          </a>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-slate-700 hover:text-slate-950 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 rounded"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* CTA + hamburger */}
          <div className="flex items-center gap-3">
            <a
              href="#tariffs"
              className="hidden md:inline-flex items-center px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors"
            >
              Выбрать тариф
            </a>
            <button
              className="md:hidden p-2 text-slate-600 hover:text-slate-900"
              onClick={() => setMobileOpen((v) => !v)}
              aria-label="Открыть меню"
            >
              {mobileOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-slate-200 py-4 space-y-2">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block px-2 py-2 text-slate-700 hover:text-slate-900 font-medium"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <a
              href="#tariffs"
              className="block mt-2 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold text-center hover:bg-slate-800 transition-colors"
              onClick={() => setMobileOpen(false)}
            >
              Выбрать тариф
            </a>
          </div>
        )}
      </div>
    </header>
  )
}
