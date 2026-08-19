import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Paper from '@mui/material/Paper'
import { useTheme } from '@mui/material/styles'
import { relativeTime } from '../../utils/format.js'

export default function FeedHealthView({ feedHealth, loading, onRefresh }) {
  const theme = useTheme()
  const [showAll, setShowAll] = useState(false)

  const disabled = feedHealth.filter(f => f.disabled)
  const failing = feedHealth.filter(f => !f.disabled && f.consecutive_failures > 0)
  const healthy = feedHealth.filter(f => !f.disabled && !f.consecutive_failures && f.last_success)
  const never = feedHealth.filter(f => !f.last_success && !f.disabled)
  const issues = [...disabled, ...failing, ...never]
  const visible = showAll ? feedHealth : issues

  return (
    <Box sx={{ flex: 1, overflowY: 'auto', p: 2.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
        <Box>
          <Typography variant="body2" fontWeight={600}>Feed Health</Typography>
          <Typography variant="caption" color="text.secondary">
            {healthy.length} healthy · {failing.length} failing · {disabled.length} disabled
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 0.75 }}>
          {feedHealth.length > 0 && (
            <Button size="small" variant="outlined" onClick={() => setShowAll(p => !p)}>
              {showAll ? 'Issues only' : `Show all (${feedHealth.length})`}
            </Button>
          )}
          <Button size="small" variant="outlined" onClick={onRefresh} disabled={loading}>
            {loading ? 'Refreshing…' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {feedHealth.length === 0 && !loading && (
        <Box
          sx={{
            textAlign: 'center',
            py: 5,
            fontSize: 12,
            color: 'text.secondary',
            border: 1,
            borderStyle: 'dashed',
            borderColor: 'divider',
            borderRadius: 1,
          }}
        >
          No feed health data — start worker.py to begin ingestion
        </Box>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {visible.map(f => {
          const isDisabled = f.disabled
          const isFailing = !isDisabled && f.consecutive_failures > 0
          const isHealthy = !isDisabled && !isFailing && f.last_success
          const dot = isDisabled
            ? theme.palette.error.main
            : isFailing
              ? theme.palette.warning.main
              : isHealthy
                ? theme.palette.success.main
                : theme.palette.text.secondary
          const is404 = f.last_error?.includes('404')

          return (
            <Paper key={f.url} variant="outlined" sx={{ display: 'flex', alignItems: 'center', gap: 1.25, px: 1.5, py: 1.125 }}>
              <Box sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: dot, flexShrink: 0 }} />
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="body2" fontWeight={500} noWrap>
                  {f.name}
                </Typography>
                {f.last_error && !is404 && (
                  <Typography variant="caption" color="error" noWrap display="block">
                    {f.last_error}
                  </Typography>
                )}
              </Box>
              {is404 && <Chip label="404" size="small" color="error" variant="outlined" sx={{ fontSize: 9 }} />}
              {isFailing && !is404 && (
                <Chip label={`${f.consecutive_failures}×`} size="small" color="warning" variant="outlined" sx={{ fontSize: 9 }} />
              )}
              {isDisabled && <Chip label="OFF" size="small" color="error" variant="outlined" sx={{ fontSize: 9 }} />}
              {f.last_success && (
                <Typography variant="caption" color="text.disabled" sx={{ flexShrink: 0 }}>
                  {relativeTime(f.last_success)}
                </Typography>
              )}
            </Paper>
          )
        })}
      </Box>
    </Box>
  )
}
