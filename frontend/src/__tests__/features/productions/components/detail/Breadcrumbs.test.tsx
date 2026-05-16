import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import Breadcrumbs from '../../../../../features/productions/components/detail/Breadcrumbs'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (_k: string, d: string) => d }),
}))

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

afterEach(() => {
  mockNavigate.mockReset()
  jest.clearAllMocks()
})

describe('Breadcrumbs component', () => {
  it('renders items and navigates when item has to', () => {
    render(
      <MemoryRouter>
        <Breadcrumbs
          items={[
            { label: 'Home', to: '/home' },
            { label: 'Production', translationKey: 'productions.detail.title' },
          ]}
          separator=" > "
        />
      </MemoryRouter>,
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Production')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Home'))
    expect(mockNavigate).toHaveBeenCalledWith('/nl/home')
  })

  it('does not navigate for item without link when not last item', () => {
    render(
      <MemoryRouter>
        <Breadcrumbs items={[{ label: 'NoDestination' }, { label: 'Last' }]} />
      </MemoryRouter>,
    )

    const button = screen.getByRole('button', { name: 'NoDestination' })
    expect(button).toBeDisabled()
    fireEvent.click(button)
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('renders disabled button when to is absent', () => {
    render(
      <MemoryRouter>
        <Breadcrumbs items={[{ label: 'NoLink' }, { label: 'Last' }]} />
      </MemoryRouter>,
    )

    const button = screen.getByRole('button', { name: /NoLink/i })
    expect(button).toBeDisabled()
    fireEvent.click(button)
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})
