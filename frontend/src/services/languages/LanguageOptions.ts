import type { FilteredListOptions } from '../ApiTypes'

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
