/**
 * Pricing category returned as nested object in event-price responses.
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
 * Availability tier returned as nested object in event-price responses.
 */
export interface PriceRank {
  id: number
  position: number
  sold_out_buffer: number
  description: Record<string, string> | null
  display_description: string | null
}
