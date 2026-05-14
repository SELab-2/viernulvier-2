/**
 * Utilities for handling floating alert state during navigation.
 *
 * This module is used in conjunction with React Router navigation to pass
 * temporary UI state (floating alerts) between routes without relying on
 * global state management.
 *
 * Typical use case:
 * - Show success/error/info messages after a redirect
 * - Pass transient UI feedback via router state
 */

import type { FloatingAlertSeverity } from '../types/FloatingAlertConfig'
import type { NavigateFunction } from 'react-router-dom'

/**
 * Payload describing a floating alert to be shown after navigation.
 *
 * All fields are optional so callers can construct minimal alerts,
 * but the final state will always mark the alert as `open: true`.
 */
type FloatingAlertPayload = {
  open?: boolean
  message?: string
  severity?: FloatingAlertSeverity
  title?: string
  autoCloseDuration?: number
}

/**
 * Creates a normalized floating alert state object.
 *
 * This ensures that any alert passed into navigation is automatically
 * opened (`open: true`) regardless of the provided payload.
 *
 * @param alert Partial floating alert configuration
 * @returns State object compatible with React Router `location.state`
 */
export const createFloatingAlertState = (alert: FloatingAlertPayload) => ({
  floatingAlert: { ...alert, open: true },
})

/**
 * Navigates to a new route while attaching a floating alert to router state.
 *
 * This allows the target page to read `location.state.floatingAlert`
 * and display a transient message to the user.
 *
 * @param navigate React Router navigate function
 * @param to Target route path
 * @param alert Floating alert payload to display after navigation
 * @param options Optional navigation settings (e.g. replace history entry)
 */
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
