import { render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import RelatedProductions from '../../../../../features/productions/components/detail/RelatedProductions'

import type { ProductionRelated, RelatedProduction } from '../../../../../types/Productions'

const languageState = { current: 'nl' }

jest.mock('../../../../../shared/components/Carousel', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: languageState.current },
    t: (key: string, fallback?: string) => {
      if (key === 'productions.detail.related') {
        return languageState.current === 'en' ? 'Related productions' : 'Gerelateerde producties'
      }

      return fallback ?? key
    },
  }),
}))

describe('RelatedProductions', () => {
  beforeEach(() => {
    languageState.current = 'nl'
  })

  it('renders related productions and updates labels on language change', async () => {
    const production = {
      id: 99,
      title: { nl: 'Productie NL', en: 'Production EN' },
      artist_name: { nl: 'Artiest NL', en: 'Artist EN' },
      display_title: 'Productie NL',
      display_artist_name: 'Artiest NL',
      media_gallery: {
        id: 123,
        name: '-',
        media_items: [
          {
            type: 'foto',
            crops: [{ name: 'hd_ready', image_url: 'https://example.com/image.jpg' }],
          },
        ],
      },
    } as unknown as RelatedProduction

    const related: ProductionRelated[] = [
      {
        tag: {
          id: 1,
          name: { nl: 'Nederlands label', en: 'English label' },
          display_name: 'Huidig label',
        },
        productions: [production],
      },
    ]

    const { rerender } = render(
      <MemoryRouter>
        <RelatedProductions related={related} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Gerelateerde producties')).toBeInTheDocument()
      expect(screen.getAllByText('Nederlands label').length).toBeGreaterThan(0)
      expect(screen.getByText('Productie NL')).toBeInTheDocument()
    })

    languageState.current = 'en'
    rerender(
      <MemoryRouter>
        <RelatedProductions related={related} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Related productions')).toBeInTheDocument()
      expect(screen.getAllByText('English label').length).toBeGreaterThan(0)
    })
  })

  it('shows timestamp and chips in related production cards when payload contains them', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    const production = {
      id: 100,
      title: { nl: 'Kaart met chips', en: 'Card with chips' },
      artist_name: { nl: 'Artiest', en: 'Artist' },
      display_title: 'Kaart met chips',
      display_artist_name: 'Artiest',
      first_event_start: '2026-03-20T18:30:00.000Z',
      last_event_end: '2026-03-20T20:00:00.000Z',
      tags: [
        {
          id: 11,
          url: 'https://example.com/tags/11',
          source: 'db',
          type: 'series',
          is_enabled: true,
          display_name: 'Festivalreeks',
          display_short_description: null,
          display_url_title: null,
          name: { nl: 'Festivalreeks', en: 'Festival series' },
          short_description: null,
          url_title: null,
        },
      ],
      genres: [
        {
          id: 2,
          type: 'primary',
          name: { nl: 'Muziek', en: 'Music' },
          display_name: 'Muziek',
          vendor_id: null,
        },
      ],
      media_gallery: {
        id: 123,
        name: '-',
        media_items: [
          {
            type: 'foto',
            crops: [{ name: 'hd_ready', image_url: 'https://example.com/image.jpg' }],
          },
        ],
      },
    } as unknown as RelatedProduction

    const related: ProductionRelated[] = [
      {
        tag: {
          id: 1,
          name: { nl: 'Nederlands label', en: 'English label' },
          display_name: 'Huidig label',
        },
        productions: [production],
      },
    ]

    try {
      render(
        <MemoryRouter>
          <RelatedProductions related={related} />
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getByText('Festivalreeks')).toBeInTheDocument()
        expect(screen.getByText('Muziek')).toBeInTheDocument()
        expect(screen.getByText(/2026/)).toBeInTheDocument()
      })

      expect(consoleErrorSpy).not.toHaveBeenCalled()
    } finally {
      consoleErrorSpy.mockRestore()
    }
  })

  it('falls back to grouped related tag when related productions have no tags or genres', async () => {
    const production = {
      id: 101,
      title: { nl: 'Zonder extra velden', en: 'Without extra fields' },
      artist_name: { nl: 'Artiest', en: 'Artist' },
      display_title: 'Zonder extra velden',
      display_artist_name: 'Artiest',
      first_event_start: null,
      last_event_end: '2026-03-20T20:00:00.000Z',
      media_gallery: {
        id: 123,
        name: '-',
        media_items: [
          {
            type: 'foto',
            crops: [{ name: 'hd_ready', image_url: 'https://example.com/image.jpg' }],
          },
        ],
      },
    } as unknown as RelatedProduction

    const related: ProductionRelated[] = [
      {
        tag: {
          id: 77,
          name: { nl: 'Hoofdtag', en: 'Main tag' },
          display_name: 'Hoofdtag',
        },
        productions: [production],
      },
    ]

    render(
      <MemoryRouter>
        <RelatedProductions related={related} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getAllByText('Hoofdtag').length).toBeGreaterThan(0)
      expect(screen.getByText(/2026/)).toBeInTheDocument()
    })
  })
})
