import { api } from '../Api'
import { buildListParams } from '../ApiParams'

import type { GetMediaFilesOptions } from './MediaFileOptions'
import type { MediaFile, MediaFileListResponse } from '../../types/MediaFiles'

/**
 * Retrieve a single media file by its UUID.
 *
 * This sends a `GET /media/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique UUID of the media file that should be fetched.
 * @returns A promise that resolves to the media file data returned by the API.
 *
 * @example
 * const mediaFile = await getMediaFile('4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3');
 *
 * @throws {ApiError} When the request fails.
 */
export const getMediaFile = async (id: string): Promise<MediaFile> => {
  const res = await api.get<MediaFile>(`/media/${id}/`)
  return res.data
}

/**
 * Retrieve a list of media files with optional pagination and filtering.
 *
 * This sends a `GET /media/` request. The `options` object is translated into
 * query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported filter fields currently include:
 * - `file_type`: filter by normalized file type
 * - `mime_type`: filter by stored MIME type
 * - `filename`: filter by uploaded filename
 * - `uploaded_by`: filter by uploader username
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `created_at` or `-created_at`
 * - `external_id`: external identifier
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const mediaFiles = await getMediaFiles();
 *
 * @example
 * const mediaFiles = await getMediaFiles({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     file_type: 'image',
 *     filename: 'poster',
 *     ordering: '-created_at',
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getMediaFiles = async (
  options?: GetMediaFilesOptions,
): Promise<MediaFileListResponse> => {
  const res = await api.get<MediaFileListResponse>('/media/', {
    params: buildListParams(options),
  })
  return res.data
}
