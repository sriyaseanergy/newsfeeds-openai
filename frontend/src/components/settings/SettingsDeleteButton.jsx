import IconButton from '@mui/material/IconButton'
import CircularProgress from '@mui/material/CircularProgress'
import DeleteOutlined from '@mui/icons-material/DeleteOutlined'

export default function SettingsDeleteButton({
  onClick,
  disabled = false,
  loading = false,
  title,
}) {
  return (
    <IconButton
      size="small"
      className="settings-delete-btn"
      onClick={onClick}
      disabled={disabled || loading}
      title={title}
      aria-label={title || 'Delete'}
    >
      {loading ? (
        <CircularProgress size={14} className="settings-delete-btn-spinner" />
      ) : (
        <DeleteOutlined fontSize="small" />
      )}
    </IconButton>
  )
}
