import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './assets/styles/global.css'
import { preloadSeaSignalLogos } from './components/SeaSignalLogo.jsx'
import App from './App.jsx'

preloadSeaSignalLogos()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
