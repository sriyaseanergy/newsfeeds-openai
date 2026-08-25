import Button from '@mui/material/Button'

export default function SettingsAddButton({ children, ...props }) {
  return (
    <Button
      variant="contained"
      className="settings-add-btn"
      disableElevation
      {...props}
    >
      {children}
    </Button>
  )
}
