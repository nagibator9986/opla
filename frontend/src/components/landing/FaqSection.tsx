import { useState } from 'react'

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
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const toggle = (i: number) => setOpenIndex((prev) => (prev === i ? null : i))

  return (
    <section id="faq" className="py-20 bg-white">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900">Частые вопросы</h2>
        </div>

        <div className="space-y-3">
          {items.map((item, i) => (
            <div key={i} className="border border-slate-200 rounded-xl overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-6 py-4 text-left font-semibold text-slate-900 hover:bg-slate-50 transition-colors"
                onClick={() => toggle(i)}
              >
                <span>{item.question}</span>
                <svg
                  className={`w-5 h-5 flex-shrink-0 text-slate-500 transition-transform duration-200 ${
                    openIndex === i ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div
                className={`overflow-hidden transition-all duration-300 ${
                  openIndex === i ? 'max-h-96' : 'max-h-0'
                }`}
              >
                <p className="px-6 pb-4 text-slate-600">{item.answer}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
