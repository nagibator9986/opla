import { Button } from '../ui/Button'

interface HeroSectionProps {
  content: Record<string, string>
}

export function HeroSection({ content }: HeroSectionProps) {
  const handleScroll = () => {
    document.getElementById('tariffs')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="min-h-screen flex items-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="inline-flex items-center px-4 py-2 rounded-full bg-amber-500/20 text-amber-400 text-sm font-medium mb-8">
          Профессиональный бизнес-аудит
        </div>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight mb-6">
          {content.hero_title}
        </h1>
        <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-10">
          {content.hero_subtitle}
        </p>
        <Button variant="secondary" size="lg" onClick={handleScroll}>
          {content.hero_cta}
        </Button>
      </div>
    </section>
  )
}
