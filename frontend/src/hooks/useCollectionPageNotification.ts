/**
 * Shared notification hook for collection pages (blogs, productions, media, series).
 * Manages floating alert state and display for data-fetching errors.
 *
 * Usage:
 *   const { showFloatingAlert, clearFloatingAlert } =
 *     useCollectionPageNotification('blogs.home.error.notification')
 *
 *   Then in fetch handler:
 *   } catch (error) {
 *     showFloatingAlert()
 *   }
 */

import { useCallback, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import { useNotification } from '../contexts/notificationContextShared'
import { ApiError } from '../services/ApiTypes'
import { ALERT_SEVERITIES } from '../types/FloatingAlertConfig'

export type UseCollectionPageNotificationResult = {
  showFloatingAlert: (error?: unknown) => void
  clearFloatingAlert: () => void
}

/**
 * Composable hook for collection pages to manage floating alert notifications.
 *
 * @param messageKey - i18n key for the floating alert message
 * @returns Object with showFloatingAlert and clearFloatingAlert callbacks
 */
export const useCollectionPageNotification = (
  messageKey: string,
): UseCollectionPageNotificationResult => {
  const { t } = useTranslation()
  const {
    showFloatingAlert: contextShowFloatingAlert,
    clearFloatingAlert: contextClearFloatingAlert,
  } = useNotification()
  const floatingErrorMessageRef = useRef(t(messageKey))

  // Keep the translated message in sync when language changes
  useEffect(() => {
    floatingErrorMessageRef.current = t(messageKey)
  }, [messageKey, t])

  const showFloatingAlert = useCallback(
    (error?: unknown) => {
      if (error instanceof ApiError) {
        const { message: apiMessage, status } = error

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

  const clearFloatingAlert = useCallback(() => {
    contextClearFloatingAlert()
  }, [contextClearFloatingAlert])

  return {
    showFloatingAlert,
    clearFloatingAlert,
  }
}
