import { MemoryRouter } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import RelatedProductions from '../../../components/production/RelatedProductions'
import type { ProductionRelated, RelatedProduction } from '../../../types/Productions'
import React from 'react'

const languageState = { current: 'nl' }

jest.mock('../../../components/carousel/Carousel', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

jest.mock('../../../components/carousel/Card', () => ({
  __esModule: true,
  default: ({ title, subtitle }: { title: string; subtitle?: string }) => (
    <article>
      <h3>{title}</h3>
      {subtitle ? <p>{subtitle}</p> : null}
    </article>
  ),
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
      expect(screen.getByText('Nederlands label')).toBeInTheDocument()
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
      expect(screen.getByText('English label')).toBeInTheDocument()
    })
  })
})
