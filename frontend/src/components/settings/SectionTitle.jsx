import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export default function SectionTitle({ children, showDivider = true }) {
  return (
    <Box className={showDivider ? 'settings-section-header' : undefined}>
      <Typography
        component="h2"
        className="settings-section-title"
        sx={showDivider ? undefined : { mb: 0 }}
      >
        {children}
      </Typography>
      {showDivider && <Box className="settings-section-divider" role="presentation" />}
    </Box>
  )
}
