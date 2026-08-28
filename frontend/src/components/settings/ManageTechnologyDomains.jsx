import { useCallback, useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Paper from '@mui/material/Paper'
import Switch from '@mui/material/Switch'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { useNotification } from '../notificationController.tsx'
import SectionTitle from './SectionTitle.jsx'
import SettingsDeleteButton from './SettingsDeleteButton.jsx'
import SettingsAddButton from './SettingsAddButton.jsx'
import ConfirmDeleteDialog from './ConfirmDeleteDialog.jsx'

export default function ManageTechnologyDomains({
  onTechnologyDomainsChange,
  onFeedsChange,
  onLoadingChange,
  onBusyChange,
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
  const [validationError, setValidationError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState(null)

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

  useEffect(() => {
    onLoadingChange?.(!hasFetched)
  }, [hasFetched, onLoadingChange])

  useEffect(() => {
    onBusyChange?.(saving || deleting !== null || toggling !== null)
  }, [saving, deleting, toggling, onBusyChange])

  const handleAdd = async () => {
    const trimmed = name.trim()
    if (!trimmed) {
      setValidationError('Name is required')
      return
    }
    setValidationError('')
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
      showNotification({ severity: 'success', description: `Category "${trimmed}" added` })
    } catch (e) {
      const msg = e.message.includes('409')
        ? 'A category with this name already exists'
        : `Unable to add category: ${e.message}`
      showNotification({ severity: 'error', description: msg })
    } finally {
      setSaving(false)
    }
  }

  const requestDelete = domain => {
    if (domain.feed_count > 0) {
      showNotification({
        severity: 'warning',
        description: 'Move or delete feeds assigned to this category first',
      })
      return
    }
    setDeleteTarget(domain)
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    const target = deleteTarget
    setDeleteTarget(null)
    setDeleting(target.technology_domain_id)
    try {
      await apiFetch(`${API.technologyDomains}/${target.technology_domain_id}`, { method: 'DELETE' })
      onTechnologyDomainsChange()
      onFeedsChange()
      await fetchDomainPreferences()
      showNotification({ severity: 'success', description: `Category "${target.name}" deleted` })
    } catch (e) {
      const msg = e.message.includes('409')
        ? 'Move or delete feeds assigned to this category first'
        : `Unable to delete category: ${e.message}`
      showNotification({ severity: 'error', description: msg })
    } finally {
      setDeleting(null)
    }
  }

  const handleToggle = async domain => {
    setToggling(domain.technology_domain_id)
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
      showNotification({
        severity: 'error',
        description: `Unable to update preference: ${e.message}`,
      })
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
            onChange={e => { setName(e.target.value); setValidationError('') }}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            placeholder="New category name"
            error={Boolean(validationError)}
            helperText={validationError || ' '}
          />
          <SettingsAddButton onClick={handleAdd} disabled={saving}>
            {saving ? 'Adding…' : 'Add Category'}
          </SettingsAddButton>
        </Box>
      )}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {hasFetched && domainPreferences.length === 0 ? (
          <Typography variant="body2" className="settings-muted-text" textAlign="center" py={1.5}>
            No categories configured
          </Typography>
        ) : (
          domainPreferences.map(domain => (
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
                  onClick={() => requestDelete(domain)}
                  title={domain.feed_count > 0 ? 'Remove assigned feeds before deleting' : 'Delete category'}
                />
              )}
            </Paper>
          ))
        )}
      </Box>
      <ConfirmDeleteDialog
        open={Boolean(deleteTarget)}
        title="Delete category"
        message={deleteTarget ? `Are you sure you want to delete "${deleteTarget.name}"?` : ''}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  )
}
