import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type {
  MediaGallery,
  MediaGalleryListResponse,
  MediaItem,
  MediaItemListResponse,
} from '../../types/Media'
import type { GetMediaGalleriesOptions, GetMediaItemsOptions } from './MediaOptions'

export const getMediaGalleries = async (
  options?: GetMediaGalleriesOptions,
): Promise<MediaGalleryListResponse> => {
  const response = await api.get<MediaGalleryListResponse>('/media-galleries/', {
    params: buildListParams(options),
  })
  return response.data
}

export const getMediaGallery = async (id: number): Promise<MediaGallery> => {
  const response = await api.get<MediaGallery>(`/media-galleries/${id}/`)
  return response.data
}

export const getMediaItems = async (
  options?: GetMediaItemsOptions,
): Promise<MediaItemListResponse> => {
  const response = await api.get<MediaItemListResponse>('/media-items/', {
    params: buildListParams(options),
  })
  return response.data
}

export const getMediaItem = async (id: number): Promise<MediaItem> => {
  const response = await api.get<MediaItem>(`/media-items/${id}/`)
  return response.data
}
