import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import {
  NotificationContext,
  type FloatingAlertEntry,
  type FloatingAlertPayload,
} from './notificationContextShared'
import FloatingAlert from '../components/FloatingAlert'
import { ALERT_SEVERITIES } from '../types/FloatingAlertConfig'

type NotificationProviderProps = {
  children: ReactNode
}

export const NotificationProvider = ({ children }: NotificationProviderProps) => {
  const location = useLocation()
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState<FloatingAlertEntry[]>([])

  const showFloatingAlert = (payload: FloatingAlertPayload) => {
    setAlerts((currentAlerts) => [
      ...currentAlerts,
      {
        ...payload,
        open: true,
        id: currentAlerts.length > 0 ? Math.max(...currentAlerts.map((alert) => alert.id)) + 1 : 1,
      },
    ])
  }

  const clearFloatingAlert = () => {
    setAlerts([])
  }

  const consumedNavigationKeyRef = useRef<string | null>(null)

  useEffect(() => {
    if (!location.key || consumedNavigationKeyRef.current === location.key) {
      return
    }

    const state = location.state as { floatingAlert?: FloatingAlertPayload } | null | undefined
    if (state?.floatingAlert?.message) {
      consumedNavigationKeyRef.current = location.key
      Promise.resolve().then(() => {
        showFloatingAlert({
          message: state.floatingAlert!.message ?? '',
          severity: state.floatingAlert!.severity ?? ALERT_SEVERITIES.error,
          title: state.floatingAlert!.title,
          autoCloseDuration: state.floatingAlert!.autoCloseDuration,
        })
        navigate(location.pathname, { replace: true, state: {} })
      })
    }
  }, [location.key, location.state, location.pathname, navigate])

  const value = useMemo(() => ({ showFloatingAlert, clearFloatingAlert, isFallback: false }), [])

  return (
    <NotificationContext.Provider value={value}>
      {children}
      {alerts.map((alert, index) => (
        <FloatingAlert
          key={alert.id}
          open={alert.open !== false}
          onClose={() => {
            setAlerts((currentAlerts) =>
              currentAlerts.filter((currentAlert) => currentAlert.id !== alert.id),
            )
          }}
          message={alert.message ?? ''}
          title={alert.title}
          severity={alert.severity}
          autoCloseDuration={alert.autoCloseDuration}
          stackOffsetPx={index * 88}
        />
      ))}
    </NotificationContext.Provider>
  )
}
