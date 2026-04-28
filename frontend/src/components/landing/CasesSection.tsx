import { Link } from 'react-router-dom'

import { Container, Section } from '../ui/Container'

const TEASER_BRANDS: { slug: string; label: string }[] = [
  { slug: 'cocacola', label: 'Coca-Cola' },
  { slug: 'apple', label: 'Apple' },
  { slug: 'toyota', label: 'Toyota' },
  { slug: 'lvmh', label: 'LVMH' },
  { slug: 'netflix', label: 'Netflix' },
  { slug: 'tesla', label: 'Tesla' },
  { slug: 'samsung', label: 'Samsung' },
  { slug: 'amazon', label: 'Amazon' },
  { slug: 'google', label: 'Google' },
  { slug: 'meta', label: 'Meta' },
  { slug: 'microsoft', label: 'Microsoft' },
  { slug: 'sony', label: 'Sony' },
  { slug: 'nike', label: 'Nike' },
  { slug: 'adidas', label: 'Adidas' },
  { slug: 'mercedes', label: 'Mercedes' },
  { slug: 'spotify', label: 'Spotify' },
  { slug: 'ikea', label: 'IKEA' },
  { slug: 'ibm', label: 'IBM' },
  { slug: 'starbucks', label: 'Starbucks' },
  { slug: 'mcdonalds', label: 'McDonald’s' },
]

export function CasesSection() {
  return (
    <Section id="cases" background="ink-50">
      <Container>
        <TeaserLogoStrip />

        <div className="mt-12 md:mt-14 flex justify-center">
          <Link
            to="/cases"
            className="group inline-flex items-center gap-3 px-8 py-4 md:py-5 rounded-2xl bg-ink-900 text-white text-base md:text-lg font-semibold tracking-tight hover:bg-ink-800 transition-all shadow-[0_10px_30px_rgb(15_23_42_/_0.18)] hover:shadow-[0_14px_40px_rgb(15_23_42_/_0.28)] hover:-translate-y-0.5"
          >
            Смотреть кейсы мировых компаний
            <svg
              className="w-5 h-5 transition-transform group-hover:translate-x-1"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden
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
  const doubled = [...TEASER_BRANDS, ...TEASER_BRANDS]
  return (
    <div
      aria-label="Среди разборов — мировые компании"
      className="relative max-w-6xl mx-auto"
      style={{
        WebkitMaskImage:
          'linear-gradient(to right, transparent, black 8%, black 92%, transparent)',
        maskImage:
          'linear-gradient(to right, transparent, black 8%, black 92%, transparent)',
      }}
    >
      <p className="text-center text-[11px] uppercase tracking-[0.22em] text-ink-400 mb-7 md:mb-8">
        Среди разборов
      </p>
      <div className="overflow-hidden">
        <ul
          className="animate-marquee flex items-center gap-12 md:gap-20 grayscale opacity-70 hover:opacity-100 transition-opacity"
          style={{ width: 'max-content' }}
        >
          {doubled.map((b, i) => (
            <li
              key={`${b.slug}-${i}`}
              className="flex items-center justify-center shrink-0"
              aria-hidden={i >= TEASER_BRANDS.length}
            >
              <img
                src={`https://cdn.simpleicons.org/${b.slug}/0f172a`}
                alt={b.label}
                loading="lazy"
                className="h-9 md:h-12 w-auto select-none pointer-events-none"
                onError={(e) => {
                  const t = e.currentTarget
                  const fallback = document.createElement('span')
                  fallback.className =
                    'text-ink-700 font-bold tracking-wider text-base md:text-lg whitespace-nowrap'
                  fallback.textContent = b.label.toUpperCase()
                  t.replaceWith(fallback)
                }}
              />
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
