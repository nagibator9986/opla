import { useContentBlocks } from '../hooks/useContentBlocks'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { HeroSection } from '../components/landing/HeroSection'
import { MethodSection } from '../components/landing/MethodSection'
import { TariffsSection } from '../components/landing/TariffsSection'
import { CasesSection } from '../components/landing/CasesSection'
import { FaqSection } from '../components/landing/FaqSection'
import { CtaFooter } from '../components/landing/CtaFooter'

export function LandingPage() {
  const { data: content } = useContentBlocks()

  const c = content ?? {}

  return (
    <div className="scroll-smooth">
      <Header />
      <main className="pt-16">
        <HeroSection content={c} />
        <MethodSection content={c} />
        <TariffsSection content={c} />
        <CasesSection content={c} />
        <FaqSection content={c} />
        <CtaFooter />
      </main>
      <Footer />
    </div>
  )
}
