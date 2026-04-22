import { useContentBlocks } from '../hooks/useContentBlocks'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { HeroSection } from '../components/landing/HeroSection'
import { MethodSection } from '../components/landing/MethodSection'
import { TariffsSection } from '../components/landing/TariffsSection'
import { TrustSection } from '../components/landing/TrustSection'
import { CasesSection } from '../components/landing/CasesSection'
import { FaqSection } from '../components/landing/FaqSection'
import { CtaFooter } from '../components/landing/CtaFooter'
import { FloatingChatButton } from '../components/chat/ChatLauncher'

export function LandingPage() {
  const { data: content } = useContentBlocks()
  const c = content ?? {}

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header variant="transparent" />
      <main className="flex-1">
        <HeroSection content={c} />
        <MethodSection content={c} />
        <TariffsSection content={c} />
        <TrustSection />
        <CasesSection content={c} />
        <FaqSection content={c} />
        <CtaFooter />
      </main>
      <Footer />
      <FloatingChatButton />
    </div>
  )
}
