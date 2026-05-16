import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Shape of the navigation state used to trigger a one-time floating alert.
 */
type FloatingAlertState = {
  open?: boolean
  message?: string
}

/**
 * Typed wrapper for route state used by React Router.
 */
type NavigationState = {
  floatingAlert?: FloatingAlertState
}

/**
 * Return value of {@link useFloatingAlertOnce}.
 */
type FloatingAlertOnceResult = {
  isOpen: boolean
  message: string | null
  close: () => void
}

/**
 * Reads a `floatingAlert` object from the router state and exposes it once.
 *
 * The hook clears browser history state after showing the alert so it
 * will not reappear on back/refresh.
 */
const useFloatingAlertOnce = (): FloatingAlertOnceResult => {
  const location = useLocation()
  const nav = location as { state?: NavigationState }
  const alertState = nav.state?.floatingAlert

  const [closedKeys, setClosedKeys] = useState<Record<string, boolean>>({})
  const isOpen = Boolean(alertState?.open) && !closedKeys[location.key]
  const message = alertState?.message ?? null

  useEffect(() => {
    if (alertState?.open) {
      try {
        window.history.replaceState({}, document.title)
      } catch {
        /* ignore */
      }
    }
  }, [alertState?.open, location.key])

  return {
    isOpen,
    message,
    close: () => {
      setClosedKeys((previous) => ({
        ...previous,
        [location.key]: true,
      }))
    },
  }
}

export default useFloatingAlertOnce
