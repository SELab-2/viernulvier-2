/**
 * Genre object returned by the backend `/genres/` endpoints.
 */
export interface GenreUseAs {
  id: number
  name: string
}

export interface Genre {
  id: number
  type: string
  use_as: GenreUseAs
  name: Record<string, string> | null
  display_name: string | null
  vendor_id: string | null
}

/**
 * Paginated response shape for `GET /genres/`.
 */
export interface GenreListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Genre[]
}
