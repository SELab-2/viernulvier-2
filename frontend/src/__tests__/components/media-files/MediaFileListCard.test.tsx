import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, jest } from '@jest/globals'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'nl' },
    t: (key: string) => `t:${key}`,
  }),
}))

jest.mock('../../../theme/styles', () => ({
  createCommonStyles: () => ({
    cardBase: { boxShadow: 'none' },
  }),
}))

jest.mock('../../../theme/tokens', () => ({
  tokens: {
    borderRadius: { sm: 2 },
    spacing: { numericMd: 1, numericSm: 1, numericLg: 2 },
  },
}))

jest.mock('../../../components/media-files/MediaFilePreview', () => ({
  __esModule: true,
  default: ({ previewLabel }: { previewLabel: string }) => (
    <div data-testid="media-preview">preview:{previewLabel}</div>
  ),
}))

jest.mock('../../../components/media-files/MediaFileUtils', () => ({
  formatMediaFileDate: jest.fn(() => '23 apr 2026'),
  formatMediaFileSize: jest.fn(() => null),
  getMediaFileDescription: jest.fn(() => 'Lange beschrijving'),
  getMediaFileTypeLabel: jest.fn(() => 'Afbeelding'),
}))

import MediaFileListCard from '../../../components/media-files/MediaFileListCard'

describe('MediaFileListCard', () => {
  it('renders filename, description and preview', () => {
    render(
      <MediaFileListCard
        mediaFile={
          {
            filename: 'photo.jpg',
            file: 'https://example.com/photo.jpg',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: null,
            file_type: 'image',
          } as never
        }
      />,
    )

    expect(screen.getByRole('heading', { name: 'photo.jpg' })).toBeInTheDocument()
    expect(screen.getByText('Lange beschrijving')).toBeInTheDocument()
    expect(screen.getByText('23 apr 2026')).toBeInTheDocument()
    expect(screen.getByTestId('media-preview')).toHaveTextContent('Afbeelding')
    expect(screen.queryByText(/t:media.size/)).not.toBeInTheDocument()
  })

  it('falls back to the file type label when no description is available', async () => {
    const utils = await import('../../../components/media-files/MediaFileUtils')
    ;(utils.getMediaFileDescription as jest.Mock).mockReturnValueOnce(null)

    render(
      <MediaFileListCard
        mediaFile={
          {
            filename: 'photo.jpg',
            file: 'https://example.com/photo.jpg',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: null,
            file_type: 'image',
          } as never
        }
      />,
    )

    expect(screen.getByText('Afbeelding')).toBeInTheDocument()
  })
})
