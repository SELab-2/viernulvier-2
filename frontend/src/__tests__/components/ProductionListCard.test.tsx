import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import ProductionListCard from '../../components/productions/ProductionListCard'
import i18n from '../../i18n'
import { toLocalizedPath } from '../../utils/localizedRoutes'

import type { Genre } from '../../types/Genres'
import type { Production } from '../../types/Productions'
import type { Tag } from '../../types/Tags'
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
  name: { nl: nlName },
  display_name: nlName,
  vendor_id: null,
})

const minimalTag = (id: number, nlName: string, enName = nlName): Tag => ({
  id,
  url: `https://example.com/tags/${id}`,
  source: 'db',
  type: 'series',
  is_enabled: true,
  image: null,
  display_name: nlName,
  display_short_description: null,
  display_excerpt: null,
  display_url_title: null,
  first_production_start: null,
  last_production_end: null,
  name: { nl: nlName, en: enName },
  excerpt: null,
  short_description: null,
  url_title: null,
})

const baseProduction = (overrides: Partial<Production> = {}): Production => ({
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'solo',
  first_event_start: null,
  last_event_end: null,
  media_gallery: { id: 0, name: null, media_items: [] },
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
  selectedTagIds?: number[]
  onGenreClick?: (id: number) => void
}) => {
  const { production, selectedGenreIds, selectedTagIds } = props

  const ui: ReactElement = (
    <ProductionListCard
      production={production}
      selectedGenreIds={selectedGenreIds}
      selectedTagIds={selectedTagIds}
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

const LocationEcho = () => {
  const location = useLocation()

  return <div>{`${location.pathname}${location.search}`}</div>
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
      toLocalizedPath('/productions/1', 'nl'),
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
    expect(screen.getByRole('img', { name: 'Voorstelling' })).toHaveStyle({ height: '100%' })
  })

  it('navigates series-tag chip clicks to the archive instead of the production detail page', () => {
    const production = baseProduction({
      id: 7,
      tags: [minimalTag(11, 'Reeks')],
    })

    render(
      <MemoryRouter initialEntries={['/nl/productions?t=3']}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={accentTheme}>
            <Routes>
              <Route
                path="/nl/productions"
                element={<ProductionListCard production={production} />}
              />
              <Route path="/nl/archief" element={<LocationEcho />} />
            </Routes>
          </ThemeProvider>
        </I18nextProvider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Reeks' }))

    expect(screen.getByText('/nl/archief?t=3-11')).toBeInTheDocument()
    expect(screen.queryByText('PRODUCTION DETAIL')).not.toBeInTheDocument()
  })

  it('appends genre chips to the active genre filter in the archive url', () => {
    const production = baseProduction({
      id: 7,
      genres: [minimalGenre(22, 'Genre')],
    })

    render(
      <MemoryRouter initialEntries={['/nl/productions?g=1']}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={accentTheme}>
            <Routes>
              <Route
                path="/nl/productions"
                element={<ProductionListCard production={production} />}
              />
              <Route path="/nl/archief" element={<LocationEcho />} />
            </Routes>
          </ThemeProvider>
        </I18nextProvider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Genre' }))

    expect(screen.getByText('/nl/archief?g=1-22')).toBeInTheDocument()
  })

  it('shows formatted date range when events have start dates', () => {
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-20T20:00:00.000Z',
    })
    renderListCard({ production })

    expect(screen.getByText(/mrt|Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('does not show the date row when first_event_start is null', () => {
    const production = baseProduction({ first_event_start: null, last_event_end: null })
    renderListCard({ production })

    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })

  it('shows the start date when last_event_end is null', () => {
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: null,
    })
    renderListCard({ production })

    expect(screen.getByText(/mrt|Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('shows a date range when first and last event fall on different dates', () => {
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-25T20:00:00.000Z',
    })
    renderListCard({ production })

    expect(screen.getByText(/mrt/)).toBeInTheDocument()
    expect(screen.getByText(/ - /)).toBeInTheDocument()
  })

  it('shows a single date when first and last event fall on the same day', () => {
    const production = baseProduction({
      first_event_start: '2026-06-01T18:00:00.000Z',
      last_event_end: '2026-06-01T20:00:00.000Z',
    })
    renderListCard({ production })

    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.queryByText(/ - /)).not.toBeInTheDocument()
  })

  it('renders genre chips as navigation links without search-filter behavior', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'Dans'), minimalGenre(2, 'Muziek')],
    })

    renderListCard({ production, onGenreClick, selectedGenreIds: [1] })

    expect(screen.getByText('Dans')).toBeInTheDocument()
    expect(screen.getByText('Muziek')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
    expect(onGenreClick).not.toHaveBeenCalled()
  })

  it('renders series tag chips alongside genres as navigation links', () => {
    const production = baseProduction({
      tags: [minimalTag(11, 'Festivalreeks')],
      genres: [minimalGenre(1, 'Dans')],
    })

    renderListCard({ production })

    expect(screen.getByText('Festivalreeks')).toBeInTheDocument()
    expect(screen.getByText('Dans')).toBeInTheDocument()
  })

  it('highlights selected series tags with the series color', () => {
    const production = baseProduction({
      tags: [minimalTag(11, 'Festivalreeks')],
    })

    renderListCard({ production, selectedTagIds: [11] })

    expect(screen.getByText('Festivalreeks').closest('.MuiChip-root')).toHaveStyle({
      backgroundColor: '#1976d2',
      borderColor: '#1976d2',
    })
  })

  it('sorts selected series tags before unselected tags', () => {
    const production = baseProduction({
      tags: [minimalTag(10, 'Oud'), minimalTag(11, 'Geselecteerd')],
    })

    renderListCard({ production, selectedTagIds: [11] })

    const selectedTag = screen.getByText('Geselecteerd')
    const unselectedTag = screen.getByText('Oud')

    expect(selectedTag.compareDocumentPosition(unselectedTag)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    )
  })

  it('sorts selected genres before unselected genres', () => {
    const production = baseProduction({
      genres: [minimalGenre(1, 'Eerste'), minimalGenre(2, 'Tweede')],
    })

    renderListCard({ production, selectedGenreIds: [2] })

    const selectedGenre = screen.getByText('Tweede')
    const unselectedGenre = screen.getByText('Eerste')
    expect(selectedGenre.compareDocumentPosition(unselectedGenre)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    )
  })

  it('uses safe tag/genre fallbacks when optional translated fields are missing', () => {
    const production = baseProduction({
      tags: [
        {
          ...minimalTag(11, 'Display'),
          display_name: null,
          name: null,
          url_title: { nl: 'url-naam' },
        },
        {
          ...minimalTag(12, 'Display'),
          display_name: null,
          name: {},
          url_title: null,
          type: null as unknown as string,
        },
      ],
      genres: [
        { id: 9, type: 'primary', name: null, display_name: 'Genre fallback', vendor_id: null },
      ],
    })

    renderListCard({ production })

    expect(screen.getByText('url-naam')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('Genre fallback')).toBeInTheDocument()
  })

  it('does not render nested anchors for chips inside the production card link', () => {
    const production = baseProduction({
      tags: [minimalTag(11, 'Reeks')],
      genres: [minimalGenre(22, 'Genre')],
    })

    renderListCard({ production, selectedGenreIds: undefined, selectedTagIds: undefined })

    const cardLink = screen.getByRole('link', { name: /Voorstelling/ })

    expect(screen.getByText('Reeks')).toBeInTheDocument()
    expect(screen.getByText('Genre')).toBeInTheDocument()
    expect(cardLink.querySelectorAll('a')).toHaveLength(0)
  })

  it('ignores unrelated keyboard keys for card navigation', () => {
    const production = baseProduction({ id: 9 })
    renderListCard({ production })

    const card = screen.getByRole('link', { name: /Voorstelling/ })
    fireEvent.keyDown(card, { key: 'Escape' })

    expect(card).toHaveAttribute('href', toLocalizedPath('/productions/9', 'nl'))
  })

  it('does not render a genre row when there are no genres', () => {
    const production = baseProduction({ genres: [] })
    renderListCard({ production })

    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
  })

  it('renders a genre chip when display_name is null but translated name exists', () => {
    const production = baseProduction({
      genres: [
        {
          id: 1,
          type: 'primary',
          name: { nl: 'Zonder display' },
          display_name: null,
          vendor_id: null,
        },
      ],
    })
    renderListCard({ production })

    expect(screen.queryByText('Zonder display')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
  })

  it('links the full card to the production detail route', () => {
    const production = baseProduction({ id: 42 })
    renderListCard({ production })

    expect(screen.getByRole('link', { name: /Voorstelling/ })).toHaveAttribute(
      'href',
      toLocalizedPath('/productions/42', 'nl'),
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
      toLocalizedPath('/productions/1', 'en'),
    )
    expect(screen.getByRole('img', { name: 'Production' })).toBeInTheDocument()
  })

  it('formats the date range for the active locale (en)', async () => {
    await i18n.changeLanguage('en')
    const production = baseProduction({
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-20T20:00:00.000Z',
    })
    renderListCard({ production })

    expect(screen.getByText(/Mar/)).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('translates genre chip labels for the active locale instead of always using display_name', async () => {
    await i18n.changeLanguage('en')

    const production = baseProduction({
      genres: [
        {
          id: 9,
          type: 'primary',
          name: { nl: 'Dans', en: 'Dance' },
          display_name: 'Dans',
          vendor_id: null,
        },
      ],
    })

    renderListCard({ production })

    expect(screen.getByText('Dance')).toBeInTheDocument()
    expect(screen.queryByText(/^Dans$/)).not.toBeInTheDocument()
  })

  it('translates series tag chip labels for the active locale', async () => {
    await i18n.changeLanguage('en')

    const production = baseProduction({
      tags: [minimalTag(12, 'Reeks', 'Series')],
    })

    renderListCard({ production })

    expect(screen.getByText('Series')).toBeInTheDocument()
    expect(screen.queryByText(/^Reeks$/)).not.toBeInTheDocument()
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

  it('does not fire onGenreClick — chips navigate rather than toggle filters', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(1, 'A'), minimalGenre(2, 'B')],
    })
    renderListCard({ production, onGenreClick })

    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('B')).toBeInTheDocument()
    expect(onGenreClick).not.toHaveBeenCalled()
  })

  it('card link navigates to detail route; genre chips navigate to homepage filter', () => {
    const onGenreClick = jest.fn()
    const production = baseProduction({
      genres: [minimalGenre(5, 'Chip')],
    })
    renderListCard({ production, onGenreClick })

    expect(screen.getByText('Chip')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Filter (op|by)/ })).not.toBeInTheDocument()
    expect(onGenreClick).not.toHaveBeenCalled()

    const cardLink = screen.getByRole('link', { name: /Voorstelling/ })
    expect(cardLink).toHaveAttribute('href', toLocalizedPath('/productions/1', 'nl'))
  })
})
