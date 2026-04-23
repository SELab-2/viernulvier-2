/**
 * Common types used across the frontend, especially for API responses.
 *
 * This file is intended for types that are shared across multiple features or services,
 * such as the standard structure of paginated list responses from the API.
 */
export interface ListResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
