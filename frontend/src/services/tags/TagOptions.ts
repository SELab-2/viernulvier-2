import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/tags/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface TagFilters {
  type?: string
  source?: string
  is_enabled?: boolean
  name?: string
}

/**
 * Options accepted by {@link getTags}.
 *
 * Combines pagination (`page`, `pageSize`), tag-specific filters
 * ({@link TagFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetTagsOptions = FilteredListOptions<TagFilters>
