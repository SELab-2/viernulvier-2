/**
 * Language object returned by the backend `/languages/` endpoints.
 */
export interface Language {
  code: string
  name: string
  is_active: boolean
}

/**
 * Paginated response shape for `GET /languages/`.
 */
export interface LanguageListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Language[]
}
