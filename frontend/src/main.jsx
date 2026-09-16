import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './assets/styles/global.css'
import { preloadSeaSignalLogos } from './components/SeaSignalLogo.jsx'
import App from './App.jsx'
import { initializeMsal } from './services/msalInstance.js'

/**
 * loginPopup monitors its child window and must read the OAuth response hash
 * itself. Booting this SPA in that child can run handleRedirectPromise or a
 * router navigation first, clearing the hash before the opener reads it.
 */
function isPopupAuthCallback() {
  if (typeof window === 'undefined' || !window.opener) return false
  const response = `${window.location.search}${window.location.hash}`
  return /(?:^|[?#&])(code|error|state)=/.test(response)
}

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

if (!isPopupAuthCallback()) {
  preloadSeaSignalLogos()
  bootstrap()
}
