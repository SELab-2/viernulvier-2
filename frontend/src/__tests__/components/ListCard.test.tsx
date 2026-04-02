import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'
import ListCard from '../../components/ListCard'
import i18n from '../../i18n'
import type { Event } from '../../types/Events'
import type { Genre } from '../../types/Genres'
import type { Hall } from '../../types/Halls'
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

const hallWithLocation = (locationNl: string): Hall => ({
  id: 10,
  space: {
    id: 2,
    location: {
      id: 3,
      street: null,
      number: null,
      postal_code: null,
      city: null,
      country: 'BE',
      phone_1: null,
      phone_2: null,
      is_own_location: true,
      name: { nl: locationNl },
      display_name: null,
    },
    name: { nl: 'Ruimte' },
    display_name: null,
    halls: [],
  },
  seat_selection: false,
  open_seating: true,
  name: { nl: 'Zaal' },
  display_name: null,
  remark: null,
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
  media_gallery: null,
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
    <ListCard
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

describe('ListCard', () => {
  it('renders title, artist, view link, and poster image with translated alt text', () => {
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
    expect(screen.getByRole('link', { name: /Bekijk/ })).toHaveAttribute('href', '/productions/1')
    expect(screen.getByRole('img', { name: 'Afbeelding voor Voorstelling' })).toHaveAttribute(
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
    expect(screen.getByRole('img', { name: 'Afbeelding voor Fallback titel' })).toBeInTheDocument()
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

  it('shows hall location when all events share the same location', () => {
    const hall = hallWithLocation('Campus 404')
    const production = baseProduction({
      events: [makeEvent({ id: 1, hall }), makeEvent({ id: 2, hall })],
    })
    renderListCard({ production })

    expect(screen.getByText('Campus 404')).toBeInTheDocument()
  })

  it('does not show location when events have different locations', () => {
    const production = baseProduction({
      events: [
        makeEvent({ id: 1, hall: hallWithLocation('Campus 404') }),
        makeEvent({ id: 2, hall: hallWithLocation('Andere Zaal') }),
      ],
    })
    renderListCard({ production })

    expect(screen.queryByText('Campus 404')).not.toBeInTheDocument()
    expect(screen.queryByText('Andere Zaal')).not.toBeInTheDocument()
  })

  it('does not show location when events have no hall', () => {
    const production = baseProduction({
      events: [makeEvent({ id: 1, hall: null })],
    })
    renderListCard({ production })

    expect(screen.queryByText('Ruimte')).not.toBeInTheDocument()
  })

  it('shows both date range and location when all events share a location and have dates', () => {
    const hall = hallWithLocation('Campus 404')
    const production = baseProduction({
      events: [
        makeEvent({ id: 1, starts_at: '2026-06-01T20:00:00.000Z', hall }),
        makeEvent({ id: 2, starts_at: '2026-06-05T20:00:00.000Z', hall }),
      ],
    })
    renderListCard({ production })

    expect(screen.getByText('Campus 404')).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.getByText(/jun|Jun/)).toBeInTheDocument()
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

  it('links the view button to the production detail route', () => {
    const production = baseProduction({ id: 42 })
    renderListCard({ production })

    expect(screen.getByRole('link', { name: /Bekijk/ })).toHaveAttribute('href', '/productions/42')
  })

  it('uses English copy when the locale is en', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction()
    renderListCard({ production })

    expect(screen.getByRole('heading', { name: 'Production' })).toBeInTheDocument()
    expect(screen.getByText('Artist')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /View/ })).toHaveAttribute('href', '/productions/1')
    expect(screen.getByRole('img', { name: 'Image for Production' })).toBeInTheDocument()
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

  it('shows only the date row when there is a start time but no hall', () => {
    const production = baseProduction({
      events: [makeEvent({ id: 1, starts_at: '2026-01-10T12:00:00.000Z', hall: null })],
    })
    renderListCard({ production })

    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.queryByText('Campus 404')).not.toBeInTheDocument()
  })

  it('shows only the hall row when events have a hall but no start date', () => {
    const production = baseProduction({
      events: [makeEvent({ id: 1, hall: hallWithLocation('Solo zaal'), starts_at: null })],
    })
    renderListCard({ production })

    expect(screen.getByText('Solo zaal')).toBeInTheDocument()
    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
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

  it('still renders when the hall label resolves to an empty string', () => {
    const hall: Hall = {
      id: 1,
      space: null,
      seat_selection: false,
      open_seating: true,
      name: { nl: '' },
      display_name: null,
      remark: null,
    }
    const production = baseProduction({
      events: [makeEvent({ id: 1, hall })],
    })
    renderListCard({ production })

    expect(screen.getByRole('heading', { name: 'Voorstelling' })).toBeInTheDocument()
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

    const viewLink = screen.getByRole('link', { name: /Bekijk/ })
    expect(viewLink).toHaveAttribute('href', '/productions/1')
  })
})
