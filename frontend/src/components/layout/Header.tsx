import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Logo } from '../ui/Logo'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/cn'

const navLinks = [
  { label: 'Метод', href: '#method' },
  { label: 'Тарифы', href: '#tariffs' },
  { label: 'Кейсы', href: '#cases' },
  { label: 'FAQ', href: '#faq' },
]

interface HeaderProps {
  variant?: 'transparent' | 'solid'
}

export function Header({ variant = 'solid' }: HeaderProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isLanding = location.pathname === '/'

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileOpen])

  useEffect(() => {
    // Close mobile nav when route changes — synchronising UI to an external
    // (router) signal is the intended use of useEffect here.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMobileOpen(false)
  }, [location.pathname])

  // When the header is over the dark hero (transparent variant, not scrolled,
  // mobile menu closed), flip all text/icons to the light palette so the
  // branding remains legible.
  const isOverDark = variant === 'transparent' && !scrolled && !mobileOpen

  const headerStyle = cn(
    'fixed top-0 inset-x-0 z-50 transition-all duration-300',
    isOverDark
      ? 'bg-transparent'
      : 'bg-white/85 backdrop-blur-xl border-b border-ink-200/70 shadow-[0_1px_2px_rgb(15_23_42_/_0.04)]',
  )

  const navLinkStyle = cn(
    'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
    isOverDark
      ? 'text-white/80 hover:text-white hover:bg-white/10'
      : 'text-ink-700 hover:text-ink-900 hover:bg-ink-100/70',
  )

  const ctaStyle = cn(
    'hidden sm:inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-colors',
    isOverDark
      ? 'bg-white text-ink-900 hover:bg-ink-100'
      : 'bg-ink-900 text-white hover:bg-ink-800',
  )

  const mobileBtnStyle = cn(
    'md:hidden inline-flex items-center justify-center w-10 h-10 rounded-lg transition-colors',
    isOverDark
      ? 'text-white hover:bg-white/10'
      : 'text-ink-700 hover:bg-ink-100',
  )

  return (
    <header className={headerStyle}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex-shrink-0 focus:outline-none" aria-label="Baqsy System — главная">
            <Logo variant={isOverDark ? 'light' : 'dark'} />
          </Link>

          {isLanding && (
            <nav className="hidden md:flex items-center gap-1" aria-label="Главное меню">
              {navLinks.map((link) => (
                <a key={link.href} href={link.href} className={navLinkStyle}>
                  {link.label}
                </a>
              ))}
            </nav>
          )}

          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <Link to="/cabinet" className={ctaStyle}>
                <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
                Кабинет
              </Link>
            ) : isLanding ? (
              <a href="#tariffs" className={ctaStyle}>
                Выбрать тариф
              </a>
            ) : (
              <Link to="/tariffs" className={ctaStyle}>
                Выбрать тариф
              </Link>
            )}

            <button
              className={mobileBtnStyle}
              onClick={() => setMobileOpen((v) => !v)}
              aria-label={mobileOpen ? 'Закрыть меню' : 'Открыть меню'}
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M4 12h16M4 17h10" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      <div
        className={cn(
          'md:hidden fixed inset-x-0 top-16 bottom-0 bg-white transition-all duration-300 overflow-y-auto',
          mobileOpen ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0 pointer-events-none',
        )}
      >
        <div className="px-4 py-6 space-y-1">
          {isLanding &&
            navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block px-4 py-3 rounded-xl text-base font-semibold text-ink-800 hover:bg-ink-50 transition-colors"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
          <div className="pt-4 border-t border-ink-100 space-y-2">
            {isAuthenticated ? (
              <Link
                to="/cabinet"
                className="block px-4 py-3 rounded-xl bg-ink-900 text-white text-base font-semibold text-center hover:bg-ink-800 transition-colors"
                onClick={() => setMobileOpen(false)}
              >
                Перейти в кабинет
              </Link>
            ) : isLanding ? (
              <a
                href="#tariffs"
                className="block px-4 py-3 rounded-xl bg-ink-900 text-white text-base font-semibold text-center hover:bg-ink-800 transition-colors"
                onClick={() => setMobileOpen(false)}
              >
                Выбрать тариф
              </a>
            ) : (
              <Link
                to="/tariffs"
                className="block px-4 py-3 rounded-xl bg-ink-900 text-white text-base font-semibold text-center hover:bg-ink-800 transition-colors"
                onClick={() => setMobileOpen(false)}
              >
                Выбрать тариф
              </Link>
            )}
            {/* Chat launcher is globally available via FloatingChatButton,
                we intentionally don't duplicate it in the mobile menu. */}
          </div>
        </div>
      </div>
    </header>
  )
}
