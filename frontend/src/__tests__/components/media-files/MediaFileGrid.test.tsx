import { describe, expect, it, jest } from '@jest/globals'
import { render, screen } from '@testing-library/react'
import React from 'react'

jest.mock('../../../shared/components/GenericGrid', () => ({
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
    <div data-testid="generic-grid">
      {items.map((item) => (
        <div key={getKey(item)} data-testid={`grid-item-${item.id}`}>
          {renderItem(item)}
        </div>
      ))}
    </div>
  ),
}))

jest.mock('../../../features/media-files/components/MediaFileGridCard', () => ({
  __esModule: true,
  default: ({ mediaFile }: { mediaFile: { filename: string } }) => (
    <div data-testid="grid-card">{mediaFile.filename}</div>
  ),
}))

import MediaFileGrid from '../../../features/media-files/components/MediaFileGrid'

describe('MediaFileGrid', () => {
  it('renders all media files through GenericGrid and MediaFileGridCard', () => {
    render(
      <MediaFileGrid
        mediaFiles={
          [
            { id: '1', filename: 'one.pdf' },
            { id: '2', filename: 'two.jpg' },
          ] as never
        }
      />,
    )

    expect(screen.getByTestId('generic-grid')).toBeInTheDocument()
    expect(screen.getAllByTestId('grid-card')).toHaveLength(2)
    expect(screen.getByText('one.pdf')).toBeInTheDocument()
    expect(screen.getByText('two.jpg')).toBeInTheDocument()
  })
})
