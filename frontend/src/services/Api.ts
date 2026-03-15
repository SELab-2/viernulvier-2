import axios from 'axios'
import { ApiError } from './ApiTypes'

const API_KEY: string = import.meta.env.VITE_PUBLIC_API_KEY

/**
 * Shared Axios instance pre-configured with the correct base URL and API key
 * header. Use this in every service instead of calling `axios` directly.
 *
 * A response interceptor is attached below that converts every failed request
 * into a typed `ApiError`. This means service functions do not need their own
 * try/catch blocks for HTTP errors — any uncaught error reaching a component
 * will already be an `ApiError` with a readable `status` and `message`.
 *
 * @example
 * const res = await api.get('/genres/');
 * console.log(res.data);
 */
export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
})

/** Human-readable messages for the most common HTTP error statuses. */
const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request parameters.',
  401: 'Not authenticated. Please log in.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  500: 'An internal server error occurred. Please try again later.',
}

/**
 * Response interceptor that normalises every failed request into an `ApiError`.
 *
 * - For responses with an HTTP error status (4xx / 5xx), the status code and a
 *   descriptive message are captured from the response.
 * - For requests that never received a response (network failure, timeout,
 *   CORS block), status `0` is used.
 * - All other unexpected errors are re-thrown as-is.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status ?? 0
      const message =
        STATUS_MESSAGES[status] ??
        (status > 0
          ? `Request failed with status ${status}.`
          : 'A network error occurred. Please check your connection.')

      return Promise.reject(new ApiError(status, message))
    }

    // Not an Axios error - propagate unchanged.
    return Promise.reject(error)
  },
)