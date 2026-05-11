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
    card: { borderRadius: 2 },
    spacing: { numericSm: 1, numericLg: 2 },
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

import MediaFileGridCard from '../../../features/media-files/components/MediaFileGridCard'

describe('MediaFileGridCard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    formatMediaFileDateMock.mockReturnValue('23 apr 2026')
    formatMediaFileSizeMock.mockReturnValue('2.0 MB')
    getMediaFileDescriptionMock.mockReturnValue('Korte beschrijving')
    getMediaFileTypeLabelMock.mockReturnValue('PDF')
  })

  it('renders the main metadata, preview and file link', () => {
    render(
      <MediaFileGridCard
        mediaFile={
          {
            filename: 'brochure.pdf',
            file: 'https://example.com/brochure.pdf',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: 2 * 1024 * 1024,
            file_type: 'pdf',
          } as never
        }
      />,
    )

    expect(screen.getByRole('heading', { name: 'brochure.pdf' })).toBeInTheDocument()
    expect(screen.getByText('Korte beschrijving')).toBeInTheDocument()
    expect(screen.getByText('23 apr 2026')).toBeInTheDocument()
    expect(screen.getByText('t:media.size: 2.0 MB')).toBeInTheDocument()
    expect(screen.getByTestId('media-preview')).toHaveTextContent('preview:PDF')

    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', 'https://example.com/brochure.pdf')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('falls back to the file type label when the description is empty', () => {
    getMediaFileDescriptionMock.mockReturnValueOnce('')

    render(
      <MediaFileGridCard
        mediaFile={
          {
            filename: 'brochure.pdf',
            file: 'https://example.com/brochure.pdf',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: 2 * 1024 * 1024,
            file_type: 'pdf',
          } as never
        }
      />,
    )

    expect(screen.getByText('PDF')).toBeInTheDocument()
  })

  it('hides the file size when no formatted size is available', () => {
    formatMediaFileSizeMock.mockReturnValueOnce(null)

    render(
      <MediaFileGridCard
        mediaFile={
          {
            filename: 'brochure.pdf',
            file: 'https://example.com/brochure.pdf',
            created_at: '2026-04-23T10:00:00Z',
            size_bytes: null,
            file_type: 'pdf',
          } as never
        }
      />,
    )

    expect(screen.queryByText(/t:media.size/)).not.toBeInTheDocument()
  })
})
