import { fireEvent, render, screen } from '@testing-library/react'
// Mock useTranslation to avoid i18n warning in tests
jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' } }),
}))
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { MemoryRouter } from 'react-router-dom'
import SearchBar, { FilteredSearchBarProps } from '../../components/searchbar/FilteredSearchBar'

const renderSearchBar = (props: FilteredSearchBarProps) => {
  const theme = createTheme() // You can customize the theme as needed
  return render(
    <MemoryRouter>
      <ThemeProvider theme={theme}>
        <SearchBar {...props} />
      </ThemeProvider>
    </MemoryRouter>,
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
      { display_name: 'Theater', name: { nl: 'Theater', en: 'Theatre' } },
      { display_name: 'Dans', name: { nl: 'Dans', en: 'Dance' } },
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
    renderSearchBar({ ...props, searchValue: '' })
    const input = screen.getByPlaceholderText('Search...')
    fireEvent.change(input, { target: { value: 'new value' } })
    // Simulate controlled input by rerendering with new value
    renderSearchBar({ ...props, searchValue: 'new value' })
    expect(mockOnSearchChange).toHaveBeenCalledWith('new value')
  })

  it('renders all filters', () => {
    renderSearchBar(props)
    expect(screen.getByText('Periode:')).toBeInTheDocument()
    expect(screen.getByText('Zalen:')).toBeInTheDocument()
  })

  it('toggles tags when clicked', () => {
    renderSearchBar(props)
    // Find all tag buttons and match by text
    const tagButtons = screen.getAllByRole('button')
    const tag1 = tagButtons.find((btn) => btn.textContent?.includes('Theater'))
    const tag2 = tagButtons.find((btn) => btn.textContent?.includes('Dans'))
    expect(tag1).toBeTruthy()
    expect(tag2).toBeTruthy()
    fireEvent.click(tag1!)
    expect(mockOnTagToggle).toHaveBeenCalledWith('Theater')
    fireEvent.click(tag2!)
    expect(mockOnTagToggle).toHaveBeenCalledWith('Dans')
    fireEvent.click(tag1!)
    expect(mockOnTagToggle).toHaveBeenCalledWith('Theater')
  })

  it('displays the current layout', () => {
    renderSearchBar(props)
    const layoutButton = screen.getByText('Raster')

    fireEvent.click(layoutButton)
    expect(mockOnLayoutChange).toHaveBeenCalledWith('grid')
  })
})
