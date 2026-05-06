import { useEffect, type ReactNode } from 'react'
import { Header } from '../layout/Header'
import { Footer } from '../layout/Footer'
import { Container } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { DockedChatPanel } from '../chat/ChatLauncher'

interface LegalPageProps {
  badge: string
  title: string
  lastUpdated: string
  children: ReactNode
}

export function LegalPage({ badge, title, lastUpdated, children }: LegalPageProps) {
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }, [])

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header variant="solid" />
      <main className="flex-1 pt-24 pb-16 md:pt-28">
        <Container size="sm">
          <div className="mb-10">
            <Badge variant="neutral" size="sm" className="mb-3">
              {badge}
            </Badge>
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight leading-[1.1]">
              {title}
            </h1>
            <p className="mt-3 text-sm text-ink-500">
              Последнее обновление: {lastUpdated}
            </p>
          </div>

          <article className="legal-prose space-y-6 text-base md:text-[17px] leading-relaxed text-ink-800">
            {children}
          </article>

          <div className="mt-14 p-6 rounded-2xl bg-ink-50 border border-ink-200/70">
            <h3 className="text-base font-bold text-ink-900 mb-2">
              Связаться с нами
            </h3>
            <p className="text-sm text-ink-600 mb-1">
              Email: <a href="mailto:info@baqsy.kz" className="font-semibold text-brand-700 hover:text-brand-600 underline underline-offset-2">info@baqsy.kz</a>
            </p>
            <p className="text-sm text-ink-600">
              WhatsApp: <a href="https://wa.me/77002259184" className="font-semibold text-brand-700 hover:text-brand-600 underline underline-offset-2" target="_blank" rel="noopener noreferrer">+7 (700) 225-91-84</a>
            </p>
          </div>
        </Container>
      </main>
      <Footer />
      <DockedChatPanel />
    </div>
  )
}

export function LegalSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-xl md:text-2xl font-bold text-ink-900 tracking-tight pt-2">
        {title}
      </h2>
      <div className="space-y-3 text-ink-700">{children}</div>
    </section>
  )
}

export function LegalList({ items }: { items: ReactNode[] }) {
  return (
    <ul className="space-y-2 list-disc pl-5 marker:text-ink-400">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  )
}
