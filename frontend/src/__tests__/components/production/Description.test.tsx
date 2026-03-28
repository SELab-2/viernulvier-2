import { render, screen } from '@testing-library/react'
import Description from '../../../components/production/Description'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (_k: string, d: string) => d }),
}))

jest.mock('../../../utils/SanitizeHtml', () => ({
  __esModule: true,
  default: (html: string) => html,
}))

describe('Description component', () => {
  it('renders teaser and description with sanitized HTML', () => {
    render(<Description teaser="<p>Teaser</p>" description="<p>Desc</p>" />)

    expect(screen.getByText('Teaser')).toBeInTheDocument()
    expect(screen.getByText('Desc')).toBeInTheDocument()
  })

  it('renders fallback text when description is empty', () => {
    render(<Description teaser="" description="" />)

    expect(screen.getByText('No description available.')).toBeInTheDocument()
  })
})
