import { NavLink, useLocation } from 'react-router-dom'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Badge from '@mui/material/Badge'
import Box from '@mui/material/Box'
import { useTheme } from '@mui/material/styles'
import { LAYOUT, BRAND } from '../../config/theme.js'
import { catCount, technologyDomainNames } from '../../utils/articles.js'
import {
  IconFeedHealth, IconSettings, IconPsychology, IconLightbulb, IconArticle,
} from './LayoutIcons.jsx'

function technologyDomainIcon(cat) {
  const icons = {
    AI: IconPsychology,
    'Expert Context': IconLightbulb,
  }
  return icons[cat] || IconArticle
}

function SidebarNavItem({ to, Icon, label, badge, collapsed, end = false, onClick }) {
  const theme = useTheme()

  return (
    <ListItemButton
      component={NavLink}
      to={to}
      end={end}
      onClick={onClick}
      sx={{
        borderRadius: 1.5,
        mx: 1,
        mb: 0.5,
        minHeight: 40,
        justifyContent: collapsed ? 'center' : 'flex-start',
        px: collapsed ? 1 : 2,
        '&.active': {
          bgcolor: alpha => theme.palette.mode === 'dark' ? 'rgba(49,133,36,0.15)' : BRAND.menuHover,
          color: BRAND.main,
          '& .MuiListItemIcon-root': { color: BRAND.main },
        },
      }}
    >
      <ListItemIcon sx={{ minWidth: collapsed ? 0 : 36, justifyContent: 'center' }}>
        {badge > 0 ? (
          <Badge badgeContent={badge} color="primary" max={999}>
            <Icon />
          </Badge>
        ) : (
          <Icon />
        )}
      </ListItemIcon>
      {!collapsed && <ListItemText primary={label} primaryTypographyProps={{ fontSize: 13 }} />}
    </ListItemButton>
  )
}

export default function Sidebar({
  articles,
  feeds,
  technologyDomains,
  selectedCat,
  onSelectCat,
  collapsed,
  showSettings,
}) {
  const location = useLocation()
  const theme = useTheme()
  const categories = technologyDomainNames(technologyDomains)
  const drawerWidth = collapsed ? LAYOUT.drawerCollapsed : LAYOUT.drawerWidth

  const bottomItems = [
    { to: '/feed-health', Icon: IconFeedHealth, label: 'Feed Health' },
    ...(showSettings ? [{ to: '/settings', Icon: IconSettings, label: 'Settings' }] : []),
  ]

  const handleCatClick = cat => {
    onSelectCat(cat)
  }

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          position: 'relative',
          borderRight: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          transition: theme.transitions.create('width'),
          overflowX: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <Box sx={{ flex: 1, overflowY: 'auto', pt: 1 }}>
        <List disablePadding>
          {categories.map(cat => {
            const count = catCount(articles, cat, feeds, technologyDomains)
            const Icon = technologyDomainIcon(cat)
            const isActive = location.pathname.startsWith('/articles') && selectedCat === cat
            return (
              <ListItemButton
                key={cat}
                selected={isActive}
                onClick={() => handleCatClick(cat)}
                sx={{
                  borderRadius: 1.5,
                  mx: 1,
                  mb: 0.5,
                  minHeight: 40,
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  px: collapsed ? 1 : 2,
                  '&.Mui-selected': {
                    bgcolor: theme.palette.mode === 'dark' ? 'rgba(49,133,36,0.15)' : BRAND.menuHover,
                    color: BRAND.main,
                    '& .MuiListItemIcon-root': { color: BRAND.main },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: collapsed ? 0 : 36, justifyContent: 'center' }}>
                  {count > 0 ? (
                    <Badge badgeContent={count} color="primary" max={999}>
                      <Icon />
                    </Badge>
                  ) : (
                    <Icon />
                  )}
                </ListItemIcon>
                {!collapsed && (
                  <ListItemText primary={cat} primaryTypographyProps={{ fontSize: 13 }} />
                )}
              </ListItemButton>
            )
          })}
        </List>
      </Box>

      <Box sx={{ borderTop: 1, borderColor: 'divider', py: 1 }}>
        <List disablePadding>
          {bottomItems.map(({ to, Icon, label }) => (
            <SidebarNavItem
              key={to}
              to={to}
              Icon={Icon}
              label={label}
              collapsed={collapsed}
            />
          ))}
        </List>
      </Box>
    </Drawer>
  )
}
