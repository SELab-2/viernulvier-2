import { act, render, screen, waitFor } from '@testing-library/react'
import RelatedProductions from '../../../components/production/RelatedProductions'
import type { Tag } from '../../../types/Tags'

const getRelatedProductionsMock = jest.fn()
const languageState = { current: 'nl' }
let resolveFetch:
  | ((value: Array<[Tag, Array<{ id: number; title: Record<string, string>; artist_name: Record<string, string>; display_title: string | null; display_artist_name: string | null; media_gallery: { media_items: Array<{ type: string; crops: Array<{ name: string; image_url: string | null }> }> } }>]>) => void)
  | undefined

jest.mock('../../../utils/productions', () => ({
  getRelatedProductions: (...args: unknown[]) => getRelatedProductionsMock(...args),
}))

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
    getRelatedProductionsMock.mockReset()
    resolveFetch = undefined
    languageState.current = 'nl'
  })

  it('shows a skeleton while loading and does not refetch on language change', async () => {
    getRelatedProductionsMock.mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      }),
    )

    const tags: Tag[] = [
      {
        id: 1,
        url: '/tags/1',
        source: 'test',
        source_type: 'manual',
        type: 'genre',
        is_external: false,
        is_enabled: true,
        display_name: 'Huidig label',
        display_short_description: null,
        display_url_title: null,
        name: { nl: 'Nederlands label', en: 'English label' },
        short_description: null,
        url_title: null,
      },
    ]

    const production = {
      id: 99,
      title: { nl: 'Productie NL', en: 'Production EN' },
      artist_name: { nl: 'Artiest NL', en: 'Artist EN' },
      display_title: 'Productie NL',
      display_artist_name: 'Artiest NL',
      media_gallery: {
        media_items: [
          {
            type: 'foto',
            crops: [{ name: 'hd_ready', image_url: 'https://example.com/image.jpg' }],
          },
        ],
      },
    }

    const { rerender } = render(<RelatedProductions tags={tags} currentProductionId={10} />)

    expect(screen.getByTestId('related-productions-skeleton')).toBeInTheDocument()

    await act(async () => {
      resolveFetch?.([[tags[0], [production]]])
    })

    await waitFor(() => {
      expect(screen.getByText('Gerelateerde producties')).toBeInTheDocument()
      expect(screen.getByText('Nederlands label')).toBeInTheDocument()
      expect(screen.getByText('Productie NL')).toBeInTheDocument()
    })

    languageState.current = 'en'
    rerender(<RelatedProductions tags={tags} currentProductionId={10} />)

    await waitFor(() => {
      expect(screen.getByText('Related productions')).toBeInTheDocument()
      expect(screen.getByText('English label')).toBeInTheDocument()
      expect(getRelatedProductionsMock).toHaveBeenCalledTimes(1)
    })
  })
})