import CloseIcon from '@mui/icons-material/Close'
import { Snackbar, Box, IconButton } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { useEffect } from 'react'

import { tokens } from '../../theme/tokens'

import type { FloatingAlertProps, FloatingAlertSeverity } from '../../types/FloatingAlertConfig'

/**
 * FloatingAlert
 *
 * A reusable notification component that supports:
 * - Severity-based styling (error, warning, info, success)
 * - Auto-dismiss behavior
 * - Optional standalone rendering (without MUI Snackbar wrapper)
 * - Accessible alert semantics
 *
 */
const FloatingAlert = ({
  open,
  onClose,
  message,
  title,
  severity = 'info',
  autoCloseDuration = 4000,
  position = { vertical: 'top', horizontal: 'right' },
  disableFloatingWrapper = false,
}: FloatingAlertProps) => {
  const theme = useTheme()

  /**
   * Visual configuration per severity level.
   * Controls background, border, and text colors.
   */
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

  /**
   * Handles auto-close behavior when using inline (non-Snackbar) mode.
   *
   * NOTE:
   * - Only active when disableFloatingWrapper = true
   * - Respects autoCloseDuration (if not null)
   * - Cleans up timeout on unmount or dependency change
   */
  useEffect(() => {
    if (!disableFloatingWrapper || !open || autoCloseDuration === null) {
      return undefined
    }

    const timeout = window.setTimeout(onClose, autoCloseDuration)
    return () => window.clearTimeout(timeout)
  }, [autoCloseDuration, disableFloatingWrapper, onClose, open])

  /**
   * Core alert UI content.
   * Shared between Snackbar and stack rendering modes.
   */
  const content = (
    <Box data-testid="floating-alert">
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
    </Box>
  )

  /**
   * Inline mode (used inside FloatingAlertStack)
   * No Snackbar wrapper is used here.
   */
  if (disableFloatingWrapper) {
    return open ? content : null
  }

  /**
   * Default mode: MUI Snackbar wrapper handles positioning + animation.
   */
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
    >
      {content}
    </Snackbar>
  )
}

export default FloatingAlert
