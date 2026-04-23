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
    card: { borderRadius: 2 },
    spacing: { numericSm: 1, numericLg: 2 },
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
  formatMediaFileSize: jest.fn(() => '2.0 MB'),
  getMediaFileDescription: jest.fn(() => 'Korte beschrijving'),
  getMediaFileTypeLabel: jest.fn(() => 'PDF'),
}))

import MediaFileGridCard from '../../../components/media-files/MediaFileGridCard'

describe('MediaFileGridCard', () => {
  it('renders the main metadata and file link', () => {
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
    expect(screen.getByTestId('media-preview')).toHaveTextContent('PDF')

    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', 'https://example.com/brochure.pdf')
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('falls back to the file type label when the description is empty', async () => {
    const utils = await import('../../../components/media-files/MediaFileUtils')
    ;(utils.getMediaFileDescription as jest.Mock).mockReturnValueOnce(null)

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
})
