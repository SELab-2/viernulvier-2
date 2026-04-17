import { api } from '../Api'
import { buildListParams } from '../ApiParams'

import type { GetTagsOptions } from './TagOptions'
import type { TagListResponse, Tag } from '../../types/Tags'

/**
 * Retrieve a single tag by its numeric ID.
 *
 * This sends a `GET /tags/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the tag that should be fetched.
 * @returns A promise that resolves to the tag data returned by the API.
 *
 * @example
 * const tag = await getTag(12);
 *
 * @throws {ApiError} When the request fails.
 */
export const getTag = async (id: number): Promise<Tag> => {
  const res = await api.get<Tag>(`/tags/${id}/`)
  return res.data
}

/**
 * Retrieve a list of tags with optional pagination and filtering.
 *
 * This sends a `GET /tags/` request. The `options` object is translated
 * into query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported tag-specific filter fields currently include:
 * - `type`: filter by tag type/category
 * - `source`: filter by originating system
 * - `is_enabled`: filter by enabled/disabled tags
 * - `name`: filter by translated tag name
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `id` or `-id`
 * - `external_id`: external identifier, for example `/api/v1/tags/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const tags = await getTags();
 *
 * @example
 * const tags = await getTags({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     type: "theme",
 *     is_enabled: true,
 *     ordering: "-id",
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getTags = async (options?: GetTagsOptions): Promise<TagListResponse> => {
  const res = await api.get<TagListResponse>('/tags/', {
    params: buildListParams(options),
  })
  return res.data
}
