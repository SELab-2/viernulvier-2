import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { I18nextProvider } from 'react-i18next'

import ChipFilterSection, { type ChipOption } from '../../../features/productions/components/filter-panel/ChipFilterSection'
import i18n from '../../../i18n'

jest.mock('../../components/chips/GenreAndTagChip', () => ({
  __esModule: true,
  default: ({
    id,
    name,
    chipType,
    selected,
    onToggle,
  }: {
    id: number
    name: string
    chipType: 'genre' | 'seriesTag'
    selected?: boolean
    onToggle?: () => void
  }) => (
    <button
      type="button"
      data-testid={`chip-${chipType}-${String(id)}`}
      data-selected={selected ? 'true' : 'false'}
      onClick={onToggle}
    >
      {name}
    </button>
  ),
}))

const genre = (id: number, name: string): ChipOption => ({
  id,
  name,
  labels: { nl: name },
  chipType: 'genre',
})

const seriesTag = (id: number, name: string): ChipOption => ({
  id,
  name,
  labels: { nl: name },
  chipType: 'seriesTag',
})

type RenderSectionProps = {
  options: ChipOption[]
  selectedIds?: number[]
  emptyLabel?: string
  onToggle?: (id: number) => void
}

const renderSection = (props: RenderSectionProps) => {
  const onToggle = props.onToggle ?? jest.fn()
  const view = render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={createTheme()}>
        <ChipFilterSection
          options={props.options}
          selectedIds={props.selectedIds ?? []}
          emptyLabel={props.emptyLabel ?? 'empty'}
          onToggle={onToggle}
        />
      </ThemeProvider>
    </I18nextProvider>,
  )
  return { ...view, onToggle }
}

describe('ChipFilterSection', () => {
  beforeEach(async () => {
    jest.clearAllMocks()
    await i18n.changeLanguage('nl')
  })

  it('does not show search or a scroll region when there are five or fewer options', () => {
    renderSection({
      options: [genre(1, 'A'), genre(2, 'B'), genre(3, 'C'), genre(4, 'D'), genre(5, 'E')],
    })

    expect(
      screen.queryByPlaceholderText(i18n.t('productions.home.filters.searchGenres')),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('region', { name: i18n.t('productions.home.filters.scrollHint') }),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(i18n.t('productions.home.filters.scrollHint')),
    ).not.toBeInTheDocument()
  })

  it('sorts selected options first and places overflow options in a scrollable region', () => {
    renderSection({
      options: [
        genre(6, 'Alpha'),
        genre(1, 'Delta'),
        genre(2, 'Charlie'),
        genre(3, 'Echo'),
        genre(4, 'Bravo'),
        genre(5, 'Foxtrot'),
      ],
      selectedIds: [6],
    })

    expect(screen.getAllByTestId(/chip-genre-/).map((chip) => chip.textContent)).toEqual([
      'Alpha',
      'Bravo',
      'Charlie',
      'Delta',
      'Echo',
      'Foxtrot',
    ])
    expect(screen.getByTestId('chip-genre-6')).toHaveAttribute('data-selected', 'true')
    expect(
      screen.getByRole('region', { name: i18n.t('productions.home.filters.scrollHint') }),
    ).toBeInTheDocument()
    expect(
      screen.queryByText(i18n.t('productions.home.filters.scrollHint')),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: i18n.t('productions.home.filters.scrollHint') }),
    ).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^(Meer|More)$/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^(Minder|Less)$/ })).not.toBeInTheDocument()
  })

  it('shows the genre search placeholder when there is overflow and options are genres', () => {
    renderSection({
      options: [
        genre(1, 'Alpha'),
        genre(2, 'Bravo'),
        genre(3, 'Charlie'),
        genre(4, 'Delta'),
        genre(5, 'Echo'),
        genre(6, 'Foxtrot'),
      ],
    })

    expect(
      screen.getByPlaceholderText(i18n.t('productions.home.filters.searchGenres')),
    ).toBeInTheDocument()
  })

  it('shows the tag search placeholder when there is overflow and options are series tags', () => {
    renderSection({
      options: [
        seriesTag(1, 'Alpha'),
        seriesTag(2, 'Bravo'),
        seriesTag(3, 'Charlie'),
        seriesTag(4, 'Delta'),
        seriesTag(5, 'Echo'),
        seriesTag(6, 'Foxtrot'),
      ],
    })

    expect(
      screen.getByPlaceholderText(i18n.t('productions.home.filters.searchTags')),
    ).toBeInTheDocument()
  })

  it('filters genre chips by a case-insensitive substring of the name', () => {
    renderSection({
      options: [
        genre(1, 'Alpha'),
        genre(2, 'Bravo'),
        genre(3, 'Charlie'),
        genre(4, 'Delta'),
        genre(5, 'Echo'),
        genre(6, 'Foxtrot'),
      ],
    })

    const search = screen.getByPlaceholderText(i18n.t('productions.home.filters.searchGenres'))
    fireEvent.change(search, { target: { value: 'BRAV' } })

    expect(screen.getByTestId('chip-genre-2')).toHaveTextContent('Bravo')
    expect(screen.queryByTestId('chip-genre-1')).not.toBeInTheDocument()
    expect(screen.queryByTestId('chip-genre-3')).not.toBeInTheDocument()
  })

  it('trims leading and trailing whitespace from the search query', () => {
    renderSection({
      options: [
        genre(1, 'Alpha'),
        genre(2, 'Bravo'),
        genre(3, 'Charlie'),
        genre(4, 'Delta'),
        genre(5, 'Echo'),
        genre(6, 'Foxtrot'),
      ],
    })

    const search = screen.getByPlaceholderText(i18n.t('productions.home.filters.searchGenres'))
    fireEvent.change(search, { target: { value: '  echo  ' } })

    expect(screen.getByTestId('chip-genre-5')).toHaveTextContent('Echo')
    expect(screen.queryByTestId('chip-genre-1')).not.toBeInTheDocument()
  })

  it('shows the empty label when the search matches no options', () => {
    const emptyLabel = 'Geen resultaten'
    renderSection({
      options: [
        genre(1, 'Alpha'),
        genre(2, 'Bravo'),
        genre(3, 'Charlie'),
        genre(4, 'Delta'),
        genre(5, 'Echo'),
        genre(6, 'Foxtrot'),
      ],
      emptyLabel,
    })

    const search = screen.getByPlaceholderText(i18n.t('productions.home.filters.searchGenres'))
    fireEvent.change(search, { target: { value: 'zzz' } })

    expect(screen.getByText(emptyLabel)).toBeInTheDocument()
    expect(screen.queryByTestId(/chip-genre-/)).not.toBeInTheDocument()
  })

  it('clears the filter and shows all chips again when the search is cleared', () => {
    renderSection({
      options: [
        genre(1, 'Alpha'),
        genre(2, 'Bravo'),
        genre(3, 'Charlie'),
        genre(4, 'Delta'),
        genre(5, 'Echo'),
        genre(6, 'Foxtrot'),
      ],
    })

    const search = screen.getByPlaceholderText(i18n.t('productions.home.filters.searchGenres'))
    fireEvent.change(search, { target: { value: 'bravo' } })
    expect(screen.queryByTestId('chip-genre-1')).not.toBeInTheDocument()

    fireEvent.change(search, { target: { value: '' } })

    expect(screen.getByTestId('chip-genre-1')).toBeInTheDocument()
    expect(screen.getByTestId('chip-genre-6')).toBeInTheDocument()
  })

  it('filters tag chips the same way as genres', () => {
    renderSection({
      options: [
        seriesTag(1, 'Premiere'),
        seriesTag(2, 'Festival'),
        seriesTag(3, 'Tour'),
        seriesTag(4, 'Kids'),
        seriesTag(5, 'Dance'),
        seriesTag(6, 'Music'),
      ],
    })

    const search = screen.getByPlaceholderText(i18n.t('productions.home.filters.searchTags'))
    fireEvent.change(search, { target: { value: 'fest' } })

    expect(screen.getByTestId('chip-seriesTag-2')).toHaveTextContent('Festival')
    expect(screen.queryByTestId('chip-seriesTag-1')).not.toBeInTheDocument()
  })
})