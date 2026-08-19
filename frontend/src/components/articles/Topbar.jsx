import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import { useTheme } from '@mui/material/styles'
import { catColor } from '../../config/theme.js'
import { CAT_DESC } from '../../constants/categories.js'

export default function Topbar({ selectedCat, typeFilter, onTypeFilter, statusData }) {
  const theme = useTheme()
  const counts = statusData?.articles
  const feeds = statusData?.feeds
  const total = counts?.total ?? '—'
  const pendSec = counts?.pending_security_notification ?? '—'
  const healthy = feeds ? `${feeds.healthy}/${feeds.total}` : '—'
  const feedColor = (feeds?.disabled ?? 0) > 0 ? theme.palette.warning.main : theme.palette.success.main

  return (
    <Box
      sx={{
        px: 2.5,
        pt: 2,
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
        flexShrink: 0,
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.75 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              bgcolor: catColor(selectedCat),
              flexShrink: 0,
            }}
          />
          <Box>
            <Typography variant="body2" fontWeight={600}>
              {selectedCat}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {CAT_DESC[selectedCat] || ''}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {[['All', 'All'], ['SEC', 'Security'], ['DEV', 'Dev']].map(([label, val]) => {
            const active = typeFilter === val
            return (
              <Button
                key={val}
                size="small"
                variant={active ? 'contained' : 'outlined'}
                color={active ? 'primary' : 'inherit'}
                onClick={() => onTypeFilter(val)}
                sx={{ minWidth: 48, fontSize: 11, py: 0.25 }}
              >
                {label}
              </Button>
            )
          })}
        </Box>
      </Box>

      <Box sx={{ display: 'flex', pb: 1 }}>
        {[
          { label: 'Total', value: total, color: 'text.primary' },
          { label: 'Pending SEC', value: pendSec, color: 'error.main' },
          { label: 'Feeds', value: healthy, color: feedColor },
        ].map(({ label, value, color }, i) => (
          <Box
            key={label}
            sx={{
              flex: 1,
              py: 1,
              pl: i > 0 ? 1.75 : 0,
              ml: i > 0 ? 1.75 : 0,
              borderLeft: i > 0 ? 1 : 0,
              borderColor: 'divider',
            }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              {label}
            </Typography>
            <Typography variant="h6" fontWeight={600} sx={{ color, fontFamily: 'monospace', fontSize: 15 }}>
              {value}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  )
}
