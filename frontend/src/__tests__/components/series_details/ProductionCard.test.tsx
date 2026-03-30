import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ProductionCard from '../../../components/series_details/ProductionCard'

describe('ProductionCard', () => {
  it('renders title, meta, description, image and tags', () => {
    render(
      <ProductionCard
        title="VIDEODROOM 2024"
        meta="11e editie · 3–5 mei 2024"
        description="Een audiovisuele editie met live visuals en performances."
        tags={['Festival', 'Audiovisueel', '3 dagen']}
        image="https://example.com/image.jpg"
      />,
    )

    expect(screen.getByText('VIDEODROOM 2024')).toBeInTheDocument()
    expect(screen.getByText('11e editie · 3–5 mei 2024')).toBeInTheDocument()
    expect(
      screen.getByText('Een audiovisuele editie met live visuals en performances.'),
    ).toBeInTheDocument()

    expect(screen.getByAltText('VIDEODROOM 2024')).toBeInTheDocument()

    expect(screen.getByText('Festival')).toBeInTheDocument()
    expect(screen.getByText('Audiovisueel')).toBeInTheDocument()
    expect(screen.getByText('3 dagen')).toBeInTheDocument()
  })

  it('renders all provided tags', () => {
    const tags = ['Festival', 'Live visuals', '25 artiesten', '3 dagen']

    render(
      <ProductionCard
        title="VIDEODROOM 2023"
        meta="10e editie"
        description="Beschrijving"
        tags={tags}
        image="https://example.com/image.jpg"
      />,
    )

    tags.forEach((tag) => {
      expect(screen.getByText(tag)).toBeInTheDocument()
    })
  })
})
