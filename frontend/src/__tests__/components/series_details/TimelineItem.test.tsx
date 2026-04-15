import { render, screen } from '@testing-library/react'

import '@testing-library/jest-dom'
import TimelineItem from '../../../components/series_details/TimelineItem'

describe('TimelineItem', () => {
  it('renders the year and child content', () => {
    render(
      <TimelineItem year="2024">
        <div>Timeline content</div>
      </TimelineItem>,
    )

    expect(screen.getByText('2024')).toBeInTheDocument()
    expect(screen.getByText('Timeline content')).toBeInTheDocument()
  })

  it('renders arbitrary React children', () => {
    render(
      <TimelineItem year="2023">
        <article>
          <h2>VIDEODROOM 2023</h2>
          <p>Festival edition</p>
        </article>
      </TimelineItem>,
    )

    expect(screen.getByText('2023')).toBeInTheDocument()
    expect(screen.getByText('VIDEODROOM 2023')).toBeInTheDocument()
    expect(screen.getByText('Festival edition')).toBeInTheDocument()
  })
})
