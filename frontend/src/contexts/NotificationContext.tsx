import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import {
  DEFAULT_FLOATING_ALERT_POSITION,
  NotificationContext,
  type FloatingAlertEntry,
  type FloatingAlertPayload,
  groupAlertsByPosition,
} from './notificationContextShared'
import FloatingAlertStack from '../shared/components/FloatingAlertStack'
import { ALERT_SEVERITIES } from '../types/FloatingAlertConfig'

type NotificationProviderProps = {
  children: ReactNode
}

/**
 * Global notification provider that manages floating alerts for the entire app.
 *
 * Responsibilities:
 * - Stores active alerts in local state
 * - Provides API to show and clear alerts
 * - Handles route-based (navigation state) alerts
 * - Renders grouped FloatingAlertStack components per screen position
 */
export const NotificationProvider = ({ children }: NotificationProviderProps) => {
  const location = useLocation()
  const navigate = useNavigate()

  /**
   * Internal alert queue.
   * Each entry represents a single floating alert instance.
   */
  const [alerts, setAlerts] = useState<FloatingAlertEntry[]>([])

  /**
   * Adds a new floating alert to the global stack.
   * Automatically assigns a unique incremental id.
   */
  const showFloatingAlert = useCallback((payload: FloatingAlertPayload) => {
    setAlerts((currentAlerts) => [
      ...currentAlerts,
      {
        ...payload,
        open: true,
        id: currentAlerts.length > 0 ? Math.max(...currentAlerts.map((alert) => alert.id)) + 1 : 1,
      },
    ])
  }, [])

  /**
   * Clears all active floating alerts.
   */
  const clearFloatingAlert = useCallback(() => {
    setAlerts([])
  }, [])

  /**
   * Removes a single alert by id.
   * Used when user closes an individual notification.
   */
  const closeFloatingAlert = useCallback((id: number) => {
    setAlerts((currentAlerts) => currentAlerts.filter((currentAlert) => currentAlert.id !== id))
  }, [])

  /**
   * Prevents duplicate consumption of route-based alerts
   * for the same navigation event.
   */
  const consumedNavigationKeyRef = useRef<string | null>(null)

  /**
   * Listens for floating alerts passed via router navigation state.
   *
   * Example use case:
   * navigate('/page', { state: { floatingAlert: {...} } })
   */
  useEffect(() => {
    if (!location.key || consumedNavigationKeyRef.current === location.key) {
      return
    }

    const state = location.state as { floatingAlert?: FloatingAlertPayload } | null | undefined
    const floatingAlert = state?.floatingAlert

    if (floatingAlert?.message) {
      consumedNavigationKeyRef.current = location.key

      Promise.resolve().then(() => {
        showFloatingAlert({
          ...floatingAlert,
          message: floatingAlert.message,
          severity: floatingAlert.severity ?? ALERT_SEVERITIES.error,
        })

        navigate(
          {
            pathname: location.pathname,
            search: location.search,
            hash: location.hash,
          },
          { replace: true, state: null },
        )
      })
    }
  }, [
    location.key,
    location.state,
    location.pathname,
    location.search,
    location.hash,
    navigate,
    showFloatingAlert,
  ])

  /**
   * Public context API exposed to the app.
   */
  const value = useMemo(
    () => ({ showFloatingAlert, clearFloatingAlert, isFallback: false }),
    [clearFloatingAlert, showFloatingAlert],
  )

  /**
   * Groups alerts by screen position (top-left, bottom-right, etc.)
   * so multiple stacks can be rendered independently.
   */
  const alertGroups = groupAlertsByPosition(alerts)

  return (
    <NotificationContext.Provider value={value}>
      {children}

      {/* Render one FloatingAlertStack per position group */}
      {alertGroups.map(({ key, position, alerts: positionedAlerts }) => (
        <FloatingAlertStack
          key={key}
          alerts={positionedAlerts.map((alert) => ({
            ...alert,
            open: alert.open !== false,
            message: alert.message ?? '',
            position: alert.position ?? DEFAULT_FLOATING_ALERT_POSITION,
          }))}
          onClose={closeFloatingAlert}
          position={position}
        />
      ))}
    </NotificationContext.Provider>
  )
}
