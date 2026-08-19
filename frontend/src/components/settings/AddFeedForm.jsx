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

export default function AddFeedForm({ technologyDomains, onAdd, canManage }) {
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
    if (!form.technology_domain_id) { setError('Technology Domain is required'); return }
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

  if (!canManage) return null

  return (
    <Box sx={{ mb: 2 }}>
      {!open ? (
        <Button variant="contained" color="primary" onClick={() => setOpen(true)}>
          + Add Feed
        </Button>
      ) : (
        <Paper variant="outlined" sx={{ p: 2, borderColor: 'primary.main' }}>
          <Typography variant="caption" fontWeight={700} color="primary.dark" sx={{ letterSpacing: '0.06em', textTransform: 'uppercase', mb: 1.5, display: 'block' }}>
            New Feed
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
            <TextField label="Name" size="small" fullWidth value={form.name} onChange={e => set('name', e.target.value)} placeholder="OpenAI Blog" />
            <TextField label="URL" size="small" fullWidth value={form.url} onChange={e => set('url', e.target.value)} placeholder="https://…/feed.xml" />
            <TextField select label="Technology Domain" size="small" fullWidth value={form.technology_domain_id} onChange={e => set('technology_domain_id', e.target.value)}>
              {technologyDomains.map(d => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
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
              {FETCH_KINDS.map(kind => <MenuItem key={kind} value={kind}>{kind}</MenuItem>)}
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
            <Box sx={{ gridColumn: '1 / span 2' }}>
              <TextField label="Description (optional)" size="small" fullWidth value={form.description} onChange={e => set('description', e.target.value)} placeholder="Short feed description" />
            </Box>
          </Box>
          {error && <Typography variant="caption" color="error" sx={{ mb: 1, display: 'block' }}>{error}</Typography>}
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
            <Button size="small" onClick={() => { setOpen(false); setError('') }} disabled={saving}>Cancel</Button>
            <Button size="small" variant="contained" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Creating…' : 'Create Feed'}
            </Button>
          </Box>
        </Paper>
      )}
    </Box>
  )
}
