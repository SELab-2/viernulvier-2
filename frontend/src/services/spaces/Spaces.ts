import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetSpacesOptions } from './SpaceOptions'
import type { Hall } from '../../types/Halls'
import type { Space, SpaceListResponse } from '../../types/Spaces'
import type { HallInSpaceResponse, SpaceResponse } from './SpaceOptions'

/**
 * Normalize a hall nested under `/spaces/` responses.
 *
 * The backend omits `hall.space` in this nested context to avoid recursive
 * payloads. The frontend uses one uniform `Hall` type, so we fill `space`
 * with `null` here.
 */
const mapHallInSpace = (hall: HallInSpaceResponse): Hall => ({
  ...hall,
  space: null,
})

/**
 * Normalize a single space response to the frontend domain shape.
 *
 * This keeps consumers simple: they can always rely on `Space.halls` being a
 * `Hall[]` with a defined `space` field (`null` for nested hall rows).
 */
const mapSpaceResponse = (space: SpaceResponse): Space => ({
  ...space,
  halls: space.halls.map(mapHallInSpace),
})

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
  const res = await api.get<SpaceResponse>(`/spaces/${id}/`)
  return mapSpaceResponse(res.data)
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
  const res = await api.get<Omit<SpaceListResponse, 'results'> & { results: SpaceResponse[] }>('/spaces/', {
    params: buildListParams(options),
  })

  return {
    ...res.data,
    results: res.data.results.map(mapSpaceResponse),
  }
}
