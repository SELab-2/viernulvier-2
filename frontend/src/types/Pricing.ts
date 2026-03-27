/**
 * Price object returned by the backend `/prices/` endpoints.
 */
export interface Price {
  id: number
  type: string
  visibility: string
  membership: string
  minimum: number | null
  maximum: number | null
  step: number | null
  sort_order: number
  cineville_box: boolean
  description: Record<string, string> | null
  display_description: string | null
}

/**
 * PriceRank object returned by the backend `/price-ranks/` endpoints.
 */
export interface PriceRank {
  id: number
  position: number
  sold_out_buffer: number
  description: Record<string, string> | null
  display_description: string | null
}

/**
 * Paginated response shape for `GET /prices/`.
 */
export interface PriceListResponse {
  results: Price[]
  count?: number
  next?: string | null
  previous?: string | null
}

/**
 * Paginated response shape for `GET /price-ranks/`.
 */
export interface PriceRankListResponse {
  results: PriceRank[]
  count?: number
  next?: string | null
  previous?: string | null
}
