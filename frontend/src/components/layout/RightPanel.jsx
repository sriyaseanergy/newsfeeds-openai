import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import { useTheme } from '@mui/material/styles'
import { relativeTime } from '../../utils/format.js'
import { IconChevronRight } from './LayoutIcons.jsx'

function SectionTitle({ children }) {
  return (
    <Typography
      variant="caption"
      fontWeight={700}
      color="text.secondary"
      sx={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}
    >
      {children}
    </Typography>
  )
}

export default function RightPanel({ statusData, onClose }) {
  const theme = useTheme()
  const ingest = statusData?.ingestion

  const statusRows = [
    { label: 'Ingestion', value: 'every 30 min', color: '#60a5fa' },
    { label: 'SEC digest', value: '9am & 6pm IST', color: theme.palette.error.main },
    { label: 'DEV digest', value: '8am IST', color: theme.palette.success.main },
    {
      label: 'Last run',
      value: ingest?.last_run ? relativeTime(ingest.last_run) : '—',
      color: theme.palette.text.secondary,
    },
  ]

  return (
    <Paper
      elevation={0}
      sx={{
        width: 280,
        borderLeft: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        height: '100%',
        borderRadius: 0,
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'flex-start', p: 1 }}>
        <IconButton size="small" onClick={onClose} title="Close panel">
          <IconChevronRight size={18} />
        </IconButton>
      </Box>

      <Box sx={{ px: 1.5, pb: 2, borderBottom: 1, borderColor: 'divider', opacity: 0.6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <SectionTitle>System Status</SectionTitle>
          <Chip label="Coming Soon" size="small" color="warning" variant="outlined" sx={{ height: 20, fontSize: 10 }} />
        </Box>
        {statusRows.map(({ label, value, color }) => (
          <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, gap: 1 }}>
            <Typography variant="caption" color="text.secondary">{label}</Typography>
            <Typography variant="caption" fontWeight={600} sx={{ color, textAlign: 'right' }}>
              {value}
            </Typography>
          </Box>
        ))}
      </Box>

      <Box sx={{ px: 1.5, py: 1.5, borderBottom: 1, borderColor: 'divider', opacity: 0.6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <SectionTitle>Recipients</SectionTitle>
          <Chip label="Coming Soon" size="small" color="warning" variant="outlined" sx={{ height: 20, fontSize: 10 }} />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Email recipients will appear here once backend support is completed.
        </Typography>
      </Box>

      <Box sx={{ px: 1.5, py: 1.5, opacity: 0.6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <SectionTitle>Feed Health</SectionTitle>
          <Chip label="Coming Soon" size="small" color="warning" variant="outlined" sx={{ height: 20, fontSize: 10 }} />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Feed ingestion health stats will appear here.
        </Typography>
      </Box>
    </Paper>
  )
}
