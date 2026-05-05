import { describe, expect, it, jest } from '@jest/globals'

import {
  formatMediaFileDate,
  formatMediaFileSize,
  getMediaFileDescription,
  getMediaFileTypeLabel,
} from '../../../components/media-files/MediaFileUtils'

import type { TFunction } from 'i18next'
import type { MediaFile } from '../../../types/MediaFiles'

const baseMediaFile = (overrides: Partial<MediaFile> = {}): MediaFile => ({
  id: '1',
  external_id: null,
  file: 'https://example.com/file.pdf',
  filename: 'file.pdf',
  display_description: null,
  description: {},
  mime_type: 'application/pdf',
  size_bytes: 1024,
  file_type: 'pdf',
  created_at: '2026-04-23T10:00:00Z',
  ...overrides,
})

describe('MediaFileUtils', () => {
  describe('formatMediaFileDate', () => {
    it('formats valid dates for the requested locale', () => {
      expect(formatMediaFileDate('2026-04-23T10:00:00Z', 'en-US')).toBe('Apr 23, 2026')
    })

    it('returns the original value for invalid dates', () => {
      expect(formatMediaFileDate('not-a-date', 'en-US')).toBe('not-a-date')
    })
  })

  describe('formatMediaFileSize', () => {
    it('returns null for missing or non-positive sizes', () => {
      expect(formatMediaFileSize(null)).toBeNull()
      expect(formatMediaFileSize(0)).toBeNull()
      expect(formatMediaFileSize(-12)).toBeNull()
    })

    it('formats byte, kilobyte and megabyte values', () => {
      expect(formatMediaFileSize(512)).toBe('512 B')
      expect(formatMediaFileSize(1536)).toBe('1.5 KB')
      expect(formatMediaFileSize(1_572_864)).toBe('1.5 MB')
    })
  })

  it('translates the file type label', () => {
    const t = jest.fn((key: string) => `translated:${key}`) as unknown as TFunction

    expect(getMediaFileTypeLabel(baseMediaFile({ file_type: 'image' }), t)).toBe(
      'translated:media.fileType.image',
    )
    expect(t).toHaveBeenCalledWith('media.fileType.image')
  })

  describe('getMediaFileDescription', () => {
    it('returns the localized description when available', () => {
      const mediaFile = baseMediaFile({
        description: { nl: 'Nederlandse beschrijving', en: 'English description' },
        display_description: 'Display description',
      })

      expect(getMediaFileDescription(mediaFile, 'en', (key) => key)).toBe('English description')
    })

    it('falls back to the first localized description', () => {
      const mediaFile = baseMediaFile({
        description: { nl: 'Nederlandse beschrijving' },
        display_description: 'Display description',
      })

      expect(getMediaFileDescription(mediaFile, 'fr', (key) => key)).toBe(
        'Nederlandse beschrijving',
      )
    })

    it('uses the display description before the no-description translation', () => {
      const mediaFile = baseMediaFile({ display_description: 'Display description' })

      expect(getMediaFileDescription(mediaFile, 'nl', (key) => `t:${key}`)).toBe(
        'Display description',
      )
    })

    it('returns the no-description translation when no description is available', () => {
      expect(getMediaFileDescription(baseMediaFile(), 'nl', (key) => `t:${key}`)).toBe(
        't:media.noDescription',
      )
    })
  })
})
