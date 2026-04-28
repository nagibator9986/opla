import { useContentBlocks } from '../hooks/useContentBlocks'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { HeroSection } from '../components/landing/HeroSection'
import { BlogSection } from '../components/landing/BlogSection'
import { CasesSection } from '../components/landing/CasesSection'
import { FaqSection } from '../components/landing/FaqSection'
import { DockedChatPanel } from '../components/chat/ChatLauncher'

export function LandingPage() {
  const { data: content } = useContentBlocks()
  const c = content ?? {}

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header variant="transparent" />
      <main className="flex-1">
        <HeroSection content={c} />
        <BlogSection />
        <CasesSection content={c} />
        <FaqSection content={c} />
      </main>
      <Footer />
      <DockedChatPanel />
    </div>
  )
}
