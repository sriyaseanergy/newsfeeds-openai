import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Typography from '@mui/material/Typography'

export default function ConfirmDeleteDialog({
  open,
  title = 'Confirm delete',
  message,
  confirmLabel = 'Delete',
  cancelLabel = 'Cancel',
  onCancel,
  onConfirm,
}) {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      maxWidth="xs"
      fullWidth
      className="confirm-delete-dialog"
    >
      <DialogTitle className="confirm-delete-dialog-title">
        {title}
      </DialogTitle>
      <DialogContent className="confirm-delete-dialog-content">
        <Typography className="confirm-delete-dialog-message">
          {message}
        </Typography>
      </DialogContent>
      <DialogActions className="confirm-delete-dialog-actions">
        <Button
          onClick={onCancel}
          disableRipple
          className="confirm-delete-dialog-cancel"
        >
          {cancelLabel}
        </Button>
        <Button
          onClick={onConfirm}
          disableRipple
          variant="contained"
          className="confirm-delete-dialog-confirm"
          disableElevation
        >
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
