import { createContext, useContext } from 'react'
import { createRoot, type Root } from 'react-dom/client'

import FloatingAlert from '../components/FloatingAlert'

import type { FloatingAlertProps } from '../types/FloatingAlertConfig'

export type FloatingAlertPayload = Partial<Omit<FloatingAlertProps, 'onClose' | 'position'>>

export type FloatingAlertEntry = FloatingAlertPayload & {
  id: number
}

export type NotificationContextValue = {
  showFloatingAlert: (payload: FloatingAlertPayload) => void
  clearFloatingAlert: () => void
  isFallback: boolean
}

export const NotificationContext = createContext<NotificationContextValue | undefined>(undefined)

type FallbackState = {
  root: Root | null
}

const fallbackState: FallbackState = {
  root: null,
}

let fallbackAlertId = 0
let fallbackAlerts: FloatingAlertEntry[] = []

const ensureFallbackRoot = () => {
  if (fallbackState.root) {
    return fallbackState.root
  }

  let container = document.getElementById('notification-fallback-root')
  if (!container) {
    container = document.createElement('div')
    container.id = 'notification-fallback-root'
    document.body.appendChild(container)
  }

  fallbackState.root = createRoot(container)
  return fallbackState.root
}

const renderFallbackAlert = () => {
  const root = ensureFallbackRoot()

  const FallbackManager = ({ alerts }: { alerts: FloatingAlertEntry[] }) => (
    <>
      {alerts.map((alert, index) => (
        <FloatingAlert
          key={alert.id}
          open={alert.open !== false}
          onClose={() => {
            fallbackAlerts = fallbackAlerts.filter((currentAlert) => currentAlert.id !== alert.id)
            renderFallbackAlert()
          }}
          message={alert.message ?? ''}
          title={alert.title}
          severity={alert.severity ?? 'info'}
          autoCloseDuration={alert.autoCloseDuration}
          stackOffsetPx={index * 88}
        />
      ))}
    </>
  )

  // In test environments, render synchronously. In production, defer to avoid React lifecycle conflicts.
  const isTestEnv = typeof process !== 'undefined' && process.env.NODE_ENV === 'test'

  if (isTestEnv) {
    root.render(<FallbackManager alerts={fallbackAlerts} />)
  } else if (typeof window !== 'undefined' && window.requestIdleCallback) {
    window.requestIdleCallback(() => {
      root.render(<FallbackManager alerts={fallbackAlerts} />)
    })
  } else {
    Promise.resolve().then(() => {
      root.render(<FallbackManager alerts={fallbackAlerts} />)
    })
  }
}

export const fallbackShowFloatingAlert = (payload: FloatingAlertPayload) => {
  if (typeof document === 'undefined') {
    return
  }

  const entry: FloatingAlertEntry = {
    ...payload,
    open: true,
    id: ++fallbackAlertId,
  }

  fallbackAlerts = [...fallbackAlerts, entry]
  renderFallbackAlert()
}

export const fallbackClearFloatingAlert = () => {
  fallbackAlerts = []
  if (typeof document !== 'undefined') {
    renderFallbackAlert()
  }
}

export const useNotification = (): NotificationContextValue => {
  const ctx = useContext(NotificationContext)
  if (ctx) {
    return ctx
  }

  return {
    isFallback: true,
    showFloatingAlert: fallbackShowFloatingAlert,
    clearFloatingAlert: fallbackClearFloatingAlert,
  }
}
