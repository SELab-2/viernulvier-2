import { api } from '../Api'
import { buildListParams } from '../ApiParams'

import type { GetPricesOptions, GetPriceRanksOptions } from './PricingOptions'
import type {
  Price,
  PriceListResponse,
  PriceRank,
  PriceRankListResponse,
} from '../../types/Pricing'

/**
 * Retrieve a single price by its numeric ID.
 */
export const getPrice = async (id: number): Promise<Price> => {
  const res = await api.get<Price>(`/prices/${id}/`)
  return res.data
}

/**
 * Retrieve a paginated list of prices with optional pagination and filtering.
 */
export const getPrices = async (options?: GetPricesOptions): Promise<PriceListResponse> => {
  const res = await api.get<PriceListResponse>('/prices/', {
    params: buildListParams(options),
  })
  return res.data
}

/**
 * Retrieve a single price rank by its numeric ID.
 */
export const getPriceRank = async (id: number): Promise<PriceRank> => {
  const res = await api.get<PriceRank>(`/price-ranks/${id}/`)
  return res.data
}

/**
 * Retrieve a paginated list of price ranks with optional pagination and filtering.
 */
export const getPriceRanks = async (
  options?: GetPriceRanksOptions,
): Promise<PriceRankListResponse> => {
  const res = await api.get<PriceRankListResponse>('/price-ranks/', {
    params: buildListParams(options),
  })
  return res.data
}
