import { Box } from '@mui/material'

import FloatingAlert from './FloatingAlert'

import type { FloatingAlertProps } from '../../types/FloatingAlertConfig'
import type { SxProps, Theme } from '@mui/material/styles'

/**
 * Internal representation of an alert inside the FloatingAlertStack.
 *
 * This extends FloatingAlertProps but removes `onClose` because
 * the stack centrally manages closing behavior via alert id.
 */
export type FloatingAlertStackEntry = Omit<FloatingAlertProps, 'onClose'> & {
  /**
   * Unique identifier used for rendering and closing the alert.
   */
  id: number
}

/**
 * Props for FloatingAlertStack component.
 *
 * This component is responsible for rendering multiple floating alerts
 * in a fixed overlay stack
 */
export type FloatingAlertStackProps = {
  /**
   * List of active alerts to display.
   */
  alerts: FloatingAlertStackEntry[]

  /**
   * Callback triggered when an alert is closed.
   * Receives the alert id.
   */
  onClose: (id: number) => void

  /**
   * Position configuration for the stack.
   * Controls vertical and horizontal alignment.
   */
  position?: NonNullable<FloatingAlertProps['position']>
}

/**
 * Default position for floating alerts if none is provided.
 */
const DEFAULT_POSITION: NonNullable<FloatingAlertProps['position']> = {
  vertical: 'top',
  horizontal: 'right',
}

/**
 * Returns horizontal positioning styles for the alert stack.
 *
 * This controls both alignment and screen anchoring.
 */
const getHorizontalSx = (
  horizontal: NonNullable<FloatingAlertStackProps['position']>['horizontal'],
): SxProps<Theme> => {
  if (horizontal === 'left') {
    return { left: 16, alignItems: 'flex-start' }
  }

  if (horizontal === 'center') {
    return { left: '50%', transform: 'translateX(-50%)', alignItems: 'center' }
  }

  return { right: 16, alignItems: 'flex-end' }
}

/**
 * FloatingAlertStack
 *
 * A layout component that renders multiple FloatingAlert components
 * in a fixed-position stack (similar to toast notifications).
 *
 * Features:
 * - Supports top/bottom positioning
 * - Supports left/center/right alignment
 * - Handles safe-area insets (mobile support)
 * - Prevents pointer blocking on empty areas
 * - Delegates actual alert rendering to FloatingAlert
 *
 * Behavior:
 * - Empty list -> renders nothing
 * - Alerts are stacked vertically with spacing
 * - Top stack grows downward; bottom stack grows upward
 */
const FloatingAlertStack = ({
  alerts,
  onClose,
  position = DEFAULT_POSITION,
}: FloatingAlertStackProps) => {
  if (alerts.length === 0) {
    return null
  }

  const verticalSx: SxProps<Theme> =
    position.vertical === 'top'
      ? {
          top: 'calc(var(--navbar-height, 64px) + 8px + env(safe-area-inset-top, 0px))',
          flexDirection: 'column',
        }
      : {
          bottom: 'calc(16px + env(safe-area-inset-bottom, 0px))',
          flexDirection: 'column-reverse',
        }

  return (
    <Box
      data-testid="floating-alert-stack"
      sx={{
        position: 'fixed',
        zIndex: (theme) => theme.zIndex.snackbar,
        display: 'flex',
        gap: 1.5,
        maxWidth: 'calc(100vw - 32px)',
        pointerEvents: 'none',
        ...(verticalSx as object),
        ...(getHorizontalSx(position.horizontal) as object),
        '& [data-testid="floating-alert"]': {
          pointerEvents: 'auto',
          width: '100%',
          maxWidth: 400,
        },
      }}
    >
      {alerts.map((alert) => (
        <FloatingAlert
          key={alert.id}
          open={alert.open}
          onClose={() => onClose(alert.id)}
          message={alert.message}
          title={alert.title}
          severity={alert.severity}
          autoCloseDuration={alert.autoCloseDuration}
          position={alert.position ?? position}
          disableFloatingWrapper
        />
      ))}
    </Box>
  )
}

export default FloatingAlertStack
