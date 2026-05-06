import type { FloatingAlertSeverity } from '../types/FloatingAlertConfig'
import type { NavigateFunction } from 'react-router-dom'

type FloatingAlertPayload = {
  open?: boolean
  message?: string
  severity?: FloatingAlertSeverity
  title?: string
  autoCloseDuration?: number
}

export const createFloatingAlertState = (alert: FloatingAlertPayload) => ({
  floatingAlert: { ...alert, open: true },
})

export const redirectWithFloatingAlert = (
  navigate: NavigateFunction,
  to: string,
  alert: FloatingAlertPayload,
  options?: { replace?: boolean },
) => {
  navigate(to, {
    state: createFloatingAlertState(alert),
    ...(options?.replace === undefined ? null : { replace: options.replace }),
  })
}

export default redirectWithFloatingAlert
