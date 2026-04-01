import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ProductionCard from '../../../components/series_details/ProductionCard'

describe('ProductionCard', () => {
  const defaultProps = {
    title: 'VIDEODROOM 2024',
    meta: '11e editie · 3–5 mei 2024',
    description: 'Een audiovisuele editie met live visuals en performances.',
    tags: ['Festival', 'Audiovisueel', '3 dagen'],
  }

  it('renders title, meta, description and tags', () => {
    render(<ProductionCard {...defaultProps} />)

    expect(screen.getByText(defaultProps.title)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.meta)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()

    defaultProps.tags.forEach((tag) => {
      expect(screen.getByText(tag)).toBeInTheDocument()
    })
  })

  it('renders all provided tags', () => {
    const tags = ['Festival', 'Live visuals', '25 artiesten', '3 dagen']

    render(
      <ProductionCard
        title="VIDEODROOM 2023"
        meta="10e editie"
        description="Beschrijving"
        tags={tags}
      />,
    )

    tags.forEach((tag) => {
      expect(screen.getByText(tag)).toBeInTheDocument()
    })
  })

  it('does not render an image', () => {
    render(<ProductionCard {...defaultProps} />)

    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })
})
