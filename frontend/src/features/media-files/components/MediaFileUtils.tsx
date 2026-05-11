import { getLocalizedValue } from '../../../utils/localization'

import type { MediaFile } from '../../../types/MediaFiles'
import type { TFunction } from 'i18next'

export const formatMediaFileDate = (value: string, locale: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export const formatMediaFileSize = (value: number | null): string | null => {
  if (value === null || value <= 0) {
    return null
  }

  if (value < 1024) {
    return `${value} B`
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

export const getMediaFileTypeLabel = (mediaFile: MediaFile, t: TFunction): string => {
  return t(`media.fileType.${mediaFile.file_type}`)
}

export const getMediaFileDescription = (
  mediaFile: MediaFile,
  language: string,
  t: (key: string) => string,
) => {
  const localized = getLocalizedValue(mediaFile.description, language)

  if (localized) {
    return localized
  }

  if (mediaFile.display_description) {
    return mediaFile.display_description
  }

  return t('media.noDescription')
}
