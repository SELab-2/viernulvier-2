import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/blogs/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface BlogFilters {
  production?: number
  published?: boolean
  slug?: string
  title?: string
}

/**
 * Options accepted by {@link getBlogs}.
 *
 * Combines pagination (`page`, `pageSize`), event-specific filters
 * ({@link BlogFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetBlogsOptions = FilteredListOptions<BlogFilters>
