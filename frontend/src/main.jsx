import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './assets/styles/global.css'
import { preloadSeaSignalLogos } from './components/SeaSignalLogo.jsx'
import App from './App.jsx'
import { initializeMsal } from './services/msalInstance.js'

preloadSeaSignalLogos()

async function bootstrap() {
  try {
    await initializeMsal()
  } catch {
    /* Azure may be unconfigured locally; login page surfaces a warning. */
  }

  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

bootstrap()
