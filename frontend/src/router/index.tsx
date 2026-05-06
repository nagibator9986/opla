import { createBrowserRouter } from 'react-router-dom'
import { LandingPage } from '../pages/LandingPage'
import { TariffsPage } from '../pages/TariffsPage'
import { CabinetPage } from '../pages/CabinetPage'
import { CasesPage } from '../pages/CasesPage'
import { CaseDetailPage } from '../pages/CaseDetailPage'
import { BlogPostPage } from '../pages/BlogPostPage'
import { InvitePage } from '../pages/InvitePage'
import { OfferPage } from '../pages/OfferPage'
import { PrivacyPage } from '../pages/PrivacyPage'
import { RefundPage } from '../pages/RefundPage'
import { ProtectedRoute } from './ProtectedRoute'

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/tariffs', element: <TariffsPage /> },
  { path: '/cases', element: <CasesPage /> },
  { path: '/cases/:slug', element: <CaseDetailPage /> },
  { path: '/blog/:slug', element: <BlogPostPage /> },
  { path: '/invite/:token', element: <InvitePage /> },
  { path: '/offer', element: <OfferPage /> },
  { path: '/privacy', element: <PrivacyPage /> },
  { path: '/refund', element: <RefundPage /> },
  { path: '/cabinet', element: <ProtectedRoute><CabinetPage /></ProtectedRoute> },
])
