import { render, screen } from '@testing-library/react'

import '@testing-library/jest-dom'
import SeriesHeader from '../../../components/series_details/SeriesHeader'

describe('SeriesHeader', () => {
  const defaultProps = {
    name: 'VIDEODROOM',
    description:
      'Het audiovisuele festival dat de grenzen tussen muziek, beeld en performance verkent.',
  }

  it('renders name and description', () => {
    render(<SeriesHeader {...defaultProps} />)

    expect(screen.getByText(defaultProps.name)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()
  })

  it('renders the title as a heading', () => {
    render(<SeriesHeader name="VIDEODROOM" description="Beschrijving" />)

    expect(screen.getByRole('heading', { name: 'VIDEODROOM' })).toBeInTheDocument()
    expect(screen.getByText('Beschrijving')).toBeInTheDocument()
  })
})
