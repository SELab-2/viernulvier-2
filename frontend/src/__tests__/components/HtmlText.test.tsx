import { render, screen } from '@testing-library/react'

import HtmlText from '../../shared/components/HtmlText'

describe('HtmlText', () => {
  it('renders sanitized html content', () => {
    const { container } = render(<HtmlText html="<p>Hello <strong>world</strong></p>" />)

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(container.querySelector('strong')).toHaveTextContent('world')
  })

  it('renders a fallback React element as-is when html is empty', () => {
    render(<HtmlText html="  " fallback={<span data-testid="fallback">No content</span>} />)

    expect(screen.getByTestId('fallback')).toHaveTextContent('No content')
  })

  it('wraps a text fallback in typography when html is empty', () => {
    render(<HtmlText html="" fallback="No description" variant="body2" />)

    expect(screen.getByText('No description')).toBeInTheDocument()
  })

  it('renders nothing when html and fallback are empty', () => {
    const { container } = render(<HtmlText html="" />)

    expect(container).toBeEmptyDOMElement()
  })
})
