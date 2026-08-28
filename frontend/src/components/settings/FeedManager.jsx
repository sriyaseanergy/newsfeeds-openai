import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Switch from '@mui/material/Switch'
import Chip from '@mui/material/Chip'
import Paper from '@mui/material/Paper'
import { useTheme } from '@mui/material/styles'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { useNotification } from '../notificationController.tsx'
import { TECHNOLOGY_DOMAIN_COLORS } from '../../constants/categories.js'
import { normalizeTechnologyDomain, technologyDomainNames } from '../../utils/articles.js'
import SettingsDeleteButton from './SettingsDeleteButton.jsx'
import ConfirmDeleteDialog from './ConfirmDeleteDialog.jsx'

export default function FeedManager({ feeds, technologyDomains, onFeedsChange, onBusyChange, isAdmin }) {
  const theme = useTheme()
  const { showNotification } = useNotification()
  const [toggling, setToggling] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const orderedTechnologyDomains = technologyDomainNames(technologyDomains)

  useEffect(() => {
    onBusyChange?.(toggling !== null || deleting !== null)
  }, [toggling, deleting, onBusyChange])

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
      showNotification({
        severity: 'error',
        description: `Unable to update feed: ${e.message}`,
      })
    } finally {
      setToggling(null)
    }
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    const target = deleteTarget
    setDeleteTarget(null)
    setDeleting(target.id)
    try {
      await apiFetch(`${API.feeds}/${target.id}`, { method: 'DELETE' })
      onFeedsChange()
      showNotification({
        severity: 'success',
        description: `Feed "${target.name}" deleted`,
      })
    } catch (e) {
      showNotification({
        severity: 'error',
        description: `Unable to delete feed: ${e.message}`,
      })
    } finally {
      setDeleting(null)
    }
  }

  if (!feeds.length) {
    return (
      <Typography variant="body2" className="settings-muted-text" textAlign="center" py={3}>
        {isAdmin ? 'No feeds configured. Add one above.' : 'No feeds configured.'}
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
              <Typography
                className="settings-body-text"
                sx={{ letterSpacing: '0.04em', textTransform: 'uppercase' }}
              >
                {q}
              </Typography>
              <Typography variant="caption" className="settings-muted-text">
                {group.length} feed{group.length !== 1 ? 's' : ''}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {group.map(feed => (
                <Paper
                  key={feed.id}
                  variant="outlined"
                  className="settings-list-item"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.25,
                    px: 1.5,
                    py: 1,
                  }}
                >
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" className="settings-body-text" noWrap>
                      {feed.name}
                    </Typography>
                    <Typography variant="caption" className="settings-muted-text" noWrap display="block">
                      {feed.url}
                    </Typography>
                  </Box>
                  <Chip
                    label={`${feed.fetch_kind}${feed.fetch_kind === 'CRAWL' ? ` · d${feed.crawl_depth || 1}` : ''}`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: 10 }}
                  />
                  {isAdmin && (
                    <>
                      <Switch
                        size="small"
                        color="primary"
                        checked={!!feed.is_enabled}
                        onChange={() => handleToggle(feed)}
                        disabled={toggling === feed.id}
                      />
                      <SettingsDeleteButton
                        onClick={() => setDeleteTarget(feed)}
                        title="Delete feed"
                      />
                    </>
                  )}
                </Paper>
              ))}
            </Box>
          </Box>
        )
      })}
      <ConfirmDeleteDialog
        open={Boolean(deleteTarget)}
        title="Delete feed"
        message={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.name}"? This cannot be undone.`
            : ''
        }
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  )
}
