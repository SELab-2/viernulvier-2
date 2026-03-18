import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/media-galleries/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface MediaGalleryFilters {
  /** Case-insensitive substring match on the gallery name. */
  name?: string
}

/**
 * Endpoint-specific filter fields for the `/media-items/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface MediaItemFilters {
  /** Exact match on the parent gallery ID. */
  gallery?: number
  /** Exact match on media type: `foto`, `video`, `audio`, or `other`. */
  type?: 'foto' | 'video' | 'audio' | 'other'
  /** Case-insensitive substring match on the file format / extension. */
  file_format?: string
  /** Case-insensitive substring match on the original filename. */
  original_filename?: string
}

/**
 * Options accepted by {@link getMediaGalleries}.
 *
 * Combines pagination (`page`, `pageSize`), gallery-specific filters
 * ({@link MediaGalleryFilters}), and shared list filters (`search`,
 * `ordering`, `external_id`).
 */
export type GetMediaGalleriesOptions = FilteredListOptions<MediaGalleryFilters>

/**
 * Options accepted by {@link getMediaItems}.
 *
 * Combines pagination (`page`, `pageSize`), media-item-specific filters
 * ({@link MediaItemFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetMediaItemsOptions = FilteredListOptions<MediaItemFilters>
