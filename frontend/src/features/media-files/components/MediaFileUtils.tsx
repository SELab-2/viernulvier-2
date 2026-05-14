import { getLocalizedValue } from '../../../utils/localization'

import type { MediaFile } from '../../../types/MediaFiles'
import type { TFunction } from 'i18next'

/**
 * Formats a raw ISO date string into a localized human-readable date.
 * Falls back to the original value if the date cannot be parsed.
 */
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

/**
 * Converts a file size in bytes into a human-readable string.
 * Returns KB or MB depending on size, or null for invalid values.
 */
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

/**
 * Returns a localized label for a media file type using i18n keys.
 */
export const getMediaFileTypeLabel = (mediaFile: MediaFile, t: TFunction): string => {
  return t(`media.fileType.${mediaFile.file_type}`)
}

/**
 * Resolves the best available description for a media file.
 *
 * Priority:
 * 1. Localized value from `description`
 * 2. Fallback `display_description`
 * 3. Translation fallback key
 */
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
