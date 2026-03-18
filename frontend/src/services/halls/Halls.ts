import type { Hall, HallListResponse } from '../../types/Halls'
import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetHallsOptions } from './HallOptions'

/**
 * Retrieve a single hall by its numeric ID.
 *
 * This sends a `GET /halls/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the hall that should be fetched.
 * @returns A promise that resolves to the hall data returned by the API.
 *
 * @example
 * const hall = await getHall(12);
 *
 * @throws {ApiError} When the request fails.
 */
export const getHall = async (id: number): Promise<Hall> => {
  const res = await api.get<Hall>(`/halls/${id}/`)
  return res.data
}

/**
 * Retrieve a list of halls with optional pagination and filtering.
 *
 * This sends a `GET /halls/` request. The `options` object is translated into
 * query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported filter fields currently include:
 * - `space`: filter by parent space ID
 * - `location`: filter by parent location ID (via space)
 * - `seat_selection`: filter by seat selection flag
 * - `open_seating`: filter by open seating flag
 * - `name`: filter by translated hall name
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `name` or `-name`
 * - `external_id`: external identifier, for example `api/v1/halls/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const halls = await getHalls();
 *
 * @example
 * const halls = await getHalls({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     location: 3,
 *     open_seating: true,
 *     ordering: 'name',
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getHalls = async (options?: GetHallsOptions): Promise<HallListResponse> => {
  const res = await api.get<HallListResponse>('/halls/', { params: buildListParams(options) })
  return res.data
}
