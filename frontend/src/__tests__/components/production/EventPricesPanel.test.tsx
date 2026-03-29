import { render, screen } from '@testing-library/react'
import type { Production } from '../../../types/Productions'
import type { Event } from '../../../types/Events'
import EventPricesPanel from '../../../components/production/EventPricesPanel'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'nl' },
    t: (key: string, d: string, opts?: { count?: number }) => {
      if (key === 'events.availableQuantity' && opts?.count != null) {
        return `${opts.count} beschikbaar`
      }
      return d
    },
  }),
}))

describe('EventPricesPanel', () => {
  const productionStub: Production = {
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

  it('renders localized hall name from hall.name first', () => {
    const production = {
      ...productionStub,
      events: [
        {
          id: 9,
          production: productionStub,
          production_display: 'Prod',
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
          ends_at: null,
          prices: [
            {
              id: 1,
              event: 9,
              price_rank: null,
              price_rank_display: null,
              price: null,
              price_display: 'VIP',
              amount: '18',
              available: 12,
            },
          ],
        } as Event,
      ],
    }

    render(<EventPricesPanel production={production} />)

    expect(screen.getByText('Hoofdzaal')).toBeInTheDocument()
    expect(screen.getByText('12 beschikbaar')).toBeInTheDocument()
  })

  it('falls back to hall_display when selected locale is not present', () => {
    const production = {
      ...productionStub,
      events: [
        {
          id: 10,
          production: productionStub,
          production_display: 'Prod',
          hall: {
            id: 1,
            space: null,
            seat_selection: false,
            open_seating: true,
            name: { en: 'Main hall' },
            display_name: 'Hall display',
            remark: null,
          },
          hall_display: 'Fallback hall',
          starts_at: '2025-08-01T20:00:00Z',
          ends_at: null,
          prices: [
            {
              id: 2,
              event: 10,
              price_rank: null,
              price_rank_display: null,
              price: null,
              price_display: 'Regular',
              amount: '15',
              available: 8,
            },
          ],
        } as Event,
      ],
    }

    render(<EventPricesPanel production={production} />)
    expect(screen.getByText('Fallback hall')).toBeInTheDocument()
    expect(screen.queryByText('Main hall')).not.toBeInTheDocument()
  })
})
