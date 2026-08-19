import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import InputBase from '@mui/material/InputBase'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import seanergyLogo from '../../assets/images/seanergy-logo.png'
import seanergyIcon from '../../assets/images/seanergy-icon.png'
import { BRAND, LAYOUT } from '../../config/theme.js'
import {
  IconNotes, IconSearch, IconDarkMode, IconLightMode, IconNotifications,
  IconChevronRight,
} from './LayoutIcons.jsx'
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
          {collapsed ? (
            <Box component="img" src={seanergyIcon} alt="seanergy.ai" sx={{ height: 32, width: 'auto' }} />
          ) : (
            <Box component="img" src={seanergyLogo} alt="seanergy.ai" sx={{ height: 36, width: 'auto', px: 2 }} />
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 1.5 }}>
          <IconButton onClick={onToggleDrawer} title={collapsed ? 'Expand menu' : 'Collapse menu'}>
            {collapsed ? <IconChevronRight size={25} /> : <IconNotes size={30} color={BRAND.main} />}
          </IconButton>
          <Typography variant="body2" fontWeight={500} color="text.secondary">
            Feed Alerts Engine
          </Typography>
        </Box>

        <Box sx={{ flex: 1 }} />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, pr: 2 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              bgcolor: alpha(theme.palette.text.primary, 0.04),
              borderRadius: 2,
              px: 1.5,
              py: 0.5,
              mr: 1,
              border: 1,
              borderColor: 'divider',
            }}
          >
            <InputBase
              placeholder="Search articles, feeds..."
              readOnly
              sx={{ fontSize: 13, width: 200 }}
            />
            <IconSearch />
          </Box>
          <IconButton
            onClick={onToggleDarkMode}
            title={darkMode ? 'Light mode' : 'Dark mode'}
            color={darkMode ? 'primary' : 'default'}
          >
            {darkMode ? <IconLightMode /> : <IconDarkMode />}
          </IconButton>
          <IconButton title="Notifications">
            <IconNotifications />
          </IconButton>
          <UserProfileMenu sessionEmployee={sessionEmployee} onLogout={onLogout} />
        </Box>
      </Toolbar>
    </AppBar>
  )
}
