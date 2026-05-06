import { createContext, useContext } from 'react'
import { createRoot, type Root } from 'react-dom/client'

import FloatingAlertStack from '../components/FloatingAlertStack'

import type { FloatingAlertProps } from '../types/FloatingAlertConfig'

export type FloatingAlertPosition = NonNullable<FloatingAlertProps['position']>

export type FloatingAlertPayload = Partial<Omit<FloatingAlertProps, 'onClose'>>

export type FloatingAlertEntry = FloatingAlertPayload & {
  id: number
}

export const DEFAULT_FLOATING_ALERT_POSITION: FloatingAlertPosition = {
  vertical: 'top',
  horizontal: 'right',
}

export const getFloatingAlertPositionKey = (position: FloatingAlertPosition): string =>
  `${position.vertical}-${position.horizontal}`

export const groupAlertsByPosition = (alerts: FloatingAlertEntry[]) => {
  const groups = new Map<
    string,
    { key: string; position: FloatingAlertPosition; alerts: FloatingAlertEntry[] }
  >()

  alerts.forEach((alert) => {
    const position = alert.position ?? DEFAULT_FLOATING_ALERT_POSITION
    const key = getFloatingAlertPositionKey(position)
    const group = groups.get(key)

    if (group) {
      group.alerts.push(alert)
      return
    }

    groups.set(key, { key, position, alerts: [alert] })
  })

  return Array.from(groups.values())
}

export type NotificationContextValue = {
  showFloatingAlert: (payload: FloatingAlertPayload) => void
  clearFloatingAlert: () => void
  isFallback: boolean
}

export const NotificationContext = createContext<NotificationContextValue | undefined>(undefined)

type FallbackState = {
  root: Root | null
  container: HTMLElement | null
}

const fallbackState: FallbackState = {
  root: null,
  container: null,
}

let fallbackAlertId = 0
let fallbackAlerts: FloatingAlertEntry[] = []

const ensureFallbackRoot = () => {
  if (
    fallbackState.root &&
    fallbackState.container &&
    document.body.contains(fallbackState.container)
  ) {
    return fallbackState.root
  }

  let container = document.getElementById('notification-fallback-root')
  if (!container) {
    container = document.createElement('div')
    container.id = 'notification-fallback-root'
    document.body.appendChild(container)
  }

  fallbackState.root = createRoot(container)
  fallbackState.container = container
  return fallbackState.root
}

const renderFallbackAlert = () => {
  const root = ensureFallbackRoot()

  const FallbackManager = ({ alerts }: { alerts: FloatingAlertEntry[] }) => (
    <>
      {groupAlertsByPosition(alerts).map(({ key, position, alerts: positionedAlerts }) => (
        <FloatingAlertStack
          key={key}
          alerts={positionedAlerts.map((alert) => ({
            ...alert,
            open: alert.open !== false,
            message: alert.message ?? '',
            position: alert.position ?? DEFAULT_FLOATING_ALERT_POSITION,
          }))}
          onClose={(id) => {
            fallbackAlerts = fallbackAlerts.filter((currentAlert) => currentAlert.id !== id)
            renderFallbackAlert()
          }}
          position={position}
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
