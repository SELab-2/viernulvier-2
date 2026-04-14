import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter } from 'react-router-dom'
import ProductionCard from '../../../components/series_details/ProductionCard'

describe('ProductionCard', () => {
  const defaultProps = {
    title: 'VIDEODROOM 2024',
    meta: '11e editie · 3–5 mei 2024',
    description: 'Een audiovisuele editie met live visuals en performances.',
    tags: [
      { id: 1, name: 'Festival', labels: { nl: 'Festival', en: 'Festival' } },
      { id: 2, name: 'Audiovisueel', labels: { nl: 'Audiovisueel', en: 'Audiovisual' } },
      { id: 3, name: 'Performance', labels: { nl: 'Performance', en: 'Performance' } },
    ],
  }

  const renderCard = (props = defaultProps) => {
    return render(
      <MemoryRouter>
        <ProductionCard {...props} />
      </MemoryRouter>,
    )
  }

  it('renders title, meta, description and genres', () => {
    renderCard()

    expect(screen.getByText(defaultProps.title)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.meta)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()

    defaultProps.tags.forEach((genre) => {
      expect(screen.getByText(genre.name)).toBeInTheDocument()
    })
  })

  it('renders all provided genres as chips', () => {
    const genres = [
      { id: 1, name: 'Festival', labels: { nl: 'Festival', en: 'Festival' } },
      { id: 2, name: 'Live visuals', labels: { nl: 'Live visuals', en: 'Live visuals' } },
      { id: 3, name: 'Audiovisueel', labels: { nl: 'Audiovisueel', en: 'Audiovisual' } },
      { id: 4, name: 'Performance', labels: { nl: 'Performance', en: 'Performance' } },
    ]

    renderCard({
      title: 'VIDEODROOM 2023',
      meta: '10e editie',
      description: 'Beschrijving',
      tags: genres,
    })

    genres.forEach((genre) => {
      expect(screen.getByText(genre.name)).toBeInTheDocument()
    })
  })
})
