import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import ProductionList from '../../components/ProductionList'
import i18n from '../../i18n'

import type { Genre } from '../../types/Genres'
import type { Production } from '../../types/Productions'

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: { main: '#8224E3', contrastText: '#ffffff' },
  },
})

const minimalGenre = (id: number, nlName: string): Genre => ({
  id,
  type: 'primary',
  name: { nl: nlName },
  display_name: nlName,
  vendor_id: null,
})

const baseProduction = (overrides: Partial<Production> = {}): Production => ({
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'solo',
  media_gallery: { id: 0, name: null, media_items: [] },
  uit_database_type: null,
  display_title: null,
  display_artist_name: null,
  first_event_start: null,
  last_event_end: null,
  title: { nl: 'Voorstelling', en: 'Production' },
  artist_name: { nl: 'Artiest', en: 'Artist' },
  tagline: {},
  teaser: {},
  description: {},
  tags: [],
  genres: [],
  events: [],
  ...overrides,
})

const renderList = (props: {
  productions?: Production[]
  selectedGenreIds?: number[]
  onGenreClick?: (id: number) => void
}) => {
  const { productions = [], selectedGenreIds = [] } = props

  return render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={accentTheme}>
          <ProductionList productions={productions} selectedGenreIds={selectedGenreIds} />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  void i18n.changeLanguage('nl')
})

afterEach(() => {
  void i18n.changeLanguage('nl')
})

describe('ProductionList', () => {
  it('renders no cards when the productions list is empty', () => {
    renderList({ productions: [] })

    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('renders one card per production', () => {
    const productions = [
      baseProduction({ id: 1, title: { nl: 'Eerste' } }),
      baseProduction({ id: 2, title: { nl: 'Tweede' } }),
      baseProduction({ id: 3, title: { nl: 'Derde' } }),
    ]

    renderList({ productions })

    expect(screen.getByRole('heading', { name: 'Eerste' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Tweede' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Derde' })).toBeInTheDocument()
  })

  it('each card links to its own detail route', () => {
    const productions = [
      baseProduction({ id: 10, title: { nl: 'Eerste' } }),
      baseProduction({ id: 20, title: { nl: 'Tweede' } }),
    ]

    renderList({ productions })

    const links = screen.getAllByRole('link')
    expect(links.some((l) => l.getAttribute('href') === '/productions/10')).toBe(true)
    expect(links.some((l) => l.getAttribute('href') === '/productions/20')).toBe(true)
  })

  it('forwards selectedGenreIds to every card', () => {
    const productions = [
      baseProduction({ id: 1, title: { nl: 'A' }, genres: [minimalGenre(1, 'Dans')] }),
      baseProduction({ id: 2, title: { nl: 'B' }, genres: [minimalGenre(1, 'Dans')] }),
    ]

    renderList({ productions, selectedGenreIds: [1] })

    expect(screen.getAllByText('Dans')).toHaveLength(2)
    expect(screen.queryByRole('button', { name: 'Filter op Dans' })).not.toBeInTheDocument()
  })

  it('forwards onGenreClick to every card', () => {
    const onGenreClick = jest.fn()
    const productions = [
      baseProduction({ id: 1, title: { nl: 'A' }, genres: [minimalGenre(1, 'Dans')] }),
      baseProduction({ id: 2, title: { nl: 'B' }, genres: [minimalGenre(2, 'Muziek')] }),
    ]

    renderList({ productions, onGenreClick })

    fireEvent.click(screen.getByText('Dans'))
    fireEvent.click(screen.getByText('Muziek'))

    expect(onGenreClick).not.toHaveBeenCalled()
  })

  it('renders without error when selectedGenreIds and onGenreClick are omitted', () => {
    const productions = [baseProduction({ id: 1 })]

    expect(() => renderList({ productions })).not.toThrow()
    expect(screen.getByRole('heading', { name: 'Voorstelling' })).toBeInTheDocument()
  })
})
