import { api } from '../Api'
import { buildListParams } from '../ApiParams'

import type { GetMediaGalleriesOptions, GetMediaItemsOptions } from './MediaOptions'
import type {
  MediaGallery,
  MediaGalleryListResponse,
  MediaItem,
  MediaItemListResponse,
} from '../../types/Media'

/**
 * Retrieve a list of media galleries with optional pagination and filtering.
 *
 * This sends a `GET /media-galleries/` request. The `options` object is
 * translated into query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported gallery-specific filter fields currently include:
 * - `name`: filter by gallery name (contains)
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `name` or `-name`
 * - `external_id`: external identifier, for example `api/v1/media-galleries/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const galleries = await getMediaGalleries();
 *
 * @example
 * const galleries = await getMediaGalleries({
 *   page: 1,
 *   pageSize: 10,
 *   filters: {
 *     name: "season",
 *     ordering: "name",
 *   },
 * });
 *
 * @throws Propagates the original request error.
 */
export const getMediaGalleries = async (
  options?: GetMediaGalleriesOptions,
): Promise<MediaGalleryListResponse> => {
  const response = await api.get<MediaGalleryListResponse>('/media-galleries/', {
    params: buildListParams(options),
  })
  return response.data
}

/**
 * Retrieve a single media gallery by its numeric ID.
 *
 * This sends a `GET /media-galleries/:id/` request to the backend and returns
 * the response payload exactly as received.
 *
 * @param id The unique ID of the media gallery that should be fetched.
 * @returns A promise that resolves to the media gallery data returned by the API.
 *
 * @example
 * const gallery = await getMediaGallery(12);
 *
 * @throws Propagates the original request error.
 */
export const getMediaGallery = async (id: number): Promise<MediaGallery> => {
  const response = await api.get<MediaGallery>(`/media-galleries/${id}/`)
  return response.data
}

/**
 * Retrieve a list of media items with optional pagination and filtering.
 *
 * This sends a `GET /media-items/` request. The `options` object is translated
 * into query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported media-item-specific filter fields currently include:
 * - `gallery`: filter by parent gallery ID
 * - `type`: filter by media type (`foto`, `video`, `audio`, or `other`)
 * - `file_format`: filter by file format or extension (contains)
 * - `original_filename`: filter by original filename (contains)
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `position` or `-type`
 * - `external_id`: external identifier, for example `api/v1/media-items/123`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const items = await getMediaItems();
 *
 * @example
 * const items = await getMediaItems({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     gallery: 5,
 *     type: "foto",
 *     ordering: "position",
 *   },
 * });
 *
 * @throws Propagates the original request error.
 */
export const getMediaItems = async (
  options?: GetMediaItemsOptions,
): Promise<MediaItemListResponse> => {
  const response = await api.get<MediaItemListResponse>('/media-items/', {
    params: buildListParams(options),
  })
  return response.data
}

/**
 * Retrieve a single media item by its numeric ID.
 *
 * This sends a `GET /media-items/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the media item that should be fetched.
 * @returns A promise that resolves to the media item data returned by the API.
 *
 * @example
 * const item = await getMediaItem(12);
 *
 * @throws Propagates the original request error.
 */
export const getMediaItem = async (id: number): Promise<MediaItem> => {
  const response = await api.get<MediaItem>(`/media-items/${id}/`)
  return response.data
}
