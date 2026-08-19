import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { createAppTheme, THEME_STORAGE_KEY } from '../config/theme.js'
import { readStoredEmployee } from '../services/auth.js'

const ThemeModeContext = createContext(null)

export function useThemeMode() {
  const ctx = useContext(ThemeModeContext)
  if (!ctx) throw new Error('useThemeMode must be used within ThemeProviderWrapper')
  return ctx
}

export function ThemeProviderWrapper({ children }) {
  const [mode, setMode] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    return localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
    if (readStoredEmployee()) {
      localStorage.setItem(THEME_STORAGE_KEY, mode)
    }
  }, [mode])

  const theme = useMemo(() => createAppTheme(mode), [mode])
  const toggleMode = () => setMode(m => (m === 'dark' ? 'light' : 'dark'))

  return (
    <ThemeModeContext.Provider value={{ mode, darkMode: mode === 'dark', setMode, toggleMode }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeModeContext.Provider>
  )
}
