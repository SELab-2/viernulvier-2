import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'

import GenericGrid from '../../components/GenericGrid'

import type { ReactNode } from 'react'

type Item = {
  id: number
  label: string
}

const renderGrid = (props: {
  items: Item[]
  getKey: (item: Item) => number
  renderItem: (item: Item) => ReactNode
}) => {
  const theme = createTheme()

  return render(
    <ThemeProvider theme={theme}>
      <GenericGrid {...props} />
    </ThemeProvider>,
  )
}

describe('GenericGrid', () => {
  it('renders one item node per provided item', () => {
    const items: Item[] = [
      { id: 1, label: 'First' },
      { id: 2, label: 'Second' },
    ]

    renderGrid({
      items,
      getKey: (item) => item.id,
      renderItem: (item) => <span>{item.label}</span>,
    })

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

    renderGrid({ items, getKey, renderItem })

    expect(getKey).toHaveBeenCalledTimes(3)
    expect(renderItem).toHaveBeenCalledTimes(3)
    expect(getKey).toHaveBeenNthCalledWith(1, items[0])
    expect(getKey).toHaveBeenNthCalledWith(2, items[1])
    expect(getKey).toHaveBeenNthCalledWith(3, items[2])
  })

  it('renders empty container content when items is empty', () => {
    const { container } = renderGrid({
      items: [],
      getKey: (item) => item.id,
      renderItem: (item) => <span>{item.label}</span>,
    })

    expect(container.textContent).toBe('')
  })
})
