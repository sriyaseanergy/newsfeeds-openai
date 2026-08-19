import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { LAYOUT } from '../../config/theme.js'

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        height: LAYOUT.footerHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderTop: 1,
        borderColor: 'divider',
        flexShrink: 0,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        © seanergy.ai group. All rights reserved
      </Typography>
    </Box>
  )
}
