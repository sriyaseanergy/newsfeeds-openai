import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Typography from '@mui/material/Typography'
import CloseIcon from '@mui/icons-material/Close'
import ErrorOutlineOutlinedIcon from '@mui/icons-material/ErrorOutlineOutlined'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import CheckCircleOutlineOutlinedIcon from '@mui/icons-material/CheckCircleOutlineOutlined'

export type NotificationSeverity = 'error' | 'warning' | 'info' | 'success'

export type AppNotification = {
  id: string
  status: string
  description: string
  severity: NotificationSeverity
}

export type ShowNotificationInput = {
  message: string
  severity?: NotificationSeverity
  status?: string
  description?: string
  autoHideMs?: number
}

type NotificationContextValue = {
  showNotification: (input: ShowNotificationInput) => string
  dismissNotification: (id: string) => void
  clearNotifications: () => void
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

const SEVERITY_STYLES: Record<
  NotificationSeverity,
  { bg: string; border: string; iconColor: string }
> = {
  error: {
    bg: '#ffffff',
    border: 'rgba(0, 0, 0, 0.12)',
    iconColor: '#dc2626',
  },
  warning: {
    bg: '#ffffff',
    border: 'rgba(0, 0, 0, 0.12)',
    iconColor: '#ca8a04',
  },
  info: {
    bg: '#ffffff',
    border: 'rgba(0, 0, 0, 0.12)',
    iconColor: '#2563eb',
  },
  success: {
    bg: '#ffffff',
    border: 'rgba(0, 0, 0, 0.12)',
    iconColor: '#16a34a',
  },
}

const DEFAULT_STATUS: Record<NotificationSeverity, string> = {
  error: 'Error',
  warning: 'Warning',
  info: 'Info',
  success: 'Success',
}

function severityFromStatus(status: string, fallback: NotificationSeverity): NotificationSeverity {
  const code = Number.parseInt(status, 10)
  if (Number.isNaN(code)) return fallback
  if (code >= 400) return 'error'
  if (code >= 200 && code < 300) return 'success'
  return fallback
}

function parseNotification(input: ShowNotificationInput): Pick<AppNotification, 'status' | 'description' | 'severity'> {
  const severity = input.severity ?? 'error'
  if (input.status && input.description) {
    return {
      status: input.status,
      description: input.description,
      severity: severityFromStatus(input.status, severity),
    }
  }

  const message = String(input.message || '').trim()
  const statusMatch = message.match(/^(\d{3})\s+([\s\S]+)$/)
  if (statusMatch) {
    return {
      status: statusMatch[1],
      description: statusMatch[2].trim(),
      severity: severityFromStatus(statusMatch[1], severity),
    }
  }

  return {
    status: input.status ?? DEFAULT_STATUS[severity],
    description: input.description ?? message,
    severity,
  }
}

function SeverityIcon({ severity }: { severity: NotificationSeverity }) {
  const sx = { fontSize: 22, flexShrink: 0 }
  switch (severity) {
    case 'warning':
      return <WarningAmberOutlinedIcon sx={sx} />
    case 'info':
      return <InfoOutlinedIcon sx={sx} />
    case 'success':
      return <CheckCircleOutlineOutlinedIcon sx={sx} />
    default:
      return <ErrorOutlineOutlinedIcon sx={sx} />
  }
}

export function useNotification() {
  const ctx = useContext(NotificationContext)
  if (!ctx) {
    throw new Error('useNotification must be used within NotificationProvider')
  }
  return ctx
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<AppNotification[]>([])

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const showNotification = useCallback(
    (input: ShowNotificationInput) => {
      const parsed = parseNotification(input)
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      const item: AppNotification = { id, ...parsed }

      setNotifications(prev => [...prev, item])

      const autoHideMs = input.autoHideMs ?? 8000
      if (autoHideMs > 0) {
        window.setTimeout(() => dismissNotification(id), autoHideMs)
      }

      return id
    },
    [dismissNotification],
  )

  const value = useMemo(
    () => ({ showNotification, dismissNotification, clearNotifications }),
    [showNotification, dismissNotification, clearNotifications],
  )

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationController
        notifications={notifications}
        onDismiss={dismissNotification}
      />
    </NotificationContext.Provider>
  )
}

type NotificationControllerProps = {
  notifications: AppNotification[]
  onDismiss: (id: string) => void
}

export default function NotificationController({
  notifications,
  onDismiss,
}: NotificationControllerProps) {
  if (!notifications.length) return null

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        zIndex: theme => theme.zIndex.snackbar + 1,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.25,
        width: 'min(380px, calc(100vw - 32px))',
        pointerEvents: 'none',
      }}
    >
      {notifications.map(notification => {
        const styles = SEVERITY_STYLES[notification.severity]
        return (
          <Box
            key={notification.id}
            role="alert"
            sx={{
              pointerEvents: 'auto',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1.25,
              px: 1.5,
              py: 1.25,
              borderRadius: 1.5,
              bgcolor: styles.bg,
              border: `1px solid ${styles.border}`,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
            }}
          >
            <Box sx={{ color: styles.iconColor, mt: 0.25 }}>
              <SeverityIcon severity={notification.severity} />
            </Box>

            <Box sx={{ flex: 1, minWidth: 0, pr: 0.5 }}>
              <Typography
                sx={{
                  fontSize: 16,
                  fontWeight: 500,
                  color: '#000000',
                  lineHeight: 1.3,
                }}
              >
                {notification.status}
              </Typography>
              <Typography
                sx={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: '#000000',
                  lineHeight: 1.45,
                  mt: 0.25,
                  wordBreak: 'break-word',
                }}
              >
                {notification.description}
              </Typography>
            </Box>

            <IconButton
              size="small"
              aria-label="Dismiss notification"
              onClick={() => onDismiss(notification.id)}
              sx={{
                mt: -0.25,
                mr: -0.5,
                color: '#000000',
                '&:hover': { color: '#000000', bgcolor: 'rgba(0, 0, 0, 0.06)' },
              }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
        )
      })}
    </Box>
  )
}
