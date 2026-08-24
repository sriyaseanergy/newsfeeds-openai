import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Typography from '@mui/material/Typography'
import { useTheme } from '@mui/material/styles'
import { BRAND, FONT_FAMILY, LAYOUT } from '../../config/theme.js'
import {
  IconNotes, IconDarkMode, IconLightMode, IconChevronRight,
} from './LayoutIcons.jsx'
import SeanergyBrandLogo from './SeanergyBrandLogo.jsx'
import UserProfileMenu from './UserProfileMenu.jsx'

export default function Header({
  sessionEmployee,
  onLogout,
  collapsed,
  onToggleDrawer,
  darkMode,
  onToggleDarkMode,
}) {
  const theme = useTheme()
  const drawerWidth = collapsed ? LAYOUT.drawerCollapsed : LAYOUT.drawerWidth

  return (
    <AppBar
      position="static"
      elevation={1}
      sx={{
        bgcolor: 'background.paper',
        color: 'text.primary',
        borderBottom: 1,
        borderColor: 'divider',
        height: LAYOUT.headerHeight,
        justifyContent: 'center',
      }}
    >
      <Toolbar disableGutters sx={{ minHeight: `${LAYOUT.headerHeight}px !important`, px: 0 }}>
        <Box
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: theme.transitions.create('width'),
            borderRight: 1,
            borderColor: 'divider',
            height: LAYOUT.headerHeight,
          }}
        >
          <SeanergyBrandLogo collapsed={collapsed} darkMode={darkMode} />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 1.5 }}>
          <IconButton
            onClick={onToggleDrawer}
            title={collapsed ? 'Expand menu' : 'Collapse menu'}
            sx={{ color: BRAND.main }}
          >
            {collapsed ? (
              <IconChevronRight size={25} color={BRAND.main} />
            ) : (
              <IconNotes size={30} color={BRAND.main} />
            )}
          </IconButton>
          <Typography
            sx={{
              fontFamily: FONT_FAMILY,
              fontSize: 20,
              fontWeight: 500,
              color: 'text.primary',
              letterSpacing: '0.02em',
            }}
          >
            Feed Alerts Engine
          </Typography>
        </Box>

        <Box sx={{ flex: 1 }} />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, pr: 2 }}>
          <IconButton
            onClick={onToggleDarkMode}
            title={darkMode ? 'Light mode' : 'Dark mode'}
            sx={{
              color: darkMode ? '#ffffff' : 'text.secondary',
              '&:hover': {
                bgcolor: 'action.hover',
                color: darkMode ? '#ffffff' : 'text.secondary',
              },
            }}
          >
            {darkMode ? <IconLightMode /> : <IconDarkMode />}
          </IconButton>
          <UserProfileMenu sessionEmployee={sessionEmployee} onLogout={onLogout} />
        </Box>
      </Toolbar>
    </AppBar>
  )
}
