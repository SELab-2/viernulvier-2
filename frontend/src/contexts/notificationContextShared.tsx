import { createContext, useContext } from 'react'
import { createRoot, type Root } from 'react-dom/client'

import FloatingAlertStack from '../shared/components/FloatingAlertStack'

import type { FloatingAlertProps } from '../types/FloatingAlertConfig'

/**
 * Position type extracted from FloatingAlertProps.
 * Defines where alerts are rendered on screen.
 */
export type FloatingAlertPosition = NonNullable<FloatingAlertProps['position']>

/**
 * Public payload used to trigger a floating alert.
 * Excludes internal `onClose` handler.
 */
export type FloatingAlertPayload = Partial<Omit<FloatingAlertProps, 'onClose'>>

/**
 * Internal alert entry with unique identifier.
 */
export type FloatingAlertEntry = FloatingAlertPayload & {
  id: number
}

/**
 * Default position for floating alerts when none is provided.
 */
export const DEFAULT_FLOATING_ALERT_POSITION: FloatingAlertPosition = {
  vertical: 'top',
  horizontal: 'right',
}

/**
 * Converts a position object into a stable string key.
 * Used for grouping alerts by screen position.
 */
export const getFloatingAlertPositionKey = (position: FloatingAlertPosition): string =>
  `${position.vertical}-${position.horizontal}`

/**
 * Groups alerts by their screen position.
 *
 * This ensures each FloatingAlertStack only renders alerts
 * belonging to the same position group.
 */
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

/**
 * Public API exposed through React context.
 */
export type NotificationContextValue = {
  showFloatingAlert: (payload: FloatingAlertPayload) => void
  clearFloatingAlert: () => void
  isFallback: boolean
}

/**
 * Notification context used across the application.
 * If undefined, fallback implementation is used instead.
 */
export const NotificationContext = createContext<NotificationContextValue | undefined>(undefined)

/**
 * Internal state for fallback notification renderer.
 * Used when React context provider is not available.
 */
type FallbackState = {
  root: Root | null
  container: HTMLElement | null
}

const fallbackState: FallbackState = {
  root: null,
  container: null,
}

/**
 * Internal incremental ID counter for fallback alerts.
 */
let fallbackAlertId = 0

/**
 * In-memory store of fallback alerts.
 */
let fallbackAlerts: FloatingAlertEntry[] = []

/**
 * Ensures a React root exists for fallback rendering.
 * Creates a DOM container if necessary.
 */
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

/**
 * Renders all fallback alerts into a React root.
 * Groups alerts by position before rendering.
 */
const renderFallbackAlert = () => {
  const root = ensureFallbackRoot()

  /**
   * Internal fallback renderer component.
   * Maps grouped alerts to FloatingAlertStack components.
   */
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

  // Detect test environment for synchronous rendering
  const isTestEnv = typeof process !== 'undefined' && process.env.NODE_ENV === 'test'

  if (isTestEnv) {
    root.render(<FallbackManager alerts={fallbackAlerts} />)
  } else if (typeof window !== 'undefined' && window.requestIdleCallback) {
    // Defer rendering when possible to avoid blocking UI updates
    window.requestIdleCallback(() => {
      root.render(<FallbackManager alerts={fallbackAlerts} />)
    })
  } else {
    // Fallback async scheduling
    Promise.resolve().then(() => {
      root.render(<FallbackManager alerts={fallbackAlerts} />)
    })
  }
}

/**
 * Fallback implementation of showFloatingAlert.
 * Used when NotificationContext is not available.
 */
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

/**
 * Clears all fallback alerts.
 */
export const fallbackClearFloatingAlert = () => {
  fallbackAlerts = []
  if (typeof document !== 'undefined') {
    renderFallbackAlert()
  }
}

/**
 * Hook to access notification system.
 *
 * Falls back to DOM-based implementation when provider is missing.
 */
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
