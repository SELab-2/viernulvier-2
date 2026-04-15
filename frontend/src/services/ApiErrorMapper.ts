import { ApiError } from './ApiTypes'
import i18n from '../i18n'

/** Translation keys for the most common HTTP error statuses. */
const STATUS_MESSAGE_KEYS: Record<number, string> = {
  400: 'apiErrors.status.400',
  401: 'apiErrors.status.401',
  403: 'apiErrors.status.403',
  404: 'apiErrors.status.404',
  500: 'apiErrors.status.500',
}

/**
 * Convert an unknown request error to a typed `ApiError` when possible.
 *
 * This keeps Api.ts simple and makes the normalization logic testable without
 * importing the full Axios client setup.
 */
export const normalizeApiError = (
  error: unknown,
  isAxiosError: (error: unknown) => boolean,
): unknown => {
  if (isAxiosError(error)) {
    const status = (error as { response?: { status?: number } }).response?.status ?? 0
    const knownStatusTranslationKey = STATUS_MESSAGE_KEYS[status]
    const message =
      (knownStatusTranslationKey ? i18n.t(knownStatusTranslationKey) : null) ??
      (status > 0
        ? i18n.t('apiErrors.status.genericWithCode', { status })
        : i18n.t('apiErrors.network'))

    return new ApiError(status, message)
  }

  return error
}
