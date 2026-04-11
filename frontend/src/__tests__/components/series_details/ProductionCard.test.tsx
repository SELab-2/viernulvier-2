import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import i18n from '../../../i18n'
import ProductionCard from '../../../components/series_details/ProductionCard'
import type { Tag } from '../../../types/Tags'

describe('ProductionCard', () => {
  const baseTags: Tag[] = [
    {
      id: 1,
      url: 'http://example.com/tag/1',
      source: 'internal',
      source_type: 'tag',
      type: 'Festival',
      is_external: false,
      is_enabled: true,
      display_name: 'Festival',
      display_short_description: null,
      display_url_title: null,
      name: { nl: 'Festival', en: 'Festival' },
      short_description: null,
      url_title: null,
    },
    {
      id: 2,
      url: 'http://example.com/tag/2',
      source: 'internal',
      source_type: 'tag',
      type: 'Audiovisueel',
      is_external: false,
      is_enabled: true,
      display_name: 'Audiovisueel',
      display_short_description: null,
      display_url_title: null,
      name: { nl: 'Audiovisueel', en: 'Audiovisual' },
      short_description: null,
      url_title: null,
    },
  ]

  const defaultProps = {
    title: 'VIDEODROOM 2024',
    meta: '11e editie · 3–5 mei 2024',
    description: 'Een audiovisuele editie met live visuals en performances.',
    tags: baseTags,
  }

  const renderCard = (props = defaultProps) => {
    return render(
      <MemoryRouter>
        <I18nextProvider i18n={i18n}>
          <ProductionCard {...props} />
        </I18nextProvider>
      </MemoryRouter>,
    )
  }

  it('renders title, meta, description and tags', () => {
    renderCard()

    expect(screen.getByText(defaultProps.title)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.meta)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()

    // Tags should display with translated names
    expect(screen.getByText('Festival')).toBeInTheDocument()
    expect(screen.getByText('Audiovisueel')).toBeInTheDocument()
  })

  it('renders all provided tags as clickable chips', () => {
    const tags: Tag[] = [
      {
        id: 3,
        url: 'http://example.com/tag/3',
        source: 'internal',
        source_type: 'tag',
        type: 'LiveVisuals',
        is_external: false,
        is_enabled: true,
        display_name: 'Live visuals',
        display_short_description: null,
        display_url_title: null,
        name: { nl: 'Live visuals', en: 'Live visuals' },
        short_description: null,
        url_title: null,
      },
    ]

    renderCard({
      title: 'VIDEODROOM 2023',
      meta: '10e editie',
      description: 'Beschrijving',
      tags,
    })

    expect(screen.getByText('Live visuals')).toBeInTheDocument()
  })
})
