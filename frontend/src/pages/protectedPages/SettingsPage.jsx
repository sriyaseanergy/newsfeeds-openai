import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import CircularProgress from '@mui/material/CircularProgress'
import { useTheme } from '@mui/material/styles'
import { API } from '../../config/api.js'
import { apiFetch } from '../../services/api.js'
import { canManageFeedSources } from '../../services/auth.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useAppData } from '../../context/AppDataContext.jsx'
import ManageTechnologyDomains from '../../components/settings/ManageTechnologyDomains.jsx'
import AddFeedForm from '../../components/settings/AddFeedForm.jsx'
import FeedManager from '../../components/settings/FeedManager.jsx'
import SectionTitle from '../../components/settings/SectionTitle.jsx'

export default function SettingsPage() {
  const theme = useTheme()
  const { sessionEmployee } = useAuth()
  const {
    feeds,
    technologyDomains,
    recipients,
    recipientsLoading,
    setRecipients,
    fetchFeeds,
    fetchTechnologyDomains,
  } = useAppData()

  const canManageFeeds = canManageFeedSources(sessionEmployee)
  const [input, setInput] = useState('')
  const [adding, setAdding] = useState(false)
  const [removing, setRemoving] = useState(null)
  const [recError, setRecError] = useState('')

  const validEmail = e => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)

  const handleAddRecipient = async () => {
    const email = input.trim().toLowerCase()
    if (!email) { setRecError('Email is required'); return }
    if (!validEmail(email)) { setRecError('Please enter a valid email address'); return }
    setRecError('')
    setAdding(true)
    try {
      const created = await apiFetch(API.emails, {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setRecipients(prev => [created, ...prev])
      setInput('')
    } catch (e) {
      const msg = String(e?.message || '')
      if (msg.includes('409')) setRecError('This email recipient already exists')
      else if (msg.includes('422')) setRecError('Please enter a valid email address')
      else setRecError(`Unable to add recipient: ${msg}`)
    } finally {
      setAdding(false)
    }
  }

  const handleRemoveRecipient = async recipient => {
    setRecError('')
    setRemoving(recipient.id)
    try {
      await apiFetch(`${API.emails}/${recipient.id}`, { method: 'DELETE' })
      setRecipients(prev => prev.filter(r => r.id !== recipient.id))
    } catch (e) {
      const msg = String(e?.message || '')
      if (msg.includes('404')) setRecError('Recipient was already removed')
      else setRecError(`Unable to remove recipient: ${msg}`)
    } finally {
      setRemoving(null)
    }
  }

  return (
    <Box sx={{ flex: 1, overflowY: 'auto', p: 2.5 }}>
      <ManageTechnologyDomains
        technologyDomains={technologyDomains}
        feeds={feeds}
        onTechnologyDomainsChange={fetchTechnologyDomains}
        onFeedsChange={fetchFeeds}
        canManageFeeds={canManageFeeds}
      />

      <SectionTitle>Feed Sources</SectionTitle>
      <Typography variant="caption" color="text.secondary" sx={{ mb: 1.75, display: 'block' }}>
        {feeds.length} feed{feeds.length !== 1 ? 's' : ''} configured · {feeds.filter(f => f.is_enabled).length} active
      </Typography>
      {!canManageFeeds && (
        <Typography variant="caption" color="text.disabled" sx={{ mb: 1.5, display: 'block', lineHeight: 1.45 }}>
          Adding or deleting feeds is limited to Super Admin or Delivery Manager.
        </Typography>
      )}

      <AddFeedForm technologyDomains={technologyDomains} onAdd={fetchFeeds} canManage={canManageFeeds} />

      <Box sx={{ mb: 4 }}>
        <FeedManager
          feeds={feeds}
          technologyDomains={technologyDomains}
          onFeedsChange={fetchFeeds}
          canManage={canManageFeeds}
        />
      </Box>

      <SectionTitle>Email Recipients</SectionTitle>
      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
        <TextField
          size="small"
          fullWidth
          value={input}
          onChange={e => { setInput(e.target.value); setRecError('') }}
          onKeyDown={e => e.key === 'Enter' && handleAddRecipient()}
          placeholder="name@company.com"
          error={Boolean(recError)}
        />
        <Button variant="contained" onClick={handleAddRecipient} disabled={adding}>
          {adding ? 'Adding…' : 'Add'}
        </Button>
      </Box>
      {recError && <Typography variant="caption" color="error" sx={{ mb: 1, display: 'block' }}>{recError}</Typography>}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {recipientsLoading ? (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={1.5}>
            Loading recipients...
          </Typography>
        ) : recipients.length === 0 ? (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={1.5}>
            No recipients configured
          </Typography>
        ) : (
          recipients.map(recipient => (
            <Paper key={recipient.id} variant="outlined" sx={{ display: 'flex', alignItems: 'center', gap: 1.25, px: 1.5, py: 0.875 }}>
              <Box
                sx={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  bgcolor: recipient.is_enabled ? theme.palette.success.main : theme.palette.text.secondary,
                  flexShrink: 0,
                }}
              />
              <Typography variant="body2" sx={{ flex: 1 }}>{recipient.email}</Typography>
              <IconButton size="small" onClick={() => handleRemoveRecipient(recipient)} disabled={removing === recipient.id}>
                {removing === recipient.id ? <CircularProgress size={14} /> : '×'}
              </IconButton>
            </Paper>
          ))
        )}
      </Box>
    </Box>
  )
}
