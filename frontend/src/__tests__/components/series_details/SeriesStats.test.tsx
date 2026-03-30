import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import SeriesStats from '../../../components/series_details/SeriesStats'

describe('SeriesStats', () => {
  it('renders all stats values and labels', () => {
    render(
      <SeriesStats
        stats={[
          { value: '11', label: 'Edities' },
          { value: '2013–2024', label: 'Periode' },
          { value: '150+', label: 'Artiesten' },
        ]}
      />,
    )

    expect(screen.getByText('11')).toBeInTheDocument()
    expect(screen.getByText('Edities')).toBeInTheDocument()

    expect(screen.getByText('2013–2024')).toBeInTheDocument()
    expect(screen.getByText('Periode')).toBeInTheDocument()

    expect(screen.getByText('150+')).toBeInTheDocument()
    expect(screen.getByText('Artiesten')).toBeInTheDocument()
  })

  it('renders the correct number of stat labels', () => {
    const stats = [
      { value: '11', label: 'Edities' },
      { value: '2013–2024', label: 'Periode' },
      { value: '150+', label: 'Artiesten' },
    ]

    render(<SeriesStats stats={stats} />)

    stats.forEach((stat) => {
      expect(screen.getByText(stat.value)).toBeInTheDocument()
      expect(screen.getByText(stat.label)).toBeInTheDocument()
    })
  })
})
