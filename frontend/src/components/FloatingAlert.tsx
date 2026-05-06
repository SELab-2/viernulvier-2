import CloseIcon from '@mui/icons-material/Close'
import { Snackbar, Box, IconButton } from '@mui/material'
import { useTheme } from '@mui/material/styles'

import { tokens } from '../theme/tokens'

import type { FloatingAlertProps, FloatingAlertSeverity } from '../types/FloatingAlertConfig'

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
  stackOffsetPx = 0,
}: FloatingAlertProps) => {
  const theme = useTheme()

  const severityConfig: Record<
    FloatingAlertSeverity,
    { bgColor: string; textColor: string; borderColor: string; titleColor: string }
  > = {
    error: {
      bgColor: theme.palette.error.main,
      textColor: theme.palette.error.contrastText,
      borderColor: theme.palette.error.dark,
      titleColor: theme.palette.error.main,
    },
    warning: {
      bgColor: theme.palette.warning.main,
      textColor: theme.palette.text.primary,
      borderColor: theme.palette.warning.main,
      titleColor: theme.palette.warning.main,
    },
    info: {
      bgColor: theme.palette.info.main,
      textColor: theme.palette.text.primary,
      borderColor: theme.palette.info.main,
      titleColor: theme.palette.info.main,
    },
    success: {
      bgColor: theme.palette.success.main,
      textColor: theme.palette.text.primary,
      borderColor: theme.palette.success.main,
      titleColor: theme.palette.success.main,
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
                top: `calc(var(--navbar-height, 64px) + 8px + ${stackOffsetPx}px + env(safe-area-inset-top, 0px))`,
              },
              '&.MuiSnackbar-anchorOriginTopCenter': {
                top: `calc(var(--navbar-height, 64px) + 8px + ${stackOffsetPx}px + env(safe-area-inset-top, 0px))`,
              },
              '&.MuiSnackbar-anchorOriginTopRight': {
                top: `calc(var(--navbar-height, 64px) + 8px + ${stackOffsetPx}px + env(safe-area-inset-top, 0px))`,
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
          borderLeft: `4px solid ${config.titleColor}`,
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
                color: config.titleColor,
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
              bgcolor: theme.palette.action.hover,
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
