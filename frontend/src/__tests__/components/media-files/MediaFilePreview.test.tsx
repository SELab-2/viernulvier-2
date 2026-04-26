import '@testing-library/jest-dom/jest-globals'
import { describe, expect, it, jest } from '@jest/globals'
import { render, screen } from '@testing-library/react'

import type { ReactNode } from 'react'

jest.mock('react-pdf', () => ({
  Document: ({ children }: { children: ReactNode }) => <div data-testid="pdf-doc">{children}</div>,
  Page: () => <div data-testid="pdf-page" />,
  pdfjs: {
    GlobalWorkerOptions: { workerSrc: '' },
    version: '5.4.296',
  },
}))

// Mock icons
jest.mock('@mui/icons-material/DescriptionOutlined', () => ({
  __esModule: true,
  default: () => <svg data-testid="description-icon" />,
}))
jest.mock('@mui/icons-material/InsertDriveFileOutlined', () => ({
  __esModule: true,
  default: () => <svg data-testid="file-icon" />,
}))
jest.mock('@mui/icons-material/PictureAsPdfOutlined', () => ({
  __esModule: true,
  default: () => <svg data-testid="pdf-icon" />,
}))

import MediaFilePreview from '../../../components/media-files/MediaFilePreview'

describe('MediaFilePreview', () => {
  it('renders an image preview for image files', () => {
    render(
      <MediaFilePreview
        mediaFile={
          {
            file_type: 'image',
            file: 'https://example.com/image.jpg',
            filename: 'summer.jpg',
          } as never
        }
        previewLabel="Afbeelding"
      />,
    )

    const image = screen.getByRole('img', { name: 'summer.jpg' })
    expect(image).toHaveAttribute('src', 'https://example.com/image.jpg')
  })

  it('renders pdf preview (first page)', () => {
    render(
      <MediaFilePreview
        mediaFile={
          {
            file_type: 'pdf',
            file: 'https://example.com/file.pdf',
            filename: 'manual.pdf',
          } as never
        }
        previewLabel="PDF"
      />,
    )

    expect(screen.getByTestId('pdf-doc')).toBeInTheDocument()
    expect(screen.getByTestId('pdf-page')).toBeInTheDocument()
  })

  it('renders the generic file icon for other files', () => {
    render(
      <MediaFilePreview
        mediaFile={{ file_type: 'other', filename: 'archive.zip' } as never}
        previewLabel="Bestand"
      />,
    )

    expect(screen.getByTestId('file-icon')).toBeInTheDocument()
    expect(screen.getByText('Bestand')).toBeInTheDocument()
  })

  it('renders the document icon for non-image non-pdf typed files', () => {
    render(
      <MediaFilePreview
        mediaFile={{ file_type: 'document', filename: 'notes.docx' } as never}
        previewLabel="Document"
      />,
    )

    expect(screen.getByTestId('description-icon')).toBeInTheDocument()
    expect(screen.getByText('Document')).toBeInTheDocument()
  })
})
