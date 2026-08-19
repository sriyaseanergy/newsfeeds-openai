import { useCallback, useEffect, useRef, useState } from 'react'
import { Outlet, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import { useAuth } from '../../context/AuthContext.jsx'
import { useAppData } from '../../context/AppDataContext.jsx'
import { useThemeMode } from '../../context/ThemeProviderWrapper.jsx'
import { canManageFeedSources } from '../../services/auth.js'
import { technologyDomainNames } from '../../utils/articles.js'
import { DEFAULT_TECHNOLOGY_DOMAINS } from '../../constants/categories.js'
import { RIGHT_PANEL_INITIAL_MS, RIGHT_PANEL_MAX_MS } from '../../constants/categories.js'
import Header from './Header.jsx'
import Sidebar from './Sidebar.jsx'
import Footer from './Footer.jsx'
import Breadcrumb from './Breadcrumb.jsx'
import RightPanel from './RightPanel.jsx'
import { IconChevronLeft } from './LayoutIcons.jsx'

export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { sessionEmployee, logout } = useAuth()
  const { darkMode, toggleMode } = useThemeMode()
  const {
    articles,
    feeds,
    technologyDomains,
    statusData,
    feedHealth,
    recipients,
    apiError,
    fetched,
    fetchFeedHealth,
    fetchFeeds,
    fetchTechnologyDomains,
    fetchRecipients,
  } = useAppData()

  const [drawerCollapsed, setDrawerCollapsed] = useState(false)
  const [rightPanelOpen, setRightPanelOpen] = useState(true)
  const rightPanelTimersRef = useRef({ short: null, max: null })
  const rightPanelManualOpenRef = useRef(false)

  const categories = technologyDomainNames(technologyDomains)
  const catFromUrl = searchParams.get('cat')
  const selectedCat = catFromUrl && categories.includes(catFromUrl)
    ? catFromUrl
    : categories[0] || DEFAULT_TECHNOLOGY_DOMAINS[0]

  const canManageSettings = canManageFeedSources(sessionEmployee)

  useEffect(() => {
    if (location.pathname === '/feed-health') fetchFeedHealth()
    if (location.pathname === '/settings') {
      fetchFeeds()
      fetchTechnologyDomains()
      fetchRecipients()
    }
  }, [location.pathname, fetchFeedHealth, fetchFeeds, fetchTechnologyDomains, fetchRecipients])

  const clearRightPanelTimers = useCallback(() => {
    const { short, max } = rightPanelTimersRef.current
    if (short) clearTimeout(short)
    if (max) clearTimeout(max)
    rightPanelTimersRef.current = { short: null, max: null }
  }, [])

  const closeRightPanel = useCallback(() => {
    clearRightPanelTimers()
    setRightPanelOpen(false)
  }, [clearRightPanelTimers])

  const scheduleRightPanelAutoClose = useCallback(({ shortDelay = false } = {}) => {
    clearRightPanelTimers()
    if (shortDelay) {
      rightPanelTimersRef.current.short = setTimeout(() => {
        setRightPanelOpen(false)
        clearRightPanelTimers()
      }, RIGHT_PANEL_INITIAL_MS)
    }
    rightPanelTimersRef.current.max = setTimeout(() => {
      setRightPanelOpen(false)
      clearRightPanelTimers()
    }, RIGHT_PANEL_MAX_MS)
  }, [clearRightPanelTimers])

  const openRightPanel = useCallback(() => {
    setRightPanelOpen(true)
    const isFirstManual = !rightPanelManualOpenRef.current
    rightPanelManualOpenRef.current = true
    scheduleRightPanelAutoClose({ shortDelay: isFirstManual })
  }, [scheduleRightPanelAutoClose])

  useEffect(() => {
    scheduleRightPanelAutoClose({ shortDelay: true })
    return clearRightPanelTimers
  }, [scheduleRightPanelAutoClose, clearRightPanelTimers])

  const handleSelectCat = cat => {
    navigate(`/articles?cat=${encodeURIComponent(cat)}`)
  }

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
        overflow: 'hidden',
      }}
    >
      <Header
        sessionEmployee={sessionEmployee}
        onLogout={logout}
        collapsed={drawerCollapsed}
        onToggleDrawer={() => setDrawerCollapsed(c => !c)}
        darkMode={darkMode}
        onToggleDarkMode={toggleMode}
      />

      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <Sidebar
          articles={articles}
          feeds={feeds}
          technologyDomains={technologyDomains}
          selectedCat={selectedCat}
          onSelectCat={handleSelectCat}
          collapsed={drawerCollapsed}
          showSettings={canManageSettings}
        />

        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
          <Breadcrumb selectedCat={selectedCat} />
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', px: 2, pb: 1, minHeight: 0, overflow: 'hidden' }}>
            <Outlet />
          </Box>
          <Footer />
        </Box>

        <Box sx={{ position: 'relative', flexShrink: 0, display: 'flex' }}>
          {rightPanelOpen ? (
            <RightPanel
              statusData={statusData}
              feedHealth={feedHealth}
              recipients={recipients}
              apiError={apiError}
              fetched={fetched}
              onClose={closeRightPanel}
            />
          ) : (
            <Box
              sx={{
                width: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderLeft: 1,
                borderColor: 'divider',
              }}
            >
              <IconButton size="small" onClick={openRightPanel} title="Open status panel">
                <IconChevronLeft size={18} />
              </IconButton>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  )
}
