import { Box } from '@mui/material'

import FloatingAlert from './FloatingAlert'

import type { FloatingAlertProps } from '../../types/FloatingAlertConfig'
import type { SxProps, Theme } from '@mui/material/styles'

export type FloatingAlertStackEntry = Omit<FloatingAlertProps, 'onClose'> & {
  id: number
}

export type FloatingAlertStackProps = {
  alerts: FloatingAlertStackEntry[]
  onClose: (id: number) => void
  position?: NonNullable<FloatingAlertProps['position']>
}

const DEFAULT_POSITION: NonNullable<FloatingAlertProps['position']> = {
  vertical: 'top',
  horizontal: 'right',
}

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
