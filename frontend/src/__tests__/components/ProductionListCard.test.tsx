import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'
import ProductionListCard from '../../components/ProductionListCard'
import i18n from '../../i18n'
import type { Event } from '../../types/Events'
import type { Genre } from '../../types/Genres'
import type { Production } from '../../types/Productions'

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

const makeEvent = (overrides: Partial<Event> = {}): Event => ({
  id: 1,
  production: {} as Production,
  production_display: null,
  hall: null,
  hall_display: null,
  starts_at: null,
  ends_at: null,
  prices: [],
  ...overrides,
})

const baseProduction = (overrides: Partial<Production> = {}): Production => ({
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'solo',
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

const renderListCard = (props: {
  production: Production
  selectedGenreIds?: number[]
  onGenreClick?: (id: number) => void
}) => {
  const { production, selectedGenreIds = [], onGenreClick = jest.fn() } = props

  const ui: ReactElement = (
    <ProductionListCard
      production={production}
      selectedGenreIds={selectedGenreIds}
      onGenreClick={onGenreClick}
    />
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

describe('ProductionListCard', () => {
  it('renders title, artist, full-card link, and poster image with title as alt text', () => {
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

    renderListCard({ production })

    expect(screen.getByRole('heading', { name: 'Voorstelling' })).toBeInTheDocument()
    expect(screen.getByText('Artiest')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Voorstelling/ })).toHaveAttribute(
      'href',
      '/productions/1',
    )
    expect(screen.getByRole('img', { name: 'Voorstelling' })).toHaveAttribute(
      'src',
      'https://cdn.example.com/a.jpg',
    )
  })

  it('omits the artist line when there is no artist translation or display fallback', () => {
    const production = baseProduction({
      artist_name: {},
      display_artist_name: null,
    })

    renderListCard({ production })

    expect(screen.queryByText('Artiest')).not.toBeInTheDocument()
  })

  it('uses display_title when the current language is missing from title translations', () => {
    const production = baseProduction({
      title: { en: 'English only' },
      display_title: 'Fallback titel',
    })

    renderListCard({ production })

    expect(screen.getByRole('heading', { name: 'Fallback titel' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Fallback titel' })).toBeInTheDocument()
  })

  it('uses display_artist_name when artist translations are empty for the active language', () => {
    const production = baseProduction({
      artist_name: { en: 'EN artist' },
      display_artist_name: 'Artiest uit display',
    })

    renderListCard({ production })

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

    renderListCard({ production })

    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('shows formatted date range when events have start dates', () => {
    const production = baseProduction({
      events: [makeEvent({ id: 1, starts_at: '2026-03-20T18:30:00.000Z' })],
    })
    renderListCard({ production })

    expect(screen.getByText(/mrt|Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('does not show the date row when events is empty', () => {
    const production = baseProduction({ events: [] })
    renderListCard({ production })

    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })

  it('does not show the date row when events is undefined', () => {
    const production = baseProduction({ events: undefined })
    renderListCard({ production })

    expect(screen.queryByText(/mrt|Mar/)).not.toBeInTheDocument()
  })

  it('shows a date range when there are multiple events on different dates', () => {
    const production = baseProduction({
      events: [
        makeEvent({ id: 1, starts_at: '2026-03-20T18:30:00.000Z' }),
        makeEvent({ id: 2, starts_at: '2026-03-25T20:00:00.000Z' }),
      ],
    })
    renderListCard({ production })

    expect(screen.getByText(/mrt/)).toBeInTheDocument()
    expect(screen.getByText(/ - /)).toBeInTheDocument()
  })

  it('shows a single date when all events fall on the same day', () => {
    const production = baseProduction({
      events: [
        makeEvent({ id: 1, starts_at: '2026-06-01T18:00:00.000Z' }),
        makeEvent({ id: 2, starts_at: '2026-06-01T20:00:00.000Z' }),
      ],
    })
    renderListCard({ production })

    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.queryByText(/ - /)).not.toBeInTheDocument()
  })

  it('renders genre chips and forwards clicks', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'Dans'), minimalGenre(2, 'Muziek')],
    })

    renderListCard({ production, onGenreClick, selectedGenreIds: [1] })

    expect(screen.getByRole('button', { name: 'Filter op Dans' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Filter op Muziek' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )

    fireEvent.click(screen.getByRole('button', { name: 'Filter op Muziek' }))
    expect(onGenreClick).toHaveBeenCalledWith(2)
  })

  it('does not render a genre row when there are no genres', () => {
    const production = baseProduction({ genres: [] })
    renderListCard({ production })

    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
  })

  it('does not render a genre row when every genre has display_name null', () => {
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
    renderListCard({ production })

    expect(screen.queryByRole('button', { name: /Filter op/ })).not.toBeInTheDocument()
  })

  it('links the full card to the production detail route', () => {
    const production = baseProduction({ id: 42 })
    renderListCard({ production })

    expect(screen.getByRole('link', { name: /Voorstelling/ })).toHaveAttribute(
      'href',
      '/productions/42',
    )
  })

  it('uses English copy when the locale is en', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction()
    renderListCard({ production })

    expect(screen.getByRole('heading', { name: 'Production' })).toBeInTheDocument()
    expect(screen.getByText('Artist')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Production/ })).toHaveAttribute(
      'href',
      '/productions/1',
    )
    expect(screen.getByRole('img', { name: 'Production' })).toBeInTheDocument()
  })

  it('formats the date range for the active locale (en)', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction({
      events: [makeEvent({ id: 1, starts_at: '2026-03-20T18:30:00.000Z' })],
    })
    renderListCard({ production })

    expect(screen.getByText(/Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('does not show the date row when all events have null starts_at', () => {
    const production = baseProduction({
      events: [makeEvent({ id: 1, starts_at: null })],
    })
    renderListCard({ production })

    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })

  it('shows the image fallback when media_gallery has no media items', () => {
    const production = baseProduction({
      media_gallery: { id: 1, name: null, media_items: [] },
    })
    renderListCard({ production })

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
    renderListCard({ production })

    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('fires onGenreClick once per chip and for each distinct genre', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'A'), minimalGenre(2, 'B')],
    })
    renderListCard({ production, onGenreClick })

    fireEvent.click(screen.getByRole('button', { name: 'Filter op A' }))
    fireEvent.click(screen.getByRole('button', { name: 'Filter op B' }))
    expect(onGenreClick).toHaveBeenCalledTimes(2)
    expect(onGenreClick).toHaveBeenNthCalledWith(1, 1)
    expect(onGenreClick).toHaveBeenNthCalledWith(2, 2)
  })

  it('does not navigate when interacting with a genre chip (link remains separate)', async () => {
    const user = userEvent.setup()
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(5, 'Chip')],
    })
    renderListCard({ production, onGenreClick })

    await user.click(screen.getByRole('button', { name: 'Filter op Chip' }))
    expect(onGenreClick).toHaveBeenCalledWith(5)

    const cardLink = screen.getByRole('link', { name: /Voorstelling/ })
    expect(cardLink).toHaveAttribute('href', '/productions/1')
  })
})
