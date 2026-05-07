/* eslint-disable react-refresh/only-export-components */
import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { LandingPage } from '../pages/LandingPage'
import { TariffsPage } from '../pages/TariffsPage'
import { CasesPage } from '../pages/CasesPage'
import { ProtectedRoute } from './ProtectedRoute'
import { PageFallback } from './PageFallback'

// Lazy-load редко открываемые страницы — уменьшает initial bundle (~50%).
const CabinetPage = lazy(() => import('../pages/CabinetPage').then((m) => ({ default: m.CabinetPage })))
const CaseDetailPage = lazy(() => import('../pages/CaseDetailPage').then((m) => ({ default: m.CaseDetailPage })))
const BlogPostPage = lazy(() => import('../pages/BlogPostPage').then((m) => ({ default: m.BlogPostPage })))
const InvitePage = lazy(() => import('../pages/InvitePage').then((m) => ({ default: m.InvitePage })))
const OfferPage = lazy(() => import('../pages/OfferPage').then((m) => ({ default: m.OfferPage })))
const PrivacyPage = lazy(() => import('../pages/PrivacyPage').then((m) => ({ default: m.PrivacyPage })))
const RefundPage = lazy(() => import('../pages/RefundPage').then((m) => ({ default: m.RefundPage })))
const MagicLinkPage = lazy(() => import('../pages/MagicLinkPage').then((m) => ({ default: m.MagicLinkPage })))

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/tariffs', element: <TariffsPage /> },
  { path: '/cases', element: <CasesPage /> },
  {
    path: '/cases/:slug',
    element: <Suspense fallback={<PageFallback />}><CaseDetailPage /></Suspense>,
  },
  {
    path: '/blog/:slug',
    element: <Suspense fallback={<PageFallback />}><BlogPostPage /></Suspense>,
  },
  {
    path: '/invite/:token',
    element: <Suspense fallback={<PageFallback />}><InvitePage /></Suspense>,
  },
  {
    path: '/offer',
    element: <Suspense fallback={<PageFallback />}><OfferPage /></Suspense>,
  },
  {
    path: '/privacy',
    element: <Suspense fallback={<PageFallback />}><PrivacyPage /></Suspense>,
  },
  {
    path: '/refund',
    element: <Suspense fallback={<PageFallback />}><RefundPage /></Suspense>,
  },
  {
    path: '/auth/magic/:token',
    element: <Suspense fallback={<PageFallback />}><MagicLinkPage /></Suspense>,
  },
  {
    path: '/cabinet',
    element: (
      <ProtectedRoute>
        <Suspense fallback={<PageFallback />}>
          <CabinetPage />
        </Suspense>
      </ProtectedRoute>
    ),
  },
])
