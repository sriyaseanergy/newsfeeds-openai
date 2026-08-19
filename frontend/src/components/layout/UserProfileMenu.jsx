import { useEffect, useRef, useState } from 'react'
import Avatar from '@mui/material/Avatar'
import IconButton from '@mui/material/IconButton'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Divider from '@mui/material/Divider'
import Typography from '@mui/material/Typography'
import { IconPerson, IconLogout } from './LayoutIcons.jsx'

export default function UserProfileMenu({ sessionEmployee, onLogout }) {
  const [anchorEl, setAnchorEl] = useState(null)
  const avatarLetter = (sessionEmployee?.name || 'U').charAt(0).toUpperCase()

  const handleOpen = e => setAnchorEl(e.currentTarget)
  const handleClose = () => setAnchorEl(null)

  const handleLogout = () => {
    handleClose()
    onLogout()
  }

  return (
    <>
      <IconButton onClick={handleOpen} sx={{ p: 0.5 }}>
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: 'primary.main',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {avatarLetter}
        </Avatar>
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{ paper: { sx: { minWidth: 220, mt: 1 } } }}
      >
        {sessionEmployee && (
          <MenuItem disabled sx={{ opacity: '1 !important', flexDirection: 'column', alignItems: 'flex-start', py: 1.5 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              {sessionEmployee.name || '—'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {sessionEmployee.email || ''}
            </Typography>
          </MenuItem>
        )}
        <Divider />
        <MenuItem onClick={handleClose}>
          <ListItemIcon><IconPerson /></ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
          <ListItemIcon sx={{ color: 'error.main' }}><IconLogout /></ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>
    </>
  )
}
