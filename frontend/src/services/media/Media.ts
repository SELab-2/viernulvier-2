import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import {
    MediaGallery,
    MediaGalleryListResponse,
    MediaItem,
    MediaItemListResponse,
} from '../../types/Media'
import type { GetMediaGalleriesOptions, GetMediaItemsOptions } from './MediaOptions'

export async function getMediaGalleries(
    options?: GetMediaGalleriesOptions,
): Promise<MediaGalleryListResponse> {
    const response = await api.get<MediaGalleryListResponse>('/media-galleries/', {
        params: buildListParams(options),
    })
    return response.data
}

export async function getMediaGallery(id: number): Promise<MediaGallery> {
    const response = await api.get<MediaGallery>(`/media-galleries/${id}/`)
    return response.data
}

export async function getMediaItems(
    options?: GetMediaItemsOptions,
): Promise<MediaItemListResponse> {
    const response = await api.get<MediaItemListResponse>('/media-items/', {
        params: buildListParams(options),
    })
    return response.data
}

export async function getMediaItem(id: number): Promise<MediaItem> {
    const response = await api.get<MediaItem>(`/media-items/${id}/`)
    return response.data
}
