import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import { useAuth } from '../../context/AuthContext.jsx'
import { useAppData } from '../../context/AppDataContext.jsx'
import { useThemeMode } from '../../context/ThemeProviderWrapper.jsx'
import { canManageFeedSources } from '../../services/auth.js'
import { technologyDomainNames } from '../../utils/articles.js'
import { DEFAULT_TECHNOLOGY_DOMAINS } from '../../constants/categories.js'
import Header from './Header.jsx'
import Sidebar from './Sidebar.jsx'
import Footer from './Footer.jsx'
import Breadcrumb from './Breadcrumb.jsx'

export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sessionEmployee, logout } = useAuth()
  const { darkMode, toggleMode } = useThemeMode()
  const {
    articles,
    feeds,
    technologyDomains,
    fetchFeedHealth,
    fetchFeeds,
  } = useAppData()

  const [drawerCollapsed, setDrawerCollapsed] = useState(false)
  const [selectedCat, setSelectedCat] = useState(DEFAULT_TECHNOLOGY_DOMAINS[0])

  const categories = technologyDomainNames(technologyDomains)

  useEffect(() => {
    if (categories.length && !categories.includes(selectedCat)) {
      setSelectedCat(categories[0])
    }
  }, [categories, selectedCat])

  const canManageSettings = canManageFeedSources(sessionEmployee)

  useEffect(() => {
    if (location.pathname === '/feed-health') fetchFeedHealth()
    if (location.pathname === '/settings') fetchFeeds()
  }, [location.pathname, fetchFeedHealth, fetchFeeds])

  const handleSelectCat = cat => {
    setSelectedCat(cat)
    if (location.pathname !== '/articles') {
      navigate('/articles')
    }
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
            <Outlet context={{ selectedCat }} />
          </Box>
          <Footer />
        </Box>
      </Box>
    </Box>
  )
}
