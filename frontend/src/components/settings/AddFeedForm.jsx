import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import MenuItem from '@mui/material/MenuItem'
import Paper from '@mui/material/Paper'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { FETCH_KINDS } from '../../constants/categories.js'
import SectionTitle from './SectionTitle.jsx'
import SettingsAddButton from './SettingsAddButton.jsx'

export default function AddFeedForm({
  technologyDomains,
  onAdd,
  isAdmin,
  feeds,
  children,
}) {
  const empty = () => ({
    name: '',
    url: '',
    technology_domain_id: technologyDomains[0]?.id || '',
    fetch_kind: 'RSS',
    crawl_depth: 1,
    description: '',
  })
  const [form, setForm] = useState(empty)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    const ids = technologyDomains.map(d => d.id)
    if (technologyDomains.length > 0 && !ids.includes(form.technology_domain_id)) {
      setForm(f => ({ ...f, technology_domain_id: technologyDomains[0].id }))
    }
  }, [form.technology_domain_id, technologyDomains])

  const handleSubmit = async () => {
    if (!form.name.trim()) { setError('Name is required'); return }
    if (!form.url.trim()) { setError('URL is required'); return }
    if (!form.technology_domain_id) { setError('Category is required'); return }
    if (form.fetch_kind === 'CRAWL') {
      const depth = Number(form.crawl_depth)
      if (!Number.isInteger(depth) || depth < 1) {
        setError('Crawl depth must be at least 1')
        return
      }
    }
    setError('')
    setSaving(true)
    try {
      await apiFetch(API.feeds, {
        method: 'POST',
        body: JSON.stringify({
          name: form.name.trim(),
          url: form.url.trim(),
          technology_domain_id: form.technology_domain_id,
          fetch_kind: form.fetch_kind,
          crawl_depth: form.fetch_kind === 'CRAWL' ? Number(form.crawl_depth) : null,
          description: form.description.trim() || null,
        }),
      })
      setForm(empty())
      setOpen(false)
      onAdd()
    } catch (e) {
      setError(e.message.includes('409') ? 'A feed with this URL already exists' : `Error: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setOpen(false)
    setError('')
    setForm(empty())
  }

  const activeCount = feeds.filter(f => f.is_enabled).length

  return (
    <Box className="settings-card-inner">
      <Box className="settings-section-block">
        <Box className="settings-card-header">
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <SectionTitle showDivider={false}>Feed Sources</SectionTitle>
            <Typography className="settings-subtext">
              {feeds.length} feed{feeds.length !== 1 ? 's' : ''} configured · {activeCount} active
            </Typography>
          </Box>
          {isAdmin && !open && (
            <SettingsAddButton
              onClick={() => setOpen(true)}
              sx={{ flexShrink: 0, alignSelf: 'flex-start' }}
            >
              Add Feed
            </SettingsAddButton>
          )}
        </Box>
        <Box className="settings-section-divider" role="presentation" />
      </Box>

      {isAdmin && open && (
        <Paper variant="outlined" className="settings-add-feed-form">
          <Typography component="h3" className="settings-form-title">
            New Feed
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
              gap: 1.25,
              mb: 1.25,
            }}
          >
            <TextField
              label="Name"
              size="small"
              fullWidth
              value={form.name}
              onChange={e => set('name', e.target.value)}
              placeholder="OpenAI Blog"
            />
            <TextField
              label="URL"
              size="small"
              fullWidth
              value={form.url}
              onChange={e => set('url', e.target.value)}
              placeholder="https://…/feed.xml"
            />
            <TextField
              select
              label="Category"
              size="small"
              fullWidth
              value={form.technology_domain_id}
              onChange={e => set('technology_domain_id', e.target.value)}
            >
              {technologyDomains.map(d => (
                <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Fetch Kind"
              size="small"
              fullWidth
              value={form.fetch_kind}
              onChange={e => {
                const nextKind = e.target.value
                setForm(prev => ({
                  ...prev,
                  fetch_kind: nextKind,
                  crawl_depth: nextKind === 'CRAWL' ? (prev.crawl_depth || 1) : 1,
                }))
              }}
            >
              {FETCH_KINDS.map(kind => (
                <MenuItem key={kind} value={kind}>{kind}</MenuItem>
              ))}
            </TextField>
            {form.fetch_kind === 'CRAWL' && (
              <TextField
                label="Crawl Depth"
                type="number"
                size="small"
                fullWidth
                inputProps={{ min: 1 }}
                value={form.crawl_depth}
                onChange={e => {
                  const raw = e.target.value
                  set('crawl_depth', raw === '' ? '' : Number(raw))
                }}
              />
            )}
            <Box sx={{ gridColumn: { xs: '1', sm: '1 / -1' } }}>
              <TextField
                label="Description (optional)"
                size="small"
                fullWidth
                value={form.description}
                onChange={e => set('description', e.target.value)}
                placeholder="Short feed description"
              />
            </Box>
          </Box>
          {error && (
            <Typography variant="caption" color="error" sx={{ mb: 1.25, display: 'block', fontSize: 14 }}>
              {error}
            </Typography>
          )}
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
            <Button size="small" onClick={handleCancel} disabled={saving}>
              Cancel
            </Button>
            <Button size="small" variant="contained" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Creating…' : 'Create Feed'}
            </Button>
          </Box>
        </Paper>
      )}

      {children}
    </Box>
  )
}
