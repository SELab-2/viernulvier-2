import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import ProductionCard from '../../../components/series_details/ProductionCard'
import i18n from '../../../i18n'

describe('ProductionCard', () => {
  const defaultProps = {
    title: 'VIDEODROOM 2024',
    meta: '11e editie · 3–5 mei 2024',
    description: 'Een audiovisuele editie met live visuals en performances.',
    genres: [
      { id: 1, name: 'Audiovisueel', labels: { nl: 'Audiovisueel', en: 'Audiovisual' } },
      { id: 2, name: 'Performance', labels: { nl: 'Performance', en: 'Performance' } },
    ],
    seriesTags: [
      { id: 10, name: 'VIDEODROOM', labels: { nl: 'VIDEODROOM', en: 'VIDEODROOM' } },
      { id: 11, name: 'Festivalreeks', labels: { nl: 'Festivalreeks', en: 'Festival series' } },
    ],
  }

  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  const renderCard = (props = defaultProps) => {
    return render(
      <I18nextProvider i18n={i18n}>
        <MemoryRouter>
          <ProductionCard {...props} />
        </MemoryRouter>
      </I18nextProvider>,
    )
  }

  it('renders title, meta, description, genres and series tags', () => {
    renderCard()

    expect(screen.getByText(defaultProps.title)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.meta)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()

    defaultProps.genres.forEach((genre) => {
      expect(screen.getByText(genre.name)).toBeInTheDocument()
    })

    defaultProps.seriesTags.forEach((tag) => {
      expect(screen.getByText(tag.name)).toBeInTheDocument()
    })
  })

  it('renders genre chips and clickable series tag chips', () => {
    renderCard()

    expect(screen.getByText('Audiovisueel')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()

    const seriesLinks = screen.getAllByRole('link')
    expect(seriesLinks).toHaveLength(defaultProps.seriesTags.length)
    expect(seriesLinks[0]).toHaveAttribute('href', '/series/10')
    expect(seriesLinks[1]).toHaveAttribute('href', '/series/11')
  })

  it('renders only genres when no series tags are provided', () => {
    renderCard({
      title: 'VIDEODROOM 2023',
      meta: '10e editie',
      description: 'Beschrijving',
      genres: [
        { id: 1, name: 'Live visuals', labels: { nl: 'Live visuals', en: 'Live visuals' } },
        { id: 2, name: 'Experimenteel', labels: { nl: 'Experimenteel', en: 'Experimental' } },
      ],
      seriesTags: [],
    })

    expect(screen.getByText('Live visuals')).toBeInTheDocument()
    expect(screen.getByText('Experimenteel')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('renders only series tags when no genres are provided', () => {
    renderCard({
      title: 'VIDEODROOM 2022',
      meta: '9e editie',
      description: 'Beschrijving',
      genres: [],
      seriesTags: [
        { id: 30, name: 'Retrospectieve', labels: { nl: 'Retrospectieve', en: 'Retrospective' } },
      ],
    })

    expect(screen.getByText('Retrospectieve')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Retrospectieve' })).toHaveAttribute(
      'href',
      '/series/30',
    )
  })
})
