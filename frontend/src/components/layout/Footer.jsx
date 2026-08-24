import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { FONT_FAMILY, LAYOUT } from '../../config/theme.js'

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
      <Typography
        sx={{
          fontFamily: FONT_FAMILY,
          fontSize: 14,
          fontWeight: 500,
          color: 'text.secondary',
        }}
      >
        © Seanergy.ai group. All rights reserved
      </Typography>
    </Box>
  )
}
