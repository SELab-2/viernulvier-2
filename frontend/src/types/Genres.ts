import type { ListResponse } from './Common'

/**
 * Genre object returned by the backend `/genres/` endpoints.
 */
export interface Genre {
  id: number
  type: string
  name: Record<string, string> | null
  display_name: string | null
  vendor_id: string | null
}

/**
 * Paginated response shape for `GET /genres/`.
 */
export type GenreListResponse = ListResponse<Genre>
