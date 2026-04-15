import { render, screen } from '@testing-library/react'

import EntityList from '../../components/entity/EntityList'

describe('EntityList', () => {
  it('renders items in order using the provided renderItem function', () => {
    render(
      <EntityList
        items={[1, 2, 3]}
        getKey={(item) => item}
        renderItem={(item) => <div data-testid="entity-list-item">Item {item}</div>}
      />,
    )

    const items = screen.getAllByTestId('entity-list-item')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent('Item 1')
    expect(items[1]).toHaveTextContent('Item 2')
    expect(items[2]).toHaveTextContent('Item 3')
  })
})
