import { render, screen } from '@testing-library/react'

import GenericList from '../../shared/components/GenericList'

type Item = {
  id: number
  label: string
}

describe('GenericList', () => {
  it('renders one item node per provided item', () => {
    const items: Item[] = [
      { id: 1, label: 'First' },
      { id: 2, label: 'Second' },
    ]

    render(
      <GenericList
        items={items}
        getKey={(item) => item.id}
        renderItem={(item) => <span>{item.label}</span>}
      />,
    )

    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
  })

  it('calls getKey and renderItem for each item', () => {
    const items: Item[] = [
      { id: 1, label: 'One' },
      { id: 2, label: 'Two' },
      { id: 3, label: 'Three' },
    ]

    const getKey = jest.fn((item: Item) => item.id)
    const renderItem = jest.fn((item: Item) => <span>{item.label}</span>)

    render(<GenericList items={items} getKey={getKey} renderItem={renderItem} />)

    expect(getKey).toHaveBeenCalledTimes(3)
    expect(renderItem).toHaveBeenCalledTimes(3)
    expect(renderItem).toHaveBeenNthCalledWith(1, items[0])
    expect(renderItem).toHaveBeenNthCalledWith(2, items[1])
    expect(renderItem).toHaveBeenNthCalledWith(3, items[2])
  })

  it('renders empty content when items is empty', () => {
    const { container } = render(
      <GenericList
        items={[]}
        getKey={(item: Item) => item.id}
        renderItem={(item) => <span>{item.label}</span>}
      />,
    )

    expect(container.textContent).toBe('')
  })
})
