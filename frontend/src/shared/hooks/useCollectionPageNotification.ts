import { useCallback, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import { useNotification } from '../../contexts/notificationContextShared'
import { ApiError } from '../../services/ApiTypes'
import { ALERT_SEVERITIES } from '../../types/FloatingAlertConfig'

/**
 * Return type of {@link useCollectionPageNotification}.
 *
 * Exposes functions to trigger or clear floating alerts.
 */
export type UseCollectionPageNotificationResult = {
  /**
   * Shows a floating alert.
   *
   * @param error Optional error object. If provided, it may influence message/severity.
   */
  showFloatingAlert: (error?: unknown) => void

  /**
   * Clears any active floating alert.
   */
  clearFloatingAlert: () => void
}

/**
 * useCollectionPageNotification
 *
 * A composable hook that wraps the global notification system
 * and provides collection-page-specific error handling logic.
 *
 * @param messageKey - i18n key used as fallback error message
 *
 * @returns Object containing:
 * - `showFloatingAlert(error?)` -> triggers notification
 * - `clearFloatingAlert()` -> dismisses notification
 */
export const useCollectionPageNotification = (
  messageKey: string,
): UseCollectionPageNotificationResult => {
  const { t } = useTranslation()

  const {
    showFloatingAlert: contextShowFloatingAlert,
    clearFloatingAlert: contextClearFloatingAlert,
  } = useNotification()

  /**
   * Stores the translated fallback message.
   * Uses a ref so updates don't re-trigger callbacks.
   */
  const floatingErrorMessageRef = useRef(t(messageKey))

  /**
   * Keep translated message in sync when language or key changes.
   */
  useEffect(() => {
    floatingErrorMessageRef.current = t(messageKey)
  }, [messageKey, t])

  /**
   * Shows a floating alert based on optional error input.
   *
   * Behavior:
   * - ApiError 429 -> warning with API-provided message
   * - Other errors -> fallback translated message
   */
  const showFloatingAlert = useCallback(
    (error?: unknown) => {
      if (error instanceof ApiError) {
        const { message: apiMessage, status } = error

        // Rate limiting is treated as a warning instead of error
        if (status === 429) {
          contextShowFloatingAlert({
            message: apiMessage,
            severity: ALERT_SEVERITIES.warning,
          })
          return
        }
      }

      contextShowFloatingAlert({
        message: floatingErrorMessageRef.current,
        severity: ALERT_SEVERITIES.error,
      })
    },
    [contextShowFloatingAlert],
  )

  /**
   * Clears the currently visible floating alert.
   */
  const clearFloatingAlert = useCallback(() => {
    contextClearFloatingAlert()
  }, [contextClearFloatingAlert])

  return {
    showFloatingAlert,
    clearFloatingAlert,
  }
}
