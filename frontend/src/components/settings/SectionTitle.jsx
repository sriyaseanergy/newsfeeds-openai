import Typography from '@mui/material/Typography'

export default function SectionTitle({ children }) {
  return (
    <Typography
      variant="caption"
      fontWeight={700}
      color="text.secondary"
      sx={{ letterSpacing: '0.08em', textTransform: 'uppercase', mb: 1.25, display: 'block' }}
    >
      {children}
    </Typography>
  )
}
