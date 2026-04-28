import { Link } from 'react-router-dom'

import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'

interface CasesSectionProps {
  content: Record<string, string>
}

const TEASER_BRANDS: { slug: string; label: string }[] = [
  { slug: 'cocacola', label: 'Coca-Cola' },
  { slug: 'apple', label: 'Apple' },
  { slug: 'toyota', label: 'Toyota' },
  { slug: 'lvmh', label: 'LVMH' },
  { slug: 'netflix', label: 'Netflix' },
]

export function CasesSection({ content: _content }: CasesSectionProps) {
  return (
    <Section id="cases" background="ink-50">
      <Container>
        <div className="max-w-2xl mx-auto text-center mb-8 md:mb-10">
          <Badge variant="neutral" className="mb-4">
            Кейсы мировых компаний
          </Badge>
        </div>

        <TeaserLogoStrip />

        <div className="mt-10 md:mt-12 flex justify-center">
          <Link
            to="/cases"
            className="inline-flex items-center gap-2 px-7 py-4 rounded-xl bg-ink-900 text-white font-semibold hover:bg-ink-800 transition-colors shadow-lg"
          >
            Смотреть кейсы
            <svg
              className="w-4 h-4"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </Link>
        </div>
      </Container>
    </Section>
  )
}

function TeaserLogoStrip() {
  return (
    <div
      aria-label="Примеры компаний, по которым доступны разборы"
      className="max-w-3xl mx-auto"
    >
      <p className="text-center text-[11px] uppercase tracking-[0.18em] text-ink-400 mb-5">
        Среди разборов
      </p>
      <ul className="flex flex-wrap items-center justify-center gap-x-8 gap-y-5 md:gap-x-12 grayscale opacity-60">
        {TEASER_BRANDS.map((b) => (
          <li key={b.slug} className="flex items-center justify-center">
            <img
              src={`https://cdn.simpleicons.org/${b.slug}/0f172a`}
              alt={b.label}
              loading="lazy"
              className="h-6 md:h-7 w-auto select-none pointer-events-none"
              onError={(e) => {
                const t = e.currentTarget
                const fallback = document.createElement('span')
                fallback.className =
                  'text-ink-700 font-bold tracking-wider text-sm md:text-base'
                fallback.textContent = b.label.toUpperCase()
                t.replaceWith(fallback)
              }}
            />
          </li>
        ))}
      </ul>
    </div>
  )
}
