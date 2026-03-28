import { render, screen, fireEvent } from '@testing-library/react'
import EventList from '../../../components/production/EventList'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (k: string, d: string) => d }),
}))

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

afterEach(() => jest.clearAllMocks())

describe('EventList component', () => {
  it('renders no events text when array is empty', () => {
    render(<EventList events={[]} />)
    expect(screen.getByText('Geen geplande events.')).toBeInTheDocument()
  })

  it('renders event with price and toggles expansion', () => {
    const events = [
      {
        id: 1,
        starts_at: '2025-08-01T20:00:00Z',
        ends_at: '2025-08-01T22:00:00Z',
        hall_display: 'Main hall',
        prices: [{ id: 8, price_display: 'VIP', amount: 20, available: 12 }],
      },
    ]

    render(<EventList events={events} />)

    expect(screen.getByText(/Main hall/i)).toBeInTheDocument()
    expect(screen.getByText(/20\.00/)).toBeInTheDocument()

    const toggle = screen.getByRole('button', { name: /Prijzen tonen/i })
    fireEvent.click(toggle)

    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Prijs')).toBeInTheDocument()
    expect(screen.getByText('Beschikbaar')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Prijzen verbergen/i }))
  })

  it('renders placeholder values when start/hall/prices are missing', () => {
    const events = [{ id: 2, starts_at: null, hall_display: null, prices: [] }]

    render(<EventList events={events} />)

    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.queryByText(/Prijzen tonen/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Main hall/i)).not.toBeInTheDocument()
  })

  it('uses fallback duration and unavailable marker for event with missing ends_at and available', () => {
    const events = [
      {
        id: 3,
        starts_at: '2025-08-05T20:00:00Z',
        hall_display: 'Fallback hall',
        prices: [{ id: 9, price_display: 'Standard', amount: 15 }],
      },
    ]

    render(<EventList events={events} />)

    expect(screen.queryByText(/ – /)).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /Prijzen tonen/i }))
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
