import type { Blog, BlogListResponse } from '../../types/Blogs'
import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetBlogsOptions } from './BlogOptions'

/**
 * Retrieve a single blog by its numeric ID.
 *
 * Sends a `GET /blogs/:id/` request and returns the response payload
 * exactly as received.
 *
 * @param id The unique ID of the blog to fetch.
 * @returns A promise that resolves to the blog data returned by the API.
 *
 * @example
 * const blog = await getBlog(12);
 *
 * @throws {ApiError} When the request fails.
 */
export const getBlog = async (id: number): Promise<Blog> => {
  const res = await api.get<Blog>(`/blogs/${id}/`)
  return res.data
}

/**
 * Retrieve a list of blogs with optional pagination and filtering.
 *
 * Sends a `GET /blogs/` request. The `options` object is translated into
 * query parameters by `buildListParams` (see `ApiParams`). Supported blog-
 * specific filters include fields defined in `BlogOptions` such as
 * `production`, `published`, `slug` and `title`. In addition, shared list
 * filters like `search`, `ordering` and `external_id` are supported.
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data (paginated list).
 *
 * @example
 * const blogs = await getBlogs();
 *
 * @example
 * const blogs = await getBlogs({
 *   page: 1,
 *   pageSize: 20,
 *   filters: { published: true, ordering: 'id' },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getBlogs = async (options?: GetBlogsOptions): Promise<BlogListResponse> => {
  const res = await api.get<BlogListResponse>('/blogs/', {
    params: buildListParams(options),
  })
  return res.data
}
