import { fireEvent, render, screen } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import SearchBar, { FilteredSearchBarProps } from '../../components/searchbar/FilteredSearchBar'
import i18n from '../../i18n'
import { I18nextProvider, initReactI18next } from 'react-i18next'

i18n.use(initReactI18next).init({
  lng: 'nl',
  resources: {
    nl: {
      translation: {
        'searchbar.layout.grid': 'Raster',
        'searchbar.layout.list': 'Lijst',
        'searchbar.period.label': 'Periode',
      },
    },
  },
})

const renderSearchBar = (props: FilteredSearchBarProps) => {
  const theme = createTheme() // You can customize the theme as needed
  return render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={theme}>
        <SearchBar {...props} />
      </ThemeProvider>
    </I18nextProvider>,
  )
}

describe('SearchBar', () => {
  const mockOnSearchChange = jest.fn()
  const mockOnTagToggle = jest.fn()
  const mockOnLayoutChange = jest.fn()
  const mockOnHallChange = jest.fn()
  const mockSetPeriod = jest.fn()

  const props = {
    placeholder: 'Search...',
    searchValue: '',
    onSearchChange: mockOnSearchChange,
    filters: [
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
    period: { fromDate: null, toDate: null },
    setPeriod: mockSetPeriod,
    tags: [
      { name: 'theatre', displayName: 'Theater' },
      { name: 'dance', displayName: 'Dans' },
    ],
    selectedTags: [],
    onTagToggle: mockOnTagToggle,
    layoutOptions: [{ name: 'grid' }, { name: 'list' }],
    currentLayout: 'list',
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
    expect(screen.getByLabelText('Periode')).toBeInTheDocument()
    expect(screen.getByLabelText('Zalen')).toBeInTheDocument()
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
