import { render, screen } from '@testing-library/react'

import '@testing-library/jest-dom'
import SeriesStats from '../../../../features/series/components/SeriesStats'

describe('SeriesStats', () => {
  const stats = [
    { value: '11', label: 'Edities' },
    { value: '2013–2024', label: 'Periode' },
    { value: 'Festival', label: 'Type' },
  ]

  it('renders all stat values and labels', () => {
    render(<SeriesStats stats={stats} />)

    stats.forEach((stat) => {
      expect(screen.getByText(stat.value)).toBeInTheDocument()
      expect(screen.getByText(stat.label)).toBeInTheDocument()
    })
  })

  it('renders the correct number of stat labels', () => {
    render(<SeriesStats stats={stats} />)

    expect(screen.getAllByText(/Edities|Periode|Type/)).toHaveLength(3)
  })
})
