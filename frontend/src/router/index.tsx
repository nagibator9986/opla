import { createBrowserRouter } from 'react-router-dom'
import { LandingPage } from '../pages/LandingPage'
import { TariffsPage } from '../pages/TariffsPage'
import { CabinetPage } from '../pages/CabinetPage'
import { CaseDetailPage } from '../pages/CaseDetailPage'
import { ProtectedRoute } from './ProtectedRoute'

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/tariffs', element: <TariffsPage /> },
  { path: '/cases/:slug', element: <CaseDetailPage /> },
  { path: '/cabinet', element: <ProtectedRoute><CabinetPage /></ProtectedRoute> },
])
