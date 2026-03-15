import { fireEvent, render, screen } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import SearchBar, { FilteredSearchBarProps } from '../../components/searchbar/FilteredSearchBar'

const renderSearchBar = (props: FilteredSearchBarProps) => {
  const theme = createTheme() // You can customize the theme as needed
  return render(
    <ThemeProvider theme={theme}>
      <SearchBar {...props} />
    </ThemeProvider>,
  )
}

describe('SearchBar', () => {
  const mockOnSearchChange = jest.fn()
  const mockOnTagToggle = jest.fn()
  const mockOnLayoutChange = jest.fn()
  const mockOnPeriodChange = jest.fn()
  const mockOnHallChange = jest.fn()

  const props = {
    placeholder: 'Search...',
    searchValue: '',
    onSearchChange: mockOnSearchChange,
    filters: [
      {
        name: 'period',
        displayName: 'Periode',
        options: [
          { name: 'all', displayName: 'Alle' },
          { name: '2025', displayName: '2025' },
          { name: '2026', displayName: '2026' },
        ],
        value: 'all',
        onChange: mockOnPeriodChange,
      },
      {
        name: 'hall',
        displayName: 'Zalen',
        options: [
          { name: 'all', displayName: 'Alle' },
          { name: 'hall1', displayName: 'Hall 1' },
          { name: 'hall2', displayName: 'Hall 2' },
        ],
        value: 'all',
        onChange: mockOnHallChange,
      },
    ],
    tags: [
      { name: 'theatre', displayName: 'Theater' },
      { name: 'dance', displayName: 'Dans' },
    ],
    selectedTags: [],
    onTagToggle: mockOnTagToggle,
    layoutOptions: [
      { name: 'grid', displayName: 'Raster' },
      { name: 'list', displayName: 'Lijst' },
    ],
    currentLayout: 'grid',
    onLayoutChange: mockOnLayoutChange,
  }

  it('renders the search bar with provided placeholder', () => {
    renderSearchBar(props)
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
  })

  it('calls onSearchChange when input value changes', () => {
    renderSearchBar(props)
    const input = screen.getByPlaceholderText('Search...')

    fireEvent.change(input, { target: { value: 'new value' } })
    expect(mockOnSearchChange).toHaveBeenCalledWith('new value')
  })

  it('renders all filters', () => {
    renderSearchBar(props)
    expect(screen.getByText('Periode:')).toBeInTheDocument()
    expect(screen.getByText('Zalen:')).toBeInTheDocument()
  })

  it('toggles tags when clicked', () => {
    renderSearchBar(props)
    const tag1 = screen.getByText('Theater')
    const tag2 = screen.getByText('Dans')

    fireEvent.click(tag1)
    expect(mockOnTagToggle).toHaveBeenCalledWith('theatre')
    fireEvent.click(tag2)
    expect(mockOnTagToggle).toHaveBeenCalledWith('dance')
    fireEvent.click(tag1)
    expect(mockOnTagToggle).toHaveBeenCalledWith('theatre')
  })

  it('displays the current layout', () => {
    renderSearchBar(props)
    const layoutButton = screen.getByText('Raster')

    fireEvent.click(layoutButton)
    expect(mockOnLayoutChange).toHaveBeenCalledWith('grid')
  })
})
