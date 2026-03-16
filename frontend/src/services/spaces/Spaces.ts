import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetSpacesOptions } from './SpaceOptions'
import type { Space, SpaceListResponse } from '../../types/Spaces'

/**
 * Retrieve a single space by its numeric ID.
 *
 * This sends a `GET /spaces/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the space that should be fetched.
 * @returns A promise that resolves to the space data returned by the API.
 */
export const getSpace = async (id: number): Promise<Space> => {
  const res = await api.get<Space>(`/spaces/${id}/`)
  return res.data
}

/**
 * Retrieve a list of spaces with optional pagination and filtering.
 *
 * Supported filter fields currently include:
 * - `location`: filter by parent location ID
 * - `name`: filter by translated space name
 *
 * Shared list filters are also supported: `search`, `ordering`, `external_id`.
 *
 * @param options Optional settings for pagination and filtering.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 */
export const getSpaces = async (options?: GetSpacesOptions): Promise<SpaceListResponse> => {
  const res = await api.get<SpaceListResponse>('/spaces/', { params: buildListParams(options) })
  return res.data
}
