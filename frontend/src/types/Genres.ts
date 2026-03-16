/**
 * Genre object returned by the backend `/genres/` endpoints.
 */
export interface Genre {
  id: number
  type: string
  use_as: number
  name: Record<string, string> | null
  display_name: string | null
  vendor_id: string | null
}

/**
 * Paginated response shape for `GET /genres/`.
 *
 * The backend currently returns DRF pagination fields (`count`, `next`,
 * `previous`) in addition to `results`. These metadata fields are optional in
 * this interface so tests or mocks can provide only `results` when needed.
 */
export interface GenreListResponse {
  results: Genre[]
  count?: number
  next?: string | null
  previous?: string | null
}
