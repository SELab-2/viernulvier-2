import type { FilteredListOptions } from '../services/ApiTypes'

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

/**
 * Endpoint-specific filter fields for the `/languages/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface LanguageFilters {
  code?: string
  name?: string
  is_active?: boolean
}

/**
 * Options accepted by {@link getLanguages}.
 *
 * Combines pagination (`page`, `pageSize`), language-specific filters
 * ({@link LanguageFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetLanguagesOptions = FilteredListOptions<LanguageFilters>
