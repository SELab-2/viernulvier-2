import { render, screen, fireEvent } from '@testing-library/react'
import type { Event } from '../../../types/Events'
import type { Production } from '../../../types/Productions'
import EventList from '../../../components/production/EventList'

const mockI18n = { language: 'nl' }

const enTranslations: Record<string, string> = {
  'events.priceType': 'Type',
  'events.price': 'Price',
  'events.available': 'Available',
  'events.availableQuantity': '{{count}} available',
  'productions.detail.noEvents': 'No scheduled events.',
  'events.expandPrices': 'Show prices',
  'events.collapsePrices': 'Hide prices',
}

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: mockI18n,
    t: (key: string, defaultValue: string) =>
      mockI18n.language === 'en' ? enTranslations[key] || defaultValue : defaultValue,
  }),
}))

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

afterEach(() => jest.clearAllMocks())

const baseProductionStub: Production = {
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'solo',
  uit_database_theme: null,
  uit_database_type: null,
  display_title: null,
  display_artist_name: null,
  title: {},
  artist_name: {},
  tagline: {},
  teaser: {},
  description: {},
  tags: [],
  genres: [],
  media_gallery: { id: 0, name: null, media_items: [] },
  events: [],
}

const eventFactory = (overrides: Partial<Event>): Event => ({
  id: 1,
  production: { ...baseProductionStub },
  production_display: 'Production',
  hall: null,
  hall_display: null,
  starts_at: null,
  ends_at: null,
  prices: [],
  ...overrides,
})

describe('EventList component', () => {
  it('renders no events text when array is empty', () => {
    render(<EventList events={[]} />)
    expect(screen.getByText('Geen geplande events.')).toBeInTheDocument()
  })

  it('uses hall.name by language and falls back to hall_display only without extra value fallbacks', () => {
    const events = [
      eventFactory({
        id: 4,
        production: { ...baseProductionStub, id: 1 },
        production_display: 'Production 4',
        hall: {
          id: 1,
          space: null,
          seat_selection: false,
          open_seating: true,
          name: { nl: 'Hoofdzaal', en: 'Main hall' },
          display_name: 'Hall display',
          remark: null,
        },
        hall_display: 'Fallback hall',
        starts_at: '2025-08-01T20:00:00Z',
        ends_at: '2025-08-01T22:00:00Z',
        prices: [],
      }),
    ]

    render(<EventList events={events} />)

    expect(screen.getByText('Hoofdzaal')).toBeInTheDocument()
    expect(screen.queryByText('Hall display')).not.toBeInTheDocument()
    expect(screen.queryByText('Fallback hall')).not.toBeInTheDocument()
  })

  it('renders locale fallback to hall_display when hall.name locale missing', () => {
    const events = [
      eventFactory({
        id: 5,
        production: { ...baseProductionStub, id: 1 },
        production_display: 'Production 5',
        hall: {
          id: 1,
          space: null,
          seat_selection: false,
          open_seating: true,
          name: { en: 'Main hall only' },
          display_name: 'Hall display',
          remark: null,
        },
        hall_display: 'Fallback hall 2',
        starts_at: '2025-08-01T20:00:00Z',
        ends_at: '2025-08-01T22:00:00Z',
        prices: [],
      }),
    ]

    render(<EventList events={events} />)

    expect(screen.getByText('Fallback hall 2')).toBeInTheDocument()
    expect(screen.queryByText('Main hall only')).not.toBeInTheDocument()
  })

  it('renders event header labels via i18n for English', () => {
    mockI18n.language = 'en'
    const events = [
      eventFactory({
        id: 1,
        production: { ...baseProductionStub, id: 1 },
        production_display: 'Production 1',
        hall_display: 'Main hall',
        starts_at: '2025-08-01T20:00:00Z',
        ends_at: '2025-08-01T22:00:00Z',
        prices: [
          {
            id: 8,
            event: 1,
            price_rank: null,
            price_rank_display: null,
            price: null,
            price_display: 'VIP',
            amount: '20',
            available: 12,
          },
        ],
      }),
    ]

    render(<EventList events={events} />)

    fireEvent.click(screen.getByRole('button', { name: /Show prices|Prijzen tonen/i }))

    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Price')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
  })

  it('renders event with price and toggles expansion', () => {
    mockI18n.language = 'nl'
    const events = [
      eventFactory({
        id: 1,
        production: { ...baseProductionStub, id: 1 },
        production_display: 'Production 1',
        hall_display: 'Main hall',
        starts_at: '2025-08-01T20:00:00Z',
        ends_at: '2025-08-01T22:00:00Z',
        prices: [
          {
            id: 8,
            event: 1,
            price_rank: null,
            price_rank_display: null,
            price: null,
            price_display: 'VIP',
            amount: '20',
            available: 12,
          },
        ],
      }),
    ]

    render(<EventList events={events} />)

    expect(screen.getByText(/Main hall/i)).toBeInTheDocument()

    const toggle = screen.getByRole('button', { name: /Prijzen tonen/i })
    fireEvent.click(toggle)

    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Prijs')).toBeInTheDocument()
    expect(screen.getByText('Beschikbaar')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Prijzen verbergen/i }))
  })

  it('renders placeholder values when start/hall/prices are missing', () => {
    const events = [
      {
        id: 2,
        production: {
          id: 2,
          attendance_mode: 'offline',
          performer_type: 'solo',
          uit_database_theme: null,
          uit_database_type: null,
          display_title: null,
          display_artist_name: null,
          title: {},
          artist_name: {},
          tagline: {},
          teaser: {},
          description: {},
          tags: [],
          genres: [],
          media_gallery: { id: 0, name: null, media_items: [] },
          events: [],
        },
        production_display: 'Production 2',
        hall: null,
        hall_display: null,
        starts_at: null,
        ends_at: null,
        prices: [],
      },
    ] as unknown as Event[]

    render(<EventList events={events} />)

    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.queryByText(/Prijzen tonen/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Main hall/i)).not.toBeInTheDocument()
  })

  it('uses fallback duration and unavailable marker for event with missing ends_at and available', () => {
    const events = [
      {
        id: 3,
        production: {
          id: 3,
          attendance_mode: 'offline',
          performer_type: 'solo',
          uit_database_theme: null,
          uit_database_type: null,
          display_title: null,
          display_artist_name: null,
          title: {},
          artist_name: {},
          tagline: {},
          teaser: {},
          description: {},
          tags: [],
          genres: [],
          media_gallery: { id: 0, name: null, media_items: [] },
          events: [],
        },
        production_display: 'Production 3',
        hall: null,
        hall_display: 'Fallback hall',
        starts_at: '2025-08-05T20:00:00Z',
        ends_at: null,
        prices: [
          {
            id: 9,
            event: 3,
            price_rank: null,
            price_rank_display: null,
            price: null,
            price_display: 'Standard',
            amount: '15',
            available: 0,
          },
        ],
      },
    ] as unknown as Event[]

    render(<EventList events={events} />)

    expect(screen.queryByText(/ – /)).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /Prijzen tonen/i }))
    expect(screen.getByText('0')).toBeInTheDocument()
  })
})
