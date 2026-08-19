import { Link as RouterLink, useLocation } from 'react-router-dom'
import Box from '@mui/material/Box'
import Breadcrumbs from '@mui/material/Breadcrumbs'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'
import { IconHome } from './LayoutIcons.jsx'

export default function Breadcrumb({ selectedCat }) {
  const location = useLocation()
  const path = location.pathname

  const pageLabel = path.includes('/feed-health')
    ? 'Feed Health'
    : path.includes('/settings')
      ? 'Settings'
      : selectedCat || 'Articles'

  return (
    <Box sx={{ px: 2.5, py: 1.5, flexShrink: 0 }}>
      <Breadcrumbs separator="/" sx={{ fontSize: 13 }}>
        <Link
          component={RouterLink}
          to="/articles"
          underline="hover"
          color="inherit"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          <IconHome />
          Home
        </Link>
        <Typography color="text.primary" fontSize={13} fontWeight={500}>
          {pageLabel}
        </Typography>
      </Breadcrumbs>
    </Box>
  )
}
