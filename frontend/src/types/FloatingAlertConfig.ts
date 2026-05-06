export type FloatingAlertSeverity = 'error' | 'warning' | 'info' | 'success'

export type FloatingAlertProps = {
  open: boolean
  onClose: () => void
  message: string
  title?: string
  severity?: FloatingAlertSeverity
  autoCloseDuration?: number
  position?: {
    vertical: 'top' | 'bottom'
    horizontal: 'left' | 'center' | 'right'
  }
  stackOffsetPx?: number
}

export const ALERT_SEVERITIES = {
  error: 'error',
  warning: 'warning',
  info: 'info',
  success: 'success',
} as const
