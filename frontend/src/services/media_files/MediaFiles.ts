import { api } from '../Api'
import { buildListParams } from '../ApiParams'

import type { GetMediaFilesOptions } from './MediaFileOptions'
import type { MediaFile, MediaFileListResponse } from '../../types/MediaFiles'

/**
 * Retrieve a list of media files with optional pagination and filtering.
 *
 * This sends a `GET /media-files/` request. The `options` object is translated
 * into query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported media-file-specific filter fields currently include:
 * - `file_type`: exact match on normalized file type (`image`, `pdf`, `other`)
 * - `mime_type`: exact match on MIME type
 * - `filename`: case-insensitive substring match on the uploaded filename
 * - `description`: case-insensitive substring match across translated descriptions
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `created_at` or `-size_bytes`
 * - `external_id`: external identifier
 */
export const getMediaFiles = async (
  options?: GetMediaFilesOptions,
): Promise<MediaFileListResponse> => {
  const response = await api.get<MediaFileListResponse>('/media-files/', {
    params: buildListParams(options),
  })
  return response.data
}

/**
 * Retrieve a single media file by UUID.
 */
export const getMediaFile = async (id: string): Promise<MediaFile> => {
  const response = await api.get<MediaFile>(`/media-files/${id}/`)
  return response.data
}
