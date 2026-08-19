import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import CircularProgress from '@mui/material/CircularProgress'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { catColor } from '../../config/theme.js'
import { TECHNOLOGY_DOMAIN_COLORS } from '../../constants/categories.js'
import SectionTitle from './SectionTitle.jsx'

export default function ManageTechnologyDomains({
  technologyDomains,
  feeds,
  onTechnologyDomainsChange,
  onFeedsChange,
  canManageFeeds,
}) {
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [error, setError] = useState('')

  const handleAdd = async () => {
    const trimmed = name.trim()
    if (!trimmed) { setError('Name is required'); return }
    setError('')
    setSaving(true)
    try {
      await apiFetch(API.technologyDomains, {
        method: 'POST',
        body: JSON.stringify({ name: trimmed }),
      })
      setName('')
      onTechnologyDomainsChange()
    } catch (e) {
      setError(e.message.includes('409') ? 'A technology domain with this name already exists' : `Error: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async domain => {
    const inUse = feeds.some(f => f.technology_domain_id === domain.id)
    if (inUse) { setError('Move or delete feeds assigned to this technology domain first'); return }
    if (!confirm(`Delete "${domain.name}"?`)) return
    setError('')
    setDeleting(domain.id)
    try {
      const r = await fetch(`${API.technologyDomains}/${domain.id}`, { method: 'DELETE' })
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
      onTechnologyDomainsChange()
      onFeedsChange()
    } catch (e) {
      setError(e.message.includes('409') ? 'Move or delete feeds assigned to this technology domain first' : `Error: ${e.message}`)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <Box sx={{ mb: 4 }}>
      <SectionTitle>Manage Technology Domains</SectionTitle>
      {!canManageFeeds && (
        <Typography variant="caption" color="text.disabled" sx={{ mb: 1.25, display: 'block', lineHeight: 1.45 }}>
          Adding or removing technology domains is limited to Super Admin or Delivery Manager.
        </Typography>
      )}
      {canManageFeeds && (
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <TextField
            size="small"
            fullWidth
            value={name}
            onChange={e => { setName(e.target.value); setError('') }}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            placeholder="New technology domain name"
            error={Boolean(error)}
          />
          <Button variant="contained" onClick={handleAdd} disabled={saving}>
            {saving ? 'Adding…' : 'Add'}
          </Button>
        </Box>
      )}
      {error && <Typography variant="caption" color="error" sx={{ mb: 1, display: 'block' }}>{error}</Typography>}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {technologyDomains.map(q => {
          const count = feeds.filter(f => f.technology_domain_id === q.id).length
          const color = TECHNOLOGY_DOMAIN_COLORS[q.name] || catColor(q.name)
          return (
            <Paper key={q.id || q.name} variant="outlined" sx={{ display: 'flex', alignItems: 'center', gap: 1.25, px: 1.5, py: 0.875 }}>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: color, flexShrink: 0 }} />
              <Typography variant="body2" sx={{ flex: 1 }}>{q.name}</Typography>
              <Typography variant="caption" color="text.disabled">
                {count} feed{count !== 1 ? 's' : ''}
              </Typography>
              {canManageFeeds && (
                <IconButton
                  size="small"
                  onClick={() => handleDelete(q)}
                  disabled={deleting === q.id || count > 0}
                  title={count > 0 ? 'Remove assigned feeds before deleting' : 'Delete technology domain'}
                >
                  {deleting === q.id ? <CircularProgress size={14} /> : '×'}
                </IconButton>
              )}
            </Paper>
          )
        })}
      </Box>
    </Box>
  )
}
