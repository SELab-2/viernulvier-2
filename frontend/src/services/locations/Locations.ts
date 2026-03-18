import type { Location, LocationListResponse } from '../../types/Locations'
import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetLocationsOptions } from './LocationOptions'

/**
 * Retrieve a single location by its numeric ID.
 *
 * This sends a `GET /locations/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the location that should be fetched.
 * @returns A promise that resolves to the location data returned by the API.
 *
 * @example
 * const location = await getLocation(12);
 *
 * @throws {ApiError} When the request fails.
 */
export const getLocation = async (id: number): Promise<Location> => {
  const res = await api.get<Location>(`/locations/${id}/`)
  return res.data
}

/**
 * Retrieve a list of locations with optional pagination and filtering.
 *
 * This sends a `GET /locations/` request. The `options` object is translated into
 * query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported filter fields currently include:
 * - `city`: filter by city name (contains)
 * - `country`: filter by country code
 * - `postal_code`: filter by exact postal code
 * - `is_own_location`: filter by ownership flag
 * - `name`: filter by translated location name
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `city` or `-country`
 * - `external_id`: external identifier, for example `api/v1/locations/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const locations = await getLocations();
 *
 * @example
 * const locations = await getLocations({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     city: "Ghent",
 *     country: "BE",
 *     ordering: "city",
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getLocations = async (
  options?: GetLocationsOptions,
): Promise<LocationListResponse> => {
  const res = await api.get<LocationListResponse>('/locations/', {
    params: buildListParams(options),
  })
  return res.data
}
