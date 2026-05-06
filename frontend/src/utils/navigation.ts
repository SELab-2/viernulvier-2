import type { NavigateFunction } from 'react-router-dom'

type FloatingAlertPayload = {
  open?: boolean
  message?: string
  severity?: 'error' | 'warning' | 'info' | 'success'
  title?: string
  autoCloseDuration?: number
}

export const redirectWithFloatingAlert = (
  navigate: NavigateFunction,
  to: string,
  alert: FloatingAlertPayload,
  options?: { replace?: boolean },
) => {
  navigate(to, { state: { floatingAlert: { ...alert, open: true } }, replace: !!options?.replace })
}

export default redirectWithFloatingAlert
