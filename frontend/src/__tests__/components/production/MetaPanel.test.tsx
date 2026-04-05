import { render, screen } from '@testing-library/react'
import type { Production } from '../../../types/Productions'
import MetaPanel from '../../../components/production/MetaPanel'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (_k: string, d: string) => d }),
}))

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

afterEach(() => jest.clearAllMocks())

describe('MetaPanel component', () => {
  const productionStub: Production = {
    id: 1,
    title: { nl: 'Titel' },
    display_title: 'Display titel',
    artist_name: { nl: 'Kunstenaar' },
    display_artist_name: 'Artist display',
    tagline: { nl: 'Tag' },
    description: { nl: 'Omschrijving' },
    teaser: { nl: 'Teaser' },
    media_gallery: { id: 0, name: null, media_items: [] },
    events: [
      {
        id: 1,
        production: null as unknown as Production,
        production_display: 'P1',
        hall: null,
        hall_display: 'Main hall',
        starts_at: '2025-08-01T20:00:00Z',
        ends_at: '2025-08-01T22:00:00Z',
        prices: [],
      },
    ],
    genres: [
      {
        id: 1,
        type: 'genre',
        use_as: { id: 1, name: 'main' },
        name: { nl: 'Drama' },
        display_name: 'Drama',
        vendor_id: null,
      },
    ],
    tags: [
      {
        id: 1,
        url: '',
        source: 'local',
        source_type: 'tag',
        type: 'tag',
        is_external: false,
        is_enabled: true,
        display_name: 'Tag1',
        display_short_description: null,
        display_url_title: null,
        name: null,
        short_description: null,
        url_title: null,
      },
    ],
    uit_database_theme: null,
    uit_database_type: { id: 1, name: 'Type' },
    performer_type: 'group',
    attendance_mode: 'offline',
    first_event_start: null,
    last_event_end: null,
  }

  it('renders production meta panel with production data', () => {
    render(<MetaPanel production={productionStub} />)

    expect(screen.getByText('Titel')).toBeInTheDocument()
    expect(screen.getByText('Tag')).toBeInTheDocument()
    expect(screen.getByText('Periode')).toBeInTheDocument()
    expect(screen.getByText('Locaties')).toBeInTheDocument()
    expect(screen.getByText('Genre')).toBeInTheDocument()
    expect(screen.getAllByText('Type').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Groep')).toBeInTheDocument()
    expect(screen.getByText('Fysiek')).toBeInTheDocument()
    expect(screen.getByText('Tag1')).toBeInTheDocument()
  })

  it('does not render empty fields and no tags section for empty production', () => {
    render(
      <MetaPanel
        production={{
          ...productionStub,
          title: {},
          display_title: 'Titel',
          tagline: {},
          artist_name: {},
          display_artist_name: '',
          events: [],
          genres: [],
          tags: [],
          uit_database_type: null,
          performer_type: '',
          attendance_mode: '',
        }}
      />,
    )

    expect(screen.getByText('Titel')).toBeInTheDocument()
    expect(screen.queryByText('Periode')).not.toBeInTheDocument()
    expect(screen.queryByText('Locaties')).not.toBeInTheDocument()
    expect(screen.queryByText('Genre')).not.toBeInTheDocument()
    expect(screen.queryByText('Type')).not.toBeInTheDocument()
    expect(screen.queryByText('Uitvoering')).not.toBeInTheDocument()
    expect(screen.queryByText('Aanwezigheid')).not.toBeInTheDocument()
  })

  it('renders solo/online labels when production has performer/attendance', () => {
    render(
      <MetaPanel
        production={{
          ...productionStub,
          title: {},
          display_title: 'Titel',
          artist_name: {},
          display_artist_name: '',
          tagline: {},
          performer_type: 'solo',
          attendance_mode: 'online',
          events: [],
          genres: [],
          tags: [],
          uit_database_type: null,
        }}
      />,
    )

    expect(screen.getByText('Titel')).toBeInTheDocument()
    expect(screen.getByText('Solo')).toBeInTheDocument()
    expect(screen.getByText('Online')).toBeInTheDocument()
  })
})
