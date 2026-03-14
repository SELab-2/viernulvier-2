import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetGenresOptions } from './GenreTypes'

/**
 * Retrieve a single genre by its numeric ID.
 *
 * This sends a `GET /genres/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the genre that should be fetched.
 * @returns A promise that resolves to the genre data returned by the API.
 *
 * @example
 * const genre = await getGenre(12);
 *
 * @throws Rethrows the original request error after logging it.
 */

export const getGenre = async (id: number) => {
  const res = await api.get(`/genres/${id}/`)
  return res.data
}

/**
 * Retrieve a list of genres with optional pagination and filtering.
 *
 * This sends a `GET /genres/` request. The `options` object is translated into
 * query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported filter fields currently include:
 * - `use_as`: filter by usage context ID
 * - `type`: filter by internal genre type
 * - `vendor_id`: filter by upstream vendor ID
 * - `name`: filter by translated genre name
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `name` or `-name`
 * - `external_id`: external identifier, for example `api/v1/genres/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const genres = await getGenres();
 *
 * @example
 * const genres = await getGenres({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     type: "theater",
 *     name: "festival",
 *     ordering: "use_as",
 *   },
 * });
 *
 * @throws Rethrows the original request error after logging it.
 */
export const getGenres = async (options?: GetGenresOptions) => {
  const res = await api.get('/genres/', { params: buildListParams(options) })
  return res.data
}
