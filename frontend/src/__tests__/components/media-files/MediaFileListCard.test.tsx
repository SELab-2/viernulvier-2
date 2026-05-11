import { describe, expect, it, jest, beforeEach } from '@jest/globals'
import { render, screen } from '@testing-library/react'

const formatMediaFileDateMock = jest.fn()
const formatMediaFileSizeMock = jest.fn()
const getMediaFileDescriptionMock = jest.fn()
const getMediaFileTypeLabelMock = jest.fn()

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

jest.mock('../../../features/media-files/components/MediaFilePreview', () => ({
  __esModule: true,
  default: ({ previewLabel }: { previewLabel: string }) => (
    <div data-testid="media-preview">preview:{previewLabel}</div>
  ),
}))

jest.mock('../../../features/media-files/components/MediaFileUtils', () => ({
  formatMediaFileDate: (...args: unknown[]) => formatMediaFileDateMock(...args),
  formatMediaFileSize: (...args: unknown[]) => formatMediaFileSizeMock(...args),
  getMediaFileDescription: (...args: unknown[]) => getMediaFileDescriptionMock(...args),
  getMediaFileTypeLabel: (...args: unknown[]) => getMediaFileTypeLabelMock(...args),
}))

import MediaFileListCard from '../../../features/media-files/components/MediaFileListCard'

describe('MediaFileListCard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    formatMediaFileDateMock.mockReturnValue('23 apr 2026')
    formatMediaFileSizeMock.mockReturnValue('1.5 MB')
    getMediaFileDescriptionMock.mockReturnValue('Lange beschrijving')
    getMediaFileTypeLabelMock.mockReturnValue('Afbeelding')
  })

  it('renders filename, description, preview and metadata', () => {
    render(
      <MediaFileListCard
        mediaFile={
          {
            filename: 'photo.jpg',
            file: 'https://example.com/photo.jpg',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: 1572864,
            file_type: 'image',
          } as never
        }
      />,
    )

    expect(screen.getByRole('heading', { name: 'photo.jpg' })).toBeInTheDocument()
    expect(screen.getByText('Lange beschrijving')).toBeInTheDocument()
    expect(screen.getByText('23 apr 2026')).toBeInTheDocument()
    expect(screen.getByText('t:media.size: 1.5 MB')).toBeInTheDocument()
    expect(screen.getByTestId('media-preview')).toHaveTextContent('preview:Afbeelding')

    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', 'https://example.com/photo.jpg')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('falls back to the file type label when no description is available', () => {
    getMediaFileDescriptionMock.mockReturnValueOnce('')

    render(
      <MediaFileListCard
        mediaFile={
          {
            filename: 'photo.jpg',
            file: 'https://example.com/photo.jpg',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: 1572864,
            file_type: 'image',
          } as never
        }
      />,
    )

    expect(screen.getByText('Afbeelding')).toBeInTheDocument()
  })

  it('hides the size label when no formatted size is available', () => {
    formatMediaFileSizeMock.mockReturnValueOnce(null)

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

    expect(screen.queryByText(/t:media.size/)).not.toBeInTheDocument()
  })
})
