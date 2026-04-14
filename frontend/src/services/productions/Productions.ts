import { api } from '../Api'
import { buildListParams } from '../ApiParams'

import type { GetProductionsOptions } from './ProductionOptions'
import type { Production, ProductionListResponse } from '../../types/Productions'

/**
 * Retrieve a single production by its numeric ID, optionally including events.
 *
 * This sends a `GET /productions/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the production that should be fetched.
 * @param include Optional includes, e.g. `['events']` to include related events in the response.
 * @returns A promise that resolves to the production data returned by the API.
 *
 * @example
 * const production = await getProduction(12);
 * const productionWithEvents = await getProduction(12, ['events']);
 *
 * @throws {ApiError} When the request fails.
 */
export const getProduction = async (id: number, include?: string[]): Promise<Production> => {
  const params: Record<string, string> = {}

  if (include) {
    params.include = include.join(',')
  }

  const res = await api.get<Production>(`/productions/${id}/`, { params })
  return res.data
}

/**
 * Retrieve a list of productions with optional pagination and filtering.
 *
 * This sends a `GET /productions/` request. The `options` object is translated
 * into query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported production-specific filter fields currently include:
 * - `attendance_mode`: filter by attendance mode (`offline` or `online`)
 * - `performer_type`: filter by performer type (`group` or `solo`)
 * - `uit_database_theme`: filter by UIT Database theme ID
 * - `uit_database_type`: filter by UIT Database type ID
 * - `genre`: filter by attached genre ID
 * - `tag`: filter by attached tag ID
 * - `has_media`: filter by whether a media gallery is assigned
 * - `title`: filter by translated production title
 * - `artist_name`: filter by translated artist or company name
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `id` or `-id`
 * - `external_id`: external identifier, for example `/api/v1/productions/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const productions = await getProductions();
 *
 * @example
 * const productions = await getProductions({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     attendance_mode: "offline",
 *     performer_type: "group",
 *     ordering: "-id",
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getProductions = async (
  options?: GetProductionsOptions,
): Promise<ProductionListResponse> => {
  const res = await api.get<ProductionListResponse>('/productions/', {
    params: buildListParams(options),
  })
  return res.data
}
