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
 *
 * The backend returns DRF pagination fields (`count`, `next`, `previous`) in
 * addition to `results`. These metadata fields are optional in this interface
 * so tests or mocks can provide only `results` when needed.
 */
export interface LanguageListResponse {
  results: Language[]
  count?: number
  next?: string | null
  previous?: string | null
}
