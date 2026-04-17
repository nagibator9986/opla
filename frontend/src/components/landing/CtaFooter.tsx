import { Button } from '../ui/Button'

export function CtaFooter() {
  return (
    <section className="py-20 bg-slate-900 text-white text-center">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Готовы к аудиту?</h2>
        <p className="text-slate-300 text-lg mb-10">
          Начните прямо сейчас в Telegram-боте. Это займёт всего несколько минут.
        </p>
        <a href="https://t.me/baqsy_bot" target="_blank" rel="noopener noreferrer">
          <Button variant="secondary" size="lg">
            Начать в Telegram
          </Button>
        </a>
      </div>
    </section>
  )
}
