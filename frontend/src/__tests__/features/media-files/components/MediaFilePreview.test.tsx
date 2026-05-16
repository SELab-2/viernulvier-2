import { describe, expect, it, jest } from '@jest/globals'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'

const useMediaQueryMock = jest.fn()

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material') as Record<string, unknown>
  return {
    ...actual,
    useTheme: () => ({
      breakpoints: {
        down: jest.fn(() => 'mocked-breakpoint'),
      },
    }),
    useMediaQuery: () => useMediaQueryMock(),
    // Render Modal children directly (no portal) so they are part of the
    // normal React tree and queryable with screen.*
    Modal: ({
      open,
      children,
      onClose,
    }: {
      open: boolean
      children: React.ReactNode
      onClose?: () => void
    }) =>
      open ? (
        <div data-testid="modal" onClick={() => onClose?.()}>
          {children}
        </div>
      ) : null,
  }
})

jest.mock('../../../components/media-files/MediaFileGrid', () => ({
  __esModule: true,
  default: ({
    mediaFiles,
    onOpenMediaFile,
  }: {
    mediaFiles: Array<{ id: number; filename: string }>
    onOpenMediaFile: (f: { id: number; filename: string }) => void
  }) => (
    <div data-testid="grid-view">
      {mediaFiles.map((f) => (
        <button key={f.id} onClick={() => onOpenMediaFile(f)}>
          {f.filename}
        </button>
      ))}
      grid:{mediaFiles.length}
    </div>
  ),
}))

jest.mock('../../../components/media-files/MediaFileList', () => ({
  __esModule: true,
  default: ({
    mediaFiles,
    onOpenMediaFile,
  }: {
    mediaFiles: Array<{ id: number; filename: string }>
    onOpenMediaFile: (f: { id: number; filename: string }) => void
  }) => (
    <div data-testid="list-view">
      {mediaFiles.map((f) => (
        <button key={f.id} onClick={() => onOpenMediaFile(f)}>
          {f.filename}
        </button>
      ))}
      list:{mediaFiles.length}
    </div>
  ),
}))

jest.mock('../../../components/media-files/MediaFilePreview', () => ({
  __esModule: true,
  default: ({ mediaFile }: { mediaFile: { filename: string } }) => (
    <div data-testid="media-preview">{mediaFile.filename}</div>
  ),
}))

// Mock icons used inside MediaFileModal
jest.mock('@mui/icons-material/CloseRounded', () => ({
  __esModule: true,
  default: () => <svg data-testid="close-icon" />,
}))
jest.mock('@mui/icons-material/NavigateBeforeRounded', () => ({
  __esModule: true,
  default: () => <svg data-testid="prev-icon" />,
}))
jest.mock('@mui/icons-material/NavigateNextRounded', () => ({
  __esModule: true,
  default: () => <svg data-testid="next-icon" />,
}))

// Minimal i18n stub
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (_key: string, fallback: string) => fallback,
    i18n: { language: 'nl' },
  }),
}))

// getTranslatedRecord -> return null so the description box is not rendered
jest.mock('../../../utils/translations', () => ({
  getTranslatedRecord: () => null,
}))

import MediaFileView from '../../../components/media-files/MediaFileView'

// Helpers

const file1 = { id: 1, filename: 'photo.jpg', file_type: 'image' }
const file2 = { id: 2, filename: 'report.pdf', file_type: 'pdf' }
const file3 = { id: 3, filename: 'notes.docx', file_type: 'document' }

// Layout selection

describe('MediaFileView - layout selection', () => {
  it('renders list layout when layout="list" on desktop', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1 as never]} layout="list" />)

    expect(screen.getByTestId('list-view')).toHaveTextContent('list:1')
    expect(screen.queryByTestId('grid-view')).not.toBeInTheDocument()
  })

  it('renders grid layout when layout="grid" on desktop', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="grid" />)

    expect(screen.getByTestId('grid-view')).toHaveTextContent('grid:2')
    expect(screen.queryByTestId('list-view')).not.toBeInTheDocument()
  })

  it('defaults to list layout on desktop when no layout prop is given', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1 as never]} />)

    expect(screen.getByTestId('list-view')).toBeInTheDocument()
  })

  it('forces grid layout on small screens even when layout="list" is requested', () => {
    useMediaQueryMock.mockReturnValue(true) // isSmall = true

    render(<MediaFileView mediaFiles={[file1 as never]} layout="list" />)

    expect(screen.getByTestId('grid-view')).toBeInTheDocument()
    expect(screen.queryByTestId('list-view')).not.toBeInTheDocument()
  })
})

// Empty state

describe('MediaFileView - empty state', () => {
  it('renders the empty message when mediaFiles is empty', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[]} />)

    expect(screen.getByText('No media files found')).toBeInTheDocument()
    expect(screen.queryByTestId('list-view')).not.toBeInTheDocument()
    expect(screen.queryByTestId('grid-view')).not.toBeInTheDocument()
  })
})

// Modal - open / close

describe('MediaFileView - modal', () => {
  it('opens the modal with the selected file when a file is clicked', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1 as never]} layout="list" />)

    // Modal should not be visible initially
    expect(screen.queryByTestId('modal')).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))

    const modal = screen.getByTestId('modal')
    expect(modal).toBeInTheDocument()
    expect(within(modal).getByTestId('media-preview')).toHaveTextContent(file1.filename)
  })

  it('closes the modal when the close button is clicked', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1 as never]} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))
    expect(screen.getByTestId('modal')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Close preview' }))
    expect(screen.queryByTestId('modal')).not.toBeInTheDocument()
  })

  it('closes the modal when the backdrop is clicked', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1 as never]} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))
    expect(screen.getByTestId('modal')).toBeInTheDocument()

    // Click the modal wrapper (backdrop) itself
    await userEvent.click(screen.getByTestId('modal'))
    expect(screen.queryByTestId('modal')).not.toBeInTheDocument()
  })

  // Navigation

  it('navigates to the next file when the Next button is clicked', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))

    // Preview shows file1
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file1.filename)

    await userEvent.click(screen.getByRole('button', { name: 'Next file' }))

    // Preview now shows file2
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file2.filename)
  })

  it('navigates to the previous file when the Previous button is clicked', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    // Open the second file directly
    await userEvent.click(screen.getByRole('button', { name: file2.filename }))
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file2.filename)

    await userEvent.click(screen.getByRole('button', { name: 'Previous file' }))

    expect(screen.getByTestId('media-preview')).toHaveTextContent(file1.filename)
  })

  it('disables the Previous button when the first file is selected', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))

    expect(screen.getByRole('button', { name: 'Previous file' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Next file' })).toBeEnabled()
  })

  it('disables the Next button when the last file is selected', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file2.filename }))

    expect(screen.getByRole('button', { name: 'Next file' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Previous file' })).toBeEnabled()
  })

  it('shows the correct counter (x / total) in the modal header', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2, file3] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file2.filename }))

    // file2 is index 1 -> displayed as "2 / 3"
    expect(screen.getByTestId('modal')).toHaveTextContent('2 / 3')
  })

  it('does not show navigation buttons or a counter when there is only one file', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1 as never]} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))

    expect(screen.queryByRole('button', { name: 'Previous file' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Next file' })).not.toBeInTheDocument()
    // Counter text "1 / 1" should not appear
    expect(screen.queryByText(/1 \/ 1/)).not.toBeInTheDocument()
  })

  // Keyboard navigation

  it('navigates with the ArrowRight key', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file1.filename)

    await userEvent.keyboard('{ArrowRight}')
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file2.filename)
  })

  it('navigates with the ArrowLeft key', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file2.filename }))
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file2.filename)

    await userEvent.keyboard('{ArrowLeft}')
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file1.filename)
  })

  it('does not navigate past the first file with ArrowLeft', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file1.filename }))
    await userEvent.keyboard('{ArrowLeft}')

    // Still on file1
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file1.filename)
  })

  it('does not navigate past the last file with ArrowRight', async () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[file1, file2] as never} layout="list" />)

    await userEvent.click(screen.getByRole('button', { name: file2.filename }))
    await userEvent.keyboard('{ArrowRight}')

    // Still on file2
    expect(screen.getByTestId('media-preview')).toHaveTextContent(file2.filename)
  })
})
