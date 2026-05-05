import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'

import SearchBar from '../../components/searchbar/SearchBar'
import i18n from '../../i18n'

import type { ComponentProps } from 'react'

const renderSearchBar = (props: ComponentProps<typeof SearchBar>) =>
  render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={createTheme()}>
        <SearchBar {...props} />
      </ThemeProvider>
    </I18nextProvider>,
  )

describe('SearchBar', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('updates search input and submits on Enter or search button click', () => {
    const onSearchChange = jest.fn()
    const onSearchSubmit = jest.fn()

    renderSearchBar({
      searchValue: '  zoekterm  ',
      onSearchChange,
      onSearchSubmit,
      placeholder: 'Zoek',
    })

    fireEvent.change(screen.getByPlaceholderText('Zoek'), { target: { value: 'nieuw' } })
    fireEvent.keyDown(screen.getByPlaceholderText('Zoek'), { key: 'Enter' })
    fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

    expect(onSearchChange).toHaveBeenCalledWith('nieuw')
    expect(onSearchSubmit).toHaveBeenNthCalledWith(1, 'zoekterm')
    expect(onSearchSubmit).toHaveBeenNthCalledWith(2, 'zoekterm')
  })

  it('does not submit for non-enter keys and works without submit callback', () => {
    const onSearchChange = jest.fn()

    renderSearchBar({
      searchValue: 'term',
      onSearchChange,
      placeholder: 'Search...',
    })

    fireEvent.keyDown(screen.getByPlaceholderText('Search...'), { key: 'Escape' })
    fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

    expect(onSearchChange).not.toHaveBeenCalled()
  })
})
