/* eslint-disable prettier/prettier */
import CloseIcon from '@mui/icons-material/Close'
import { Snackbar, Box, IconButton } from '@mui/material'
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
      bgColor: theme.palette.mode === 'dark' ? theme.palette.error.dark : theme.palette.error.light,
      textColor: theme.palette.getContrastText(
        theme.palette.mode === 'dark' ? theme.palette.error.dark : theme.palette.error.light,
      ),
      borderColor: theme.palette.error.main,
    },
    warning: {
      bgColor:
        theme.palette.mode === 'dark' ? theme.palette.warning.dark : theme.palette.warning.light,
      textColor: theme.palette.getContrastText(
        theme.palette.mode === 'dark' ? theme.palette.warning.dark : theme.palette.warning.light,
      ),
      borderColor: theme.palette.warning.main,
    },
    info: {
      bgColor: theme.palette.mode === 'dark' ? theme.palette.info.dark : theme.palette.info.light,
      textColor: theme.palette.getContrastText(
        theme.palette.mode === 'dark' ? theme.palette.info.dark : theme.palette.info.light,
      ),
      borderColor: theme.palette.info.main,
    },
    success: {
      bgColor:
        theme.palette.mode === 'dark' ? theme.palette.success.dark : theme.palette.success.light,
      textColor: theme.palette.getContrastText(
        theme.palette.mode === 'dark' ? theme.palette.success.dark : theme.palette.success.light,
      ),
      borderColor: theme.palette.success.main,
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
