import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'
import ListCard from '../../components/ListCard'
import i18n from '../../i18n'
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
  display_name: null,
  vendor_id: null,
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
  ...overrides,
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

const renderListCard = (props: {
  production: Production
  pathname?: string
  hall?: Hall | null
  starts_at?: string | null
  selectedGenreIds?: number[]
  onGenreClick?: (id: number) => void
}) => {
  const {
    production,
    pathname = '/production/1',
    hall,
    starts_at,
    selectedGenreIds = [],
    onGenreClick = jest.fn(),
  } = props

  const ui: ReactElement = (
    <ListCard
      production={production}
      pathname={pathname}
      hall={hall}
      starts_at={starts_at}
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
    expect(screen.getByRole('link', { name: /Bekijk/ })).toHaveAttribute('href', '/production/1')
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

  it('shows formatted start date when starts_at is set', () => {
    const production = baseProduction()
    renderListCard({ production, starts_at: '2026-03-20T18:30:00.000Z' })

    expect(screen.getByText(/maart|March/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('does not show the date row when starts_at is null', () => {
    const production = baseProduction()
    renderListCard({ production, starts_at: null })

    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })

  it('does not show the date row when starts_at is omitted', () => {
    const production = baseProduction()
    renderListCard({ production })

    expect(screen.queryByText(/maart|March/)).not.toBeInTheDocument()
  })

  it('shows hall location when hall is provided', () => {
    const production = baseProduction()
    renderListCard({ production, hall: hallWithLocation('Campus 404') })

    expect(screen.getByText('Campus 404')).toBeInTheDocument()
  })

  it('does not show location when hall is absent', () => {
    const production = baseProduction()
    renderListCard({ production, hall: undefined })

    expect(screen.queryByText('Campus 404')).not.toBeInTheDocument()
  })

  it('does not show location when hall is null', () => {
    const production = baseProduction()
    renderListCard({ production, hall: null })

    expect(screen.queryByText('Ruimte')).not.toBeInTheDocument()
  })

  it('shows both start date and hall location when both are provided', () => {
    const production = baseProduction()
    renderListCard({
      production,
      starts_at: '2026-06-01T20:00:00.000Z',
      hall: hallWithLocation('Campus 404'),
    })

    expect(screen.getByText('Campus 404')).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.getByText(/juni|June|juin/)).toBeInTheDocument()
  })

  it('renders genre chips and forwards clicks', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'Dans'), minimalGenre(2, 'Muziek')],
    })

    renderListCard({ production, onGenreClick, selectedGenreIds: [1] })

    expect(screen.getByRole('button', { name: 'Filter by Dans' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Filter by Muziek' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )

    fireEvent.click(screen.getByRole('button', { name: 'Filter by Muziek' }))
    expect(onGenreClick).toHaveBeenCalledWith(2)
  })

  it('does not render a genre row when there are no genres', () => {
    const production = baseProduction({ genres: [] })
    renderListCard({ production })

    expect(screen.queryByRole('button', { name: /^Filter by/ })).not.toBeInTheDocument()
  })

  it('uses the custom pathname on the view link', () => {
    const production = baseProduction()
    renderListCard({ production, pathname: '/custom/path' })

    expect(screen.getByRole('link', { name: /Bekijk/ })).toHaveAttribute('href', '/custom/path')
  })

  it('uses English copy when the locale is en', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction()
    renderListCard({ production })

    expect(screen.getByRole('heading', { name: 'Production' })).toBeInTheDocument()
    expect(screen.getByText('Artist')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /View/ })).toHaveAttribute('href', '/production/1')
    expect(screen.getByRole('img', { name: 'Image for Production' })).toBeInTheDocument()
  })

  it('formats the date for the active locale (en)', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction()
    renderListCard({ production, starts_at: '2026-03-20T18:30:00.000Z' })

    expect(screen.getByText(/March/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('shows only the date row when there is a start time but no hall', () => {
    const production = baseProduction()
    renderListCard({ production, starts_at: '2026-01-10T12:00:00.000Z', hall: undefined })

    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.queryByText('Campus 404')).not.toBeInTheDocument()
  })

  it('shows only the hall row when a hall is set but there is no start time', () => {
    const production = baseProduction()
    renderListCard({ production, hall: hallWithLocation('Solo zaal') })

    expect(screen.getByText('Solo zaal')).toBeInTheDocument()
    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })

  it('does not show the date row when starts_at is an empty string', () => {
    const production = baseProduction()
    renderListCard({ production, starts_at: '' })

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
    const production = baseProduction()
    const hall: Hall = {
      id: 1,
      space: null,
      seat_selection: false,
      open_seating: true,
      name: { nl: '' },
      display_name: null,
      remark: null,
    }
    renderListCard({ production, hall })

    expect(screen.getByRole('heading', { name: 'Voorstelling' })).toBeInTheDocument()
  })

  it('fires onGenreClick once per chip and for each distinct genre', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'A'), minimalGenre(2, 'B')],
    })
    renderListCard({ production, onGenreClick })

    fireEvent.click(screen.getByRole('button', { name: 'Filter by A' }))
    fireEvent.click(screen.getByRole('button', { name: 'Filter by B' }))
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
    renderListCard({ production, onGenreClick, pathname: '/events/1' })

    await user.click(screen.getByRole('button', { name: 'Filter by Chip' }))
    expect(onGenreClick).toHaveBeenCalledWith(5)

    const viewLink = screen.getByRole('link', { name: /Bekijk/ })
    expect(viewLink).toHaveAttribute('href', '/events/1')
  })
})
