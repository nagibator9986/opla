import { useState } from 'react'
import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'

interface FaqSectionProps {
  content: Record<string, string>
}

interface FaqItem {
  question: string
  answer: string
}

function getFaqItems(content: Record<string, string>): FaqItem[] {
  const items: FaqItem[] = []
  let n = 1
  while (content[`faq_${n}_q`]) {
    items.push({ question: content[`faq_${n}_q`], answer: content[`faq_${n}_a`] ?? '' })
    n++
  }
  return items
}

export function FaqSection({ content }: FaqSectionProps) {
  const items = getFaqItems(content)
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const toggle = (i: number) => setOpenIndex((prev) => (prev === i ? null : i))

  if (items.length === 0) return null

  return (
    <Section id="faq" background="white">
      <Container size="sm">
        <div className="text-center mb-12 md:mb-16">
          <Badge variant="neutral" className="mb-4">Вопросы и ответы</Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
            Частые вопросы
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            Не нашли ответ? Напишите в Telegram-бот — ответим в течение часа.
          </p>
        </div>

        <div className="space-y-3">
          {items.map((item, i) => {
            const isOpen = openIndex === i
            return (
              <div
                key={i}
                className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
                  isOpen
                    ? 'bg-white border-ink-300 shadow-[0_4px_14px_rgb(15_23_42_/_0.08)]'
                    : 'bg-white border-ink-200 hover:border-ink-300'
                }`}
              >
                <button
                  className="w-full flex items-center justify-between gap-4 px-5 md:px-6 py-4 md:py-5 text-left"
                  onClick={() => toggle(i)}
                  aria-expanded={isOpen}
                >
                  <span className="font-semibold text-ink-900 text-base md:text-lg leading-snug">
                    {item.question}
                  </span>
                  <span
                    className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200 ${
                      isOpen ? 'bg-brand-500 text-white rotate-45' : 'bg-ink-100 text-ink-600'
                    }`}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 4v12M4 10h12" />
                    </svg>
                  </span>
                </button>
                <div
                  className={`grid transition-all duration-300 ease-out ${
                    isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
                  }`}
                >
                  <div className="overflow-hidden">
                    <p className="px-5 md:px-6 pb-5 md:pb-6 text-ink-600 leading-relaxed">
                      {item.answer}
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Container>
    </Section>
  )
}
