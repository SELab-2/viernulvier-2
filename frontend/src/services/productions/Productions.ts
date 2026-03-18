import type { Production, ProductionListResponse } from '../../types/Productions'
import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetProductionsOptions } from './ProductionOptions'

/**
 * Retrieve a single production by its numeric ID.
 */
export const getProduction = async (id: number): Promise<Production> => {
  const res = await api.get<Production>(`/productions/${id}/`)
  return res.data
}

/**
 * Retrieve a list of productions with optional pagination and filtering.
 */
export const getProductions = async (
  options?: GetProductionsOptions,
): Promise<ProductionListResponse> => {
  const res = await api.get<ProductionListResponse>('/productions/', {
    params: buildListParams(options),
  })
  return res.data
}
