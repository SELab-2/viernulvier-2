/**
 * Defines the severity level of a floating alert.
 */
export type FloatingAlertSeverity = 'error' | 'warning' | 'info' | 'success'

/**
 * Props for rendering a floating alert component.
 */
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
  disableFloatingWrapper?: boolean
}

/**
 * Constant set of supported alert severities.
 *
 * Useful when you need a strongly typed reference instead of raw strings.
 */
export const ALERT_SEVERITIES = {
  error: 'error',
  warning: 'warning',
  info: 'info',
  success: 'success',
} as const
