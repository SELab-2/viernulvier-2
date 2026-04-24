import '@testing-library/jest-dom'
import { describe, expect, it, jest } from '@jest/globals'
import { render, screen } from '@testing-library/react'

jest.mock('../../../components/GenericList', () => ({
  __esModule: true,
  default: ({
    items,
    getKey,
    renderItem,
  }: {
    items: Array<{ id: string; filename: string }>
    getKey: (item: { id: string }) => string
    renderItem: (item: { id: string; filename: string }) => React.ReactNode
  }) => (
    <div data-testid="generic-list">
      {items.map((item) => (
        <div key={getKey(item)} data-testid={`list-item-${item.id}`}>
          {renderItem(item)}
        </div>
      ))}
    </div>
  ),
}))

jest.mock('../../../components/media-files/MediaFileListCard', () => ({
  __esModule: true,
  default: ({ mediaFile }: { mediaFile: { filename: string } }) => (
    <div data-testid="list-card">{mediaFile.filename}</div>
  ),
}))

import MediaFileList from '../../../components/media-files/MediaFileList'

describe('MediaFileList', () => {
  it('renders all media files through GenericList and MediaFileListCard', () => {
    render(
      <MediaFileList
        mediaFiles={
          [
            { id: '1', filename: 'one.pdf' },
            { id: '2', filename: 'two.jpg' },
          ] as never
        }
      />,
    )

    expect(screen.getByTestId('generic-list')).toBeInTheDocument()
    expect(screen.getAllByTestId('list-card')).toHaveLength(2)
    expect(screen.getByText('one.pdf')).toBeInTheDocument()
    expect(screen.getByText('two.jpg')).toBeInTheDocument()
  })
})
