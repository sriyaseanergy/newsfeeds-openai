import { useCallback, useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Paper from '@mui/material/Paper'
import Switch from '@mui/material/Switch'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { catColor } from '../../config/theme.js'
import { TECHNOLOGY_DOMAIN_COLORS } from '../../constants/categories.js'
import { useNotification } from '../notificationController.tsx'
import SectionTitle from './SectionTitle.jsx'
import SettingsDeleteButton from './SettingsDeleteButton.jsx'
import SettingsAddButton from './SettingsAddButton.jsx'

export default function ManageTechnologyDomains({
  onTechnologyDomainsChange,
  onFeedsChange,
  isAdmin,
  refreshToken = 0,
}) {
  const { showNotification } = useNotification()
  const [domainPreferences, setDomainPreferences] = useState([])
  const [hasFetched, setHasFetched] = useState(false)
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [toggling, setToggling] = useState(null)
  const [error, setError] = useState('')

  const fetchDomainPreferences = useCallback(async () => {
    try {
      const data = await apiFetch(API.domainPreferences)
      setDomainPreferences(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error(e)
      setDomainPreferences([])
    } finally {
      setHasFetched(true)
    }
  }, [])

  useEffect(() => {
    fetchDomainPreferences()
  }, [fetchDomainPreferences, refreshToken])

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
      onFeedsChange()
      await fetchDomainPreferences()
    } catch (e) {
      setError(e.message.includes('409') ? 'A category with this name already exists' : `Error: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async domain => {
    if (domain.feed_count > 0) {
      const msg = 'Move or delete feeds assigned to this category first'
      setError(msg)
      showNotification({ severity: 'warning', description: msg })
      return
    }
    if (!confirm(`Delete "${domain.name}"?`)) return
    setError('')
    setDeleting(domain.technology_domain_id)
    try {
      await apiFetch(`${API.technologyDomains}/${domain.technology_domain_id}`, { method: 'DELETE' })
      onTechnologyDomainsChange()
      onFeedsChange()
      await fetchDomainPreferences()
      showNotification({ severity: 'success', description: `Category "${domain.name}" deleted` })
    } catch (e) {
      const msg = e.message.includes('409')
        ? 'Move or delete feeds assigned to this category first'
        : `Unable to delete category: ${e.message}`
      setError(msg)
      showNotification({ severity: 'error', description: msg })
    } finally {
      setDeleting(null)
    }
  }

  const handleToggle = async domain => {
    setToggling(domain.technology_domain_id)
    setError('')
    try {
      await apiFetch(API.domainPreferences, {
        method: 'PUT',
        body: JSON.stringify({
          preferences: [{
            technology_domain_id: domain.technology_domain_id,
            enabled: !domain.user_enabled,
          }],
        }),
      })
      await fetchDomainPreferences()
    } catch (e) {
      const msg = `Unable to update preference: ${e.message}`
      setError(msg)
      showNotification({ severity: 'error', description: msg })
    } finally {
      setToggling(null)
    }
  }

  return (
    <Box className="settings-card-inner">
      <SectionTitle>Manage Categories</SectionTitle>
      {isAdmin && (
        <Box className="settings-add-row">
          <TextField
            size="small"
            fullWidth
            value={name}
            onChange={e => { setName(e.target.value); setError('') }}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            placeholder="New category name"
            error={Boolean(error)}
          />
          <SettingsAddButton onClick={handleAdd} disabled={saving}>
            {saving ? 'Adding…' : 'Add Category'}
          </SettingsAddButton>
        </Box>
      )}
      {error && (
        <Typography variant="caption" color="error" sx={{ mb: 1, display: 'block', fontSize: 14 }}>
          {error}
        </Typography>
      )}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {hasFetched && domainPreferences.length === 0 ? (
          <Typography variant="body2" className="settings-muted-text" textAlign="center" py={1.5}>
            No categories configured
          </Typography>
        ) : (
          domainPreferences.map(domain => {
            const color = TECHNOLOGY_DOMAIN_COLORS[domain.name] || catColor(domain.name)
            return (
              <Paper
                key={domain.technology_domain_id}
                variant="outlined"
                className="settings-list-item"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.25,
                  px: 1.5,
                  py: 0.875,
                }}
              >
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: color, flexShrink: 0 }} />
                <Typography variant="body2" className="settings-body-text" sx={{ flex: 1 }}>
                  {domain.name}
                </Typography>
                <Typography variant="caption" className="settings-muted-text">
                  {domain.feed_count} feed{domain.feed_count !== 1 ? 's' : ''}
                </Typography>
                <Switch
                  size="small"
                  color="primary"
                  checked={!!domain.user_enabled}
                  onChange={() => handleToggle(domain)}
                  disabled={toggling === domain.technology_domain_id || !domain.system_enabled}
                />
                {isAdmin && (
                  <SettingsDeleteButton
                    onClick={() => handleDelete(domain)}
                    loading={deleting === domain.technology_domain_id}
                    title={domain.feed_count > 0 ? 'Remove assigned feeds before deleting' : 'Delete category'}
                  />
                )}
              </Paper>
            )
          })
        )}
      </Box>
    </Box>
  )
}
