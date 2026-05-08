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

  const [isOpen, setIsOpen] = useState(Boolean(nav.state?.floatingAlert?.open))
  const [message, setMessage] = useState(nav.state?.floatingAlert?.message ?? null)

  useEffect(() => {
    const nextOpen = Boolean(nav.state?.floatingAlert?.open)
    const nextMessage = nav.state?.floatingAlert?.message ?? null

    setIsOpen(nextOpen)
    setMessage(nextMessage)

    if (nextOpen) {
      try {
        window.history.replaceState({}, document.title)
      } catch {
        /* ignore */
      }
    }
  }, [location.key, nav.state?.floatingAlert?.message, nav.state?.floatingAlert?.open])

  return {
    isOpen,
    message,
    close: () => setIsOpen(false),
  }
}

export default useFloatingAlertOnce
