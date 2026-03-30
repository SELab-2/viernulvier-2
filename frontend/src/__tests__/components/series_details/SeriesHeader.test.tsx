import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import SeriesHeader from '../../../components/series_details/SeriesHeader'

describe('SeriesHeader', () => {
  it('renders name, description and badge', () => {
    render(
      <SeriesHeader
        name="VIDEODROOM"
        description="Het audiovisuele festival dat de grenzen tussen muziek, beeld en performance verkent."
        badge="Terugkerende reeks"
      />,
    )

    expect(screen.getByText('VIDEODROOM')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Het audiovisuele festival dat de grenzen tussen muziek, beeld en performance verkent.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Terugkerende reeks')).toBeInTheDocument()
  })

  it('renders exactly one heading-like title text', () => {
    render(<SeriesHeader name="VIDEODROOM" description="Beschrijving" badge="Recurring series" />)

    expect(screen.getByText('VIDEODROOM')).toBeInTheDocument()
    expect(screen.getByText('Beschrijving')).toBeInTheDocument()
    expect(screen.getByText('Recurring series')).toBeInTheDocument()
  })
})
