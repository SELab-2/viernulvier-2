import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import ProductionGridCard from '../../components/productions/ProductionGridCard'
import i18n from '../../i18n'

import type { Genre } from '../../types/Genres'
import type { Production } from '../../types/Productions'
import type { ReactElement } from 'react'

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: {
      main: '#8224E3',
      contrastText: '#ffffff',
    },
  },
})

const minimalGenre = (id: number, nlName: string): Genre => ({
  id,
  type: 'primary',
  use_as: { id: 1, name: 'cat' },
  name: { nl: nlName },
  display_name: nlName,
  vendor_id: null,
})

const baseProduction = (overrides: Partial<Production> = {}): Production => ({
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'solo',
  first_event_start: null,
  last_event_end: null,
  media_gallery: { id: 0, name: null, media_items: [] },
  uit_database_theme: null,
  uit_database_type: null,
  display_title: null,
  display_artist_name: null,
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

const renderGridCard = (props: {
  production: Production
  selectedGenreIds?: number[]
  onGenreClick?: (id: number) => void
}) => {
  const { production, selectedGenreIds = [] } = props

  const ui: ReactElement = (
    <ProductionGridCard production={production} selectedGenreIds={selectedGenreIds} />
  )

  return render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={accentTheme}>{ui}</ThemeProvider>
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

describe('ProductionGridCard', () => {
  it('renders title, artist, and poster image with translated alt text', () => {
    const production = baseProduction({
      media_gallery: {
        id: 1,
        name: null,
        media_items: [
          {
            id: 1,
            gallery: 1,
            type: 'foto',
            format: 'jpg',
            original_filename: 'x.jpg',
            position: 0,
            width: 100,
            height: 100,
            title: null,
            display_title: null,
            description: null,
            credits: null,
            link: null,
            crops: [{ id: 1, name: 'thumb', image_url: 'https://cdn.example.com/a.jpg' }],
          },
        ],
      },
    })

    renderGridCard({ production })

    expect(screen.getByRole('heading', { name: 'Voorstelling' })).toBeInTheDocument()
    expect(screen.getByText('Artiest')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Voorstelling' })).toHaveAttribute(
      'src',
      'https://cdn.example.com/a.jpg',
    )
  })

  it('the card links to the production detail route', () => {
    const production = baseProduction({ id: 7 })
    renderGridCard({ production })

    expect(screen.getByRole('link', { name: /Voorstelling/ })).toHaveAttribute(
      'href',
      '/productions/7',
    )
  })

  it('the content area links to the production detail route', () => {
    const production = baseProduction({ id: 42 })
    renderGridCard({ production })

    const links = screen.getAllByRole('link')
    expect(links.some((l) => l.getAttribute('href') === '/productions/42')).toBe(true)
  })

  it('omits the artist line when there is no artist translation or display fallback', () => {
    const production = baseProduction({
      artist_name: {},
      display_artist_name: null,
    })

    renderGridCard({ production })

    expect(screen.queryByText('Artiest')).not.toBeInTheDocument()
  })

  it('uses display_title when the current language is missing from title translations', () => {
    const production = baseProduction({
      title: { en: 'English only' },
      display_title: 'Fallback titel',
    })

    renderGridCard({ production })

    expect(screen.getByRole('heading', { name: 'Fallback titel' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Fallback titel' })).toBeInTheDocument()
  })

  it('uses display_artist_name when artist translations are empty for the active language', () => {
    const production = baseProduction({
      artist_name: { en: 'EN artist' },
      display_artist_name: 'Artiest uit display',
    })

    renderGridCard({ production })

    expect(screen.getByText('Artiest uit display')).toBeInTheDocument()
  })

  it('shows the logo fallback when there is no usable poster URL', () => {
    const production = baseProduction({
      media_gallery: {
        id: 1,
        name: null,
        media_items: [
          {
            id: 1,
            gallery: 1,
            type: 'foto',
            format: 'jpg',
            original_filename: 'x.jpg',
            position: 0,
            width: 100,
            height: 100,
            title: null,
            display_title: null,
            description: null,
            credits: null,
            link: null,
            crops: [{ id: 1, name: 'thumb', image_url: null }],
          },
        ],
      },
    })

    renderGridCard({ production })

    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('shows the image fallback when media_gallery has no media items', () => {
    const production = baseProduction({
      media_gallery: { id: 1, name: null, media_items: [] },
    })
    renderGridCard({ production })

    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('shows the image fallback when the first media item has no crops', () => {
    const production = baseProduction({
      media_gallery: {
        id: 1,
        name: null,
        media_items: [
          {
            id: 1,
            gallery: 1,
            type: 'foto',
            format: 'jpg',
            original_filename: 'x.jpg',
            position: 0,
            width: 100,
            height: 100,
            title: null,
            display_title: null,
            description: null,
            credits: null,
            link: null,
            crops: [],
          },
        ],
      },
    })
    renderGridCard({ production })

    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('shows formatted date range when events have start dates', () => {
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-20T20:00:00.000Z',
    })
    renderGridCard({ production })

    expect(screen.getByText(/mrt|Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('does not show the date row when first_event_start is null', () => {
    const production = baseProduction({ first_event_start: null, last_event_end: null })
    renderGridCard({ production })

    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })

  it('shows the start date when last_event_end is null', () => {
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: null,
    })
    renderGridCard({ production })

    expect(screen.getByText(/mrt|Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('shows a date range when first and last event fall on different dates', () => {
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-25T20:00:00.000Z',
    })
    renderGridCard({ production })

    expect(screen.getByText(/mrt/)).toBeInTheDocument()
    expect(screen.getByText(/ - /)).toBeInTheDocument()
  })

  it('shows a single date when first and last event fall on the same day', () => {
    const production = baseProduction({
      first_event_start: '2026-06-01T18:00:00.000Z',
      last_event_end: '2026-06-01T20:00:00.000Z',
    })
    renderGridCard({ production })

    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.queryByText(/ - /)).not.toBeInTheDocument()
  })

  it('renders static genre chips without interactive filter behavior', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'Dans'), minimalGenre(2, 'Muziek')],
    })

    renderGridCard({ production, onGenreClick, selectedGenreIds: [1] })

    expect(screen.getByText('Dans')).toBeInTheDocument()
    expect(screen.getByText('Muziek')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
    expect(onGenreClick).not.toHaveBeenCalled()
  })

  it('does not render a genre row when there are no genres', () => {
    const production = baseProduction({ genres: [] })
    renderGridCard({ production })

    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
  })

  it('renders a genre chip when display_name is null but translated name exists', () => {
    const production = baseProduction({
      genres: [
        {
          id: 1,
          type: 'primary',
          use_as: { id: 1, name: 'cat' },
          name: { nl: 'Zonder display' },
          display_name: null,
          vendor_id: null,
        },
      ],
    })
    renderGridCard({ production })

    expect(screen.queryByText('Zonder display')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
  })

  it('does not fire onGenreClick for static chips', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'A'), minimalGenre(2, 'B')],
    })
    renderGridCard({ production, onGenreClick })

    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('B')).toBeInTheDocument()
    expect(onGenreClick).not.toHaveBeenCalled()
  })

  it('keeps only the card link interactive when genres are static', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(5, 'Chip')],
    })
    renderGridCard({ production, onGenreClick })

    expect(screen.getByText('Chip')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
    expect(onGenreClick).not.toHaveBeenCalled()

    const links = screen.getAllByRole('link')
    expect(links.some((l) => l.getAttribute('href') === '/productions/1')).toBe(true)
  })

  it('uses English copy when the locale is en', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction()
    renderGridCard({ production })

    expect(screen.getByRole('heading', { name: 'Production' })).toBeInTheDocument()
    expect(screen.getByText('Artist')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Production' })).toBeInTheDocument()
  })

  it('formats the date range for the active locale (en)', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-20T20:00:00.000Z',
    })
    renderGridCard({ production })

    expect(screen.getByText(/Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })
})
