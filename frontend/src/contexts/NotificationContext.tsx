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

export const NotificationProvider = ({ children }: NotificationProviderProps) => {
  const location = useLocation()
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState<FloatingAlertEntry[]>([])

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

  const clearFloatingAlert = useCallback(() => {
    setAlerts([])
  }, [])

  const closeFloatingAlert = useCallback((id: number) => {
    setAlerts((currentAlerts) => currentAlerts.filter((currentAlert) => currentAlert.id !== id))
  }, [])

  const consumedNavigationKeyRef = useRef<string | null>(null)

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

  const value = useMemo(
    () => ({ showFloatingAlert, clearFloatingAlert, isFallback: false }),
    [clearFloatingAlert, showFloatingAlert],
  )
  const alertGroups = groupAlertsByPosition(alerts)

  return (
    <NotificationContext.Provider value={value}>
      {children}
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
