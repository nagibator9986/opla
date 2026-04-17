import { createBrowserRouter } from 'react-router-dom'
import { LandingPage } from '../pages/LandingPage'
import { TariffsPage } from '../pages/TariffsPage'
import { AuthPage } from '../pages/AuthPage'
import { CabinetPage } from '../pages/CabinetPage'
import { ProtectedRoute } from './ProtectedRoute'

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/tariffs', element: <TariffsPage /> },
  { path: '/auth/:uuid', element: <AuthPage /> },
  { path: '/cabinet', element: <ProtectedRoute><CabinetPage /></ProtectedRoute> },
])
