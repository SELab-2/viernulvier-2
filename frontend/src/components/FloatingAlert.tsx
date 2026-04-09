import { Snackbar, Box, IconButton } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { useTheme } from '@mui/material/styles'
import { tokens } from '../theme/tokens'

type FloatingAlertSeverity = 'error' | 'warning' | 'info' | 'success'

type FloatingAlertProps = {
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
}

/**
 * FloatingAlert combines Alert styling with Toast floating behavior.
 * Displays severity-themed notifications that auto-dismiss.
 */
const FloatingAlert = ({
  open,
  onClose,
  message,
  title,
  severity = 'info',
  autoCloseDuration = 4000,
  position = { vertical: 'top', horizontal: 'right' },
}: FloatingAlertProps) => {
  const theme = useTheme()

  const severityConfig: Record<
    FloatingAlertSeverity,
    { bgColor: string; textColor: string; borderColor: string }
  > = {
    error: {
      bgColor: theme.palette.mode === 'dark' ? '#5f2c2c' : '#ffebee',
      textColor: theme.palette.mode === 'dark' ? '#ff8a80' : '#c62828',
      borderColor: theme.palette.mode === 'dark' ? '#ff8a80' : '#d32f2f',
    },
    warning: {
      bgColor: theme.palette.mode === 'dark' ? '#5f4c2c' : '#fff8e1',
      textColor: theme.palette.mode === 'dark' ? '#ffb74d' : '#e65100',
      borderColor: theme.palette.mode === 'dark' ? '#ffb74d' : '#f57f17',
    },
    info: {
      bgColor: theme.palette.mode === 'dark' ? '#2c4a5f' : '#e3f2fd',
      textColor: theme.palette.mode === 'dark' ? '#64b5f6' : '#0d47a1',
      borderColor: theme.palette.mode === 'dark' ? '#64b5f6' : '#1976d2',
    },
    success: {
      bgColor: theme.palette.mode === 'dark' ? '#2c5f3c' : '#e8f5e9',
      textColor: theme.palette.mode === 'dark' ? '#81c784' : '#1b5e20',
      borderColor: theme.palette.mode === 'dark' ? '#81c784' : '#388e3c',
    },
  }

  const config = severityConfig[severity]

  return (
    <Snackbar
      open={open}
      autoHideDuration={autoCloseDuration}
      onClose={onClose}
      anchorOrigin={position}
      sx={
        position.vertical === 'top'
          ? {
              '&.MuiSnackbar-anchorOriginTopLeft': {
                top: 'calc(var(--navbar-height, 64px) + 8px + env(safe-area-inset-top, 0px))',
              },
              '&.MuiSnackbar-anchorOriginTopCenter': {
                top: 'calc(var(--navbar-height, 64px) + 8px + env(safe-area-inset-top, 0px))',
              },
              '&.MuiSnackbar-anchorOriginTopRight': {
                top: 'calc(var(--navbar-height, 64px) + 8px + env(safe-area-inset-top, 0px))',
              },
            }
          : undefined
      }
      data-testid="floating-alert"
    >
      <Box
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: tokens.spacing.numericSm,
          px: tokens.spacing.numericMd,
          py: 1.5,
          borderRadius: tokens.borderRadius.sm,
          border: `1px solid ${config.borderColor}`,
          bgcolor: config.bgColor,
          color: config.textColor,
          maxWidth: 400,
          boxShadow: tokens.shadows.md,
        }}
      >
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {title && (
            <Box
              sx={{
                fontWeight: 600,
                fontSize: '0.95rem',
                mb: 0.25,
              }}
            >
              {title}
            </Box>
          )}
          <Box
            sx={{
              fontSize: '0.875rem',
              lineHeight: 1.4,
              wordBreak: 'break-word',
            }}
          >
            {message}
          </Box>
        </Box>
        <IconButton
          size="small"
          onClick={onClose}
          aria-label="Close notification"
          sx={{
            color: config.textColor,
            flexShrink: 0,
            p: 0,
            '&:hover': {
              bgcolor: tokens.colors.overlay.black05,
            },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>
    </Snackbar>
  )
}

export default FloatingAlert
