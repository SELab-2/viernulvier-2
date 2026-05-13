import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'

import i18n from '../../../../i18n'
import SearchControlsBar, {
  type SearchControlsBarProps,
} from '../../../../shared/components/search/SearchControlsBar'

const renderSearchBar = (props: SearchControlsBarProps, mode: 'light' | 'dark' = 'light') => {
  const theme = createTheme({ palette: { mode } })
  return render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={theme}>
        <SearchControlsBar {...props} />
      </ThemeProvider>
    </I18nextProvider>,
  )
}

describe('SearchControlsBar', () => {
  const mockOnSearchChange = jest.fn()
  const mockOnSortChange = jest.fn()
  const mockOnSortDirectionChange = jest.fn()
  const mockOnViewModeChange = jest.fn()
  const mockOnSearchSubmit = jest.fn()

  beforeEach(async () => {
    jest.clearAllMocks()
    await i18n.changeLanguage('nl')
  })

  const props = {
    placeholder: 'Search...',
    searchValue: '',
    onSearchChange: mockOnSearchChange,
    onSearchSubmit: mockOnSearchSubmit,
    resultCount: 12,
    sortTarget: 'date' as const,
    onSortTargetChange: mockOnSortChange,
    sortDirection: 'desc' as const,
    onSortDirectionChange: mockOnSortDirectionChange,
    viewMode: 'grid' as const,
    onViewModeChange: mockOnViewModeChange,
  }

  it('renders the search bar with provided placeholder', () => {
    renderSearchBar(props)
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
    expect(screen.getByText('12 resultaten gevonden')).toBeInTheDocument()
  })

  it('renders with default optional controls and no result count', () => {
    renderSearchBar({
      searchValue: '',
      onSearchChange: mockOnSearchChange,
    })

    expect(screen.getByRole('combobox', { name: 'Sorteer op' })).toBeInTheDocument()
    expect(screen.queryByText(/resultaat gevonden/)).not.toBeInTheDocument()

    fireEvent.click(screen.getByLabelText('Schakel naar oplopend'))
    fireEvent.click(screen.getByLabelText('Raster'))

    expect(mockOnSortDirectionChange).not.toHaveBeenCalled()
    expect(mockOnViewModeChange).not.toHaveBeenCalled()
  })

  it('uses singular copy when there is exactly one result', () => {
    renderSearchBar({ ...props, resultCount: 1 })

    expect(screen.getByText('1 resultaat gevonden')).toBeInTheDocument()
  })

  it('calls onSearchChange when input value changes', () => {
    renderSearchBar({ ...props, searchValue: '' })
    const input = screen.getByPlaceholderText('Search...')
    fireEvent.change(input, { target: { value: 'new value' } })
    expect(mockOnSearchChange).toHaveBeenCalledWith('new value')
  })

  it('renders the sort selector', () => {
    renderSearchBar(props)
    expect(screen.getByLabelText('Sorteer op')).toBeInTheDocument()
  })

  it('changes sort target when a new value is selected', () => {
    renderSearchBar(props)
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Sorteer op' }))
    fireEvent.click(screen.getByRole('option', { name: 'Naam' }))
    expect(mockOnSortChange).toHaveBeenCalledWith('name')
  })

  it('toggles sort direction when the direction button is clicked', () => {
    renderSearchBar(props)
    fireEvent.click(screen.getByLabelText('Schakel naar oplopend'))
    expect(mockOnSortDirectionChange).toHaveBeenCalledWith('asc')
  })

  it('toggles descending when the current sort direction is ascending', () => {
    renderSearchBar({ ...props, sortDirection: 'asc' })

    fireEvent.click(screen.getByLabelText('Schakel naar aflopend'))

    expect(mockOnSortDirectionChange).toHaveBeenCalledWith('desc')
  })

  it('changes view mode when the list toggle is selected', () => {
    renderSearchBar(props)
    fireEvent.click(screen.getByLabelText('Lijst'))
    expect(mockOnViewModeChange).toHaveBeenCalledWith('list')
  })

  it('hides view mode toggle when disabled', () => {
    renderSearchBar({ ...props, showViewModeToggle: false })
    expect(screen.queryByLabelText('Lijst')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Raster')).not.toBeInTheDocument()
  })

  it('falls back to the first allowed sort target when the current value is invalid', () => {
    renderSearchBar({
      ...props,
      sortTarget: 'date',
      sortTargetOptions: [{ value: 'name', labelKey: 'searchbar.sort.name' }],
    })

    expect(screen.getByRole('combobox', { name: 'Sorteer op' })).toHaveTextContent('Naam')
  })

  it('renders extra controls and keeps dark mode interactions usable', () => {
    renderSearchBar(
      {
        ...props,
        extraControls: <button type="button">Extra filter</button>,
      },
      'dark',
    )

    expect(screen.getByRole('button', { name: 'Extra filter' })).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Lijst'))
    expect(mockOnViewModeChange).toHaveBeenCalledWith('list')
  })

  it('submits the current query when the search icon is clicked', () => {
    renderSearchBar({ ...props, searchValue: 'vieren' })
    fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))
    expect(mockOnSearchSubmit).toHaveBeenCalledWith('vieren')
  })
})
