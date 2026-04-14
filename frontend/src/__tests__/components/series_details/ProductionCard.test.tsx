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
      { id: 3, name: '3 dagen', labels: { nl: '3 dagen', en: '3 days' } },
    ],
  }

  const renderCard = (props = defaultProps) => {
    return render(
      <MemoryRouter>
        <ProductionCard {...props} />
      </MemoryRouter>,
    )
  }

  it('renders title, meta, description and tags', () => {
    renderCard()

    expect(screen.getByText(defaultProps.title)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.meta)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()

    defaultProps.tags.forEach((tag) => {
      expect(screen.getByText(tag.name)).toBeInTheDocument()
    })
  })

  it('renders all provided tags as clickable chips', () => {
    const tags = [
      { id: 1, name: 'Festival', labels: { nl: 'Festival', en: 'Festival' } },
      { id: 2, name: 'Live visuals', labels: { nl: 'Live visuals', en: 'Live visuals' } },
      { id: 3, name: '25 artiesten', labels: { nl: '25 artiesten', en: '25 artists' } },
      { id: 4, name: '3 dagen', labels: { nl: '3 dagen', en: '3 days' } },
    ]

    renderCard({
      title: 'VIDEODROOM 2023',
      meta: '10e editie',
      description: 'Beschrijving',
      tags,
    })

    tags.forEach((tag) => {
      expect(screen.getByText(tag.name)).toBeInTheDocument()
    })

    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(tags.length)
    expect(links[0]).toHaveAttribute('href', '/series/1')
  })
})
