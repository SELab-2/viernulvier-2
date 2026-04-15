import { render, screen } from '@testing-library/react'

import EntityGrid from '../../components/entity/EntityGrid'

describe('EntityGrid', () => {
  it('renders items using the provided renderItem function', () => {
    render(
      <EntityGrid
        items={[1, 2, 3]}
        getKey={(item) => item}
        renderItem={(item) => <div data-testid="entity-grid-item">Item {item}</div>}
      />,
    )

    const items = screen.getAllByTestId('entity-grid-item')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent('Item 1')
    expect(items[1]).toHaveTextContent('Item 2')
    expect(items[2]).toHaveTextContent('Item 3')
  })
})
