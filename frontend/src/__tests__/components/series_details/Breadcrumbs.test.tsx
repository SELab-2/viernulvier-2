import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter } from 'react-router-dom'
import SeriesDetailsBreadcrumbs from '../../../components/series_details/Breadcrumbs'

describe('SeriesDetailsBreadcrumbs', () => {
  const renderBreadcrumbs = (items: { label: string; to?: string }[]) => {
    return render(
      <MemoryRouter>
        <SeriesDetailsBreadcrumbs items={items} />
      </MemoryRouter>,
    )
  }

  it('renders clickable links for all items except the last one', () => {
    renderBreadcrumbs([
      { label: 'Archief', to: '/' },
      { label: 'Reeksen', to: '/series' },
      { label: 'VIDEODROOM' },
    ])

    expect(screen.getByRole('link', { name: 'Archief' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Reeksen' })).toHaveAttribute('href', '/series')
    expect(screen.getByText('VIDEODROOM')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'VIDEODROOM' })).not.toBeInTheDocument()
  })

  it('renders an item without "to" as plain text even when it is not the last item', () => {
    renderBreadcrumbs([
      { label: 'Archief', to: '/' },
      { label: 'Tussenstap' },
      { label: 'VIDEODROOM' },
    ])

    expect(screen.getByRole('link', { name: 'Archief' })).toHaveAttribute('href', '/')
    expect(screen.getByText('Tussenstap')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Tussenstap' })).not.toBeInTheDocument()
    expect(screen.getByText('VIDEODROOM')).toBeInTheDocument()
  })

  it('renders the breadcrumb navigation container', () => {
    renderBreadcrumbs([
      { label: 'Archief', to: '/' },
      { label: 'Reeksen', to: '/series' },
      { label: 'VIDEODROOM' },
    ])

    expect(screen.getByLabelText('breadcrumb')).toBeInTheDocument()
  })
})
