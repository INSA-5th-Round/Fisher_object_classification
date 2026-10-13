import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/common.css'
import './components/layout/sidebar.css'
import './components/layout/app-shell.css'
import './components/layout/topbar.css'
import './pages/dashboard.css'
import './components/cctv/cctv.css'
import './components/detections/detections.css'
import './components/statistics/statistics.css'
import './components/reports/reports.css'
import './components/users/users.css'
import './components/alerts/alerts.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
