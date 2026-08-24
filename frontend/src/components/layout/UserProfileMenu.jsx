import { useState } from 'react'
import Avatar from '@mui/material/Avatar'
import IconButton from '@mui/material/IconButton'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import Divider from '@mui/material/Divider'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import CloseIcon from '@mui/icons-material/Close'
import { FONT_FAMILY } from '../../config/theme.js'
import { IconPerson, IconLogout } from './LayoutIcons.jsx'

const menuItemSx = {
  color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : theme.palette.text.primary),
  '& .MuiListItemIcon-root': {
    color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : theme.palette.text.primary),
    minWidth: 36,
  },
  '& .MuiListItemText-primary': {
    color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : theme.palette.text.primary),
  },
  '&:hover': {
    color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : theme.palette.text.primary),
    '& .MuiListItemIcon-root': {
      color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : theme.palette.text.primary),
    },
    '& .MuiListItemText-primary': {
      color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : theme.palette.text.primary),
    },
  },
}

export default function UserProfileMenu({ sessionEmployee, onLogout }) {
  const [anchorEl, setAnchorEl] = useState(null)
  const [profileOpen, setProfileOpen] = useState(false)
  const avatarLetter = (sessionEmployee?.name || 'U').charAt(0).toUpperCase()

  const handleOpen = e => setAnchorEl(e.currentTarget)
  const handleClose = () => setAnchorEl(null)

  const handleProfileOpen = () => {
    handleClose()
    setProfileOpen(true)
  }

  const handleProfileClose = () => setProfileOpen(false)

  const handleLogout = () => {
    handleClose()
    onLogout()
  }

  return (
    <>
      <IconButton
        onClick={handleOpen}
        disableRipple
        sx={{
          p: 0.5,
          '&:hover': { bgcolor: 'transparent' },
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: '#ffffff',
            color: '#000000',
            fontSize: 14,
            fontWeight: 600,
            border: 1,
            borderColor: 'divider',
          }}
        >
          {avatarLetter}
        </Avatar>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        disableRestoreFocus
        disableAutoFocusItem
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{ paper: { sx: { minWidth: 160, mt: 1 } } }}
      >
        <MenuItem
          onClick={handleProfileOpen}
          sx={{
            ...menuItemSx,
            '&.Mui-focusVisible': { bgcolor: 'transparent' },
            '&:active': { bgcolor: 'action.selected' },
          }}
        >
          <ListItemIcon><IconPerson /></ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleLogout} sx={menuItemSx}>
          <ListItemIcon><IconLogout /></ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>

      <Dialog open={profileOpen} onClose={handleProfileClose} maxWidth="xs" fullWidth>
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontFamily: FONT_FAMILY,
            fontSize: 18,
            fontWeight: 500,
            pr: 1,
            pb: 1.5,
          }}
        >
          Account Details
          <IconButton onClick={handleProfileClose} aria-label="Close" size="small">
            <CloseIcon fontSize="small" />
          </IconButton>
        </DialogTitle>
        <Divider
          sx={{
            mx: 2.5,
            borderColor: theme =>
              theme.palette.mode === 'light' ? 'rgba(0, 0, 0, 0.08)' : 'divider',
          }}
        />
        <DialogContent sx={{ pt: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pb: 1 }}>
            <Box>
              <Typography
                sx={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 16,
                  fontWeight: 500,
                  color: theme =>
                    theme.palette.mode === 'light' ? '#9aa1b0' : 'rgba(255, 255, 255, 0.55)',
                  mb: 0.5,
                }}
              >
                Name
              </Typography>
              <Typography
                sx={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 16,
                  fontWeight: 500,
                  color: 'text.primary',
                }}
              >
                {sessionEmployee?.name || '—'}
              </Typography>
            </Box>
            <Box>
              <Typography
                sx={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 16,
                  fontWeight: 500,
                  color: theme =>
                    theme.palette.mode === 'light' ? '#9aa1b0' : 'rgba(255, 255, 255, 0.55)',
                  mb: 0.5,
                }}
              >
                Email
              </Typography>
              <Typography
                sx={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 16,
                  fontWeight: 500,
                  color: 'text.primary',
                }}
              >
                {sessionEmployee?.email || '—'}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>
    </>
  )
}
