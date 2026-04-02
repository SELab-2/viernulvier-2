import axios from 'axios'
import { normalizeApiError } from './ApiErrorMapper'

// When running Vite, `process.env.VITE_PUBLIC_API_KEY` is replaced from envdefs.
// In Jest/tests, this value is available via process.env and no import.meta usage
// is needed, avoiding `Cannot use 'import.meta' outside a module` bug.
const API_KEY: string = process.env.VITE_PUBLIC_API_KEY ?? ''

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
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
})

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
    return Promise.reject(normalizeApiError(error, axios.isAxiosError))
  },
)
