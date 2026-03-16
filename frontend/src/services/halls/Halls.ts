import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetHallsOptions } from './HallOptions'
import type { Hall, HallListResponse } from '../../types/Halls'

/**
 * Retrieve a single hall by its numeric ID.
 *
 * This sends a `GET /halls/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the hall that should be fetched.
 * @returns A promise that resolves to the hall data returned by the API.
 */
export const getHall = async (id: number): Promise<Hall> => {
  const res = await api.get<Hall>(`/halls/${id}/`)
  return res.data
}

/**
 * Retrieve a list of halls with optional pagination and filtering.
 *
 * Supported filter fields currently include:
 * - `space`: filter by parent space ID
 * - `location`: filter by parent location ID (via space)
 * - `seat_selection`: filter by seat selection flag
 * - `open_seating`: filter by open seating flag
 * - `name`: filter by translated hall name
 *
 * Shared list filters are also supported: `search`, `ordering`, `external_id`.
 *
 * @param options Optional settings for pagination and filtering.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 */
export const getHalls = async (options?: GetHallsOptions): Promise<HallListResponse> => {
  const res = await api.get<HallListResponse>('/halls/', { params: buildListParams(options) })
  return res.data
}
