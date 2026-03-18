import { ApiError } from './ApiTypes'

/** Human-readable messages for the most common HTTP error statuses. */
const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request parameters.',
  401: 'Not authenticated. Please log in.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  500: 'An internal server error occurred. Please try again later.',
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
    const message =
      STATUS_MESSAGES[status] ??
      (status > 0
        ? `Request failed with status ${status}.`
        : 'A network error occurred. Please check your connection.')

    return new ApiError(status, message)
  }

  return error
}
