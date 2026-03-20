import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/prices/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface PriceFilters {
  type?: string
  visibility?: string
  membership?: string
  cineville_box?: boolean
  description?: string
}

/**
 * Options accepted by {@link getPrices}.
 *
 * Combines pagination (`page`, `pageSize`), price-specific filters
 * ({@link PriceFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetPricesOptions = FilteredListOptions<PriceFilters>

/**
 * Endpoint-specific filter fields for the `/price-ranks/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface PriceRankFilters {
  position?: number
  position_gte?: number
  position_lte?: number
  description?: string
}

/**
 * Options accepted by {@link getPriceRanks}.
 *
 * Combines pagination (`page`, `pageSize`), price-rank-specific filters
 * ({@link PriceRankFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetPriceRanksOptions = FilteredListOptions<PriceRankFilters>
