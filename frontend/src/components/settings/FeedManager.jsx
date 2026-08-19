import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Switch from '@mui/material/Switch'
import IconButton from '@mui/material/IconButton'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Paper from '@mui/material/Paper'
import { useTheme } from '@mui/material/styles'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { TECHNOLOGY_DOMAIN_COLORS } from '../../constants/categories.js'
import { normalizeTechnologyDomain, technologyDomainNames } from '../../utils/articles.js'

export default function FeedManager({ feeds, technologyDomains, onFeedsChange, canManage }) {
  const theme = useTheme()
  const [toggling, setToggling] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const orderedTechnologyDomains = technologyDomainNames(technologyDomains)

  const handleToggle = async feed => {
    setToggling(feed.id)
    try {
      await apiFetch(`${API.feeds}/${feed.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          is_enabled: !feed.is_enabled,
          fetch_kind: feed.fetch_kind,
          crawl_depth: feed.fetch_kind === 'CRAWL' ? (feed.crawl_depth || 1) : null,
        }),
      })
      onFeedsChange()
    } catch (e) {
      console.error(e)
    } finally {
      setToggling(null)
    }
  }

  const handleDelete = async feed => {
    if (!confirm(`Delete "${feed.name}"? This cannot be undone.`)) return
    setDeleting(feed.id)
    try {
      await fetch(`${API.feeds}/${feed.id}`, { method: 'DELETE' })
      onFeedsChange()
    } catch (e) {
      console.error(e)
    } finally {
      setDeleting(null)
    }
  }

  if (!feeds.length) {
    return (
      <Typography variant="body2" color="text.secondary" textAlign="center" py={3}>
        {canManage ? 'No feeds configured. Add one above.' : 'No feeds configured.'}
      </Typography>
    )
  }

  const grouped = orderedTechnologyDomains.reduce((acc, q) => {
    acc[q] = feeds.filter(f => {
      const domain = technologyDomains.find(d => d.id === f.technology_domain_id)
      return normalizeTechnologyDomain(domain ? domain.name : '') === q
    })
    return acc
  }, {})

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {orderedTechnologyDomains.map(q => {
        const group = grouped[q]
        if (!group.length) return null
        const color = TECHNOLOGY_DOMAIN_COLORS[q] || theme.palette.text.secondary
        return (
          <Box key={q}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.75, pb: 0.75, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ width: 3, height: 14, borderRadius: 0.5, bgcolor: color, flexShrink: 0 }} />
              <Typography variant="caption" fontWeight={700} sx={{ color, letterSpacing: '0.07em', textTransform: 'uppercase' }}>
                {q}
              </Typography>
              <Typography variant="caption" color="text.disabled">
                {group.length} feed{group.length !== 1 ? 's' : ''}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {group.map(feed => (
                <Paper
                  key={feed.id}
                  variant="outlined"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.25,
                    px: 1.5,
                    py: 1,
                    opacity: feed.is_enabled ? 1 : 0.45,
                    transition: 'opacity 200ms ease',
                  }}
                >
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" fontWeight={500} noWrap>
                      {feed.name}
                    </Typography>
                    <Typography variant="caption" color="text.disabled" noWrap display="block">
                      {feed.url}
                    </Typography>
                  </Box>
                  <Chip
                    label={`${feed.fetch_kind}${feed.fetch_kind === 'CRAWL' ? ` · d${feed.crawl_depth || 1}` : ''}`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: 10 }}
                  />
                  <Switch
                    size="small"
                    checked={!!feed.is_enabled}
                    onChange={() => handleToggle(feed)}
                    disabled={toggling === feed.id}
                  />
                  {canManage && (
                    <IconButton size="small" onClick={() => handleDelete(feed)} disabled={deleting === feed.id}>
                      {deleting === feed.id ? <CircularProgress size={14} /> : '×'}
                    </IconButton>
                  )}
                </Paper>
              ))}
            </Box>
          </Box>
        )
      })}
    </Box>
  )
}
