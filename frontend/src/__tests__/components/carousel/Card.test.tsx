import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Card from '../../../components/carousel/Card'

describe('Card', () => {
  it('renders the mockup-style media card and links when href is provided', () => {
    render(
      <MemoryRouter>
        <Card
          href="/productions/1"
          title="VIDEODROOM 2021"
          subtitle="9e editie · 7-9 mei 2021"
          imageSrc="https://example.com/image.jpg"
          imageAlt="VIDEODROOM 2021"
        />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: /VIDEODROOM 2021/i })).toBeInTheDocument()
    expect(screen.getByText('VIDEODROOM 2021')).toBeInTheDocument()
    expect(screen.getByText('9e editie · 7-9 mei 2021')).toBeInTheDocument()
    expect(screen.getByAltText('VIDEODROOM 2021')).toHaveAttribute(
      'src',
      'https://example.com/image.jpg',
    )
  })
})