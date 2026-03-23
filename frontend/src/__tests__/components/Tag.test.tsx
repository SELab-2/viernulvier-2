import { render, screen, fireEvent } from '@testing-library/react'
import Tag from '../../components/Tag'
// Mock useTranslation globally to avoid i18n warning and allow language switching
jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' } }),
}))
import { MemoryRouter } from 'react-router-dom'

// Mock useNavigate globally for all tests
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

describe('Tag component', () => {
  it('renders the tagName as label if no labels prop', () => {
    render(
      <MemoryRouter>
        <Tag tagName="test" />
      </MemoryRouter>,
    )
    expect(screen.getByText('test')).toBeInTheDocument()
  })

  it('renders the label for the current language if provided in labels', () => {
    render(
      <MemoryRouter>
        <Tag tagName="test" labels={{ nl: 'Test NL', en: 'Test EN' }} />
      </MemoryRouter>,
    )
    expect(screen.getByText('Test NL')).toBeInTheDocument()
  })

  it('calls onTagToggle when clicked in search context', () => {
    const onTagToggle = jest.fn()
    render(
      <MemoryRouter>
        <Tag tagName="test" onTagToggle={onTagToggle} context="search" />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(onTagToggle).toHaveBeenCalledWith('test')
  })

  it('navigates to series page in series context', () => {
    render(
      <MemoryRouter>
        <Tag tagName="reekstag" context="series" />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(mockNavigate).toHaveBeenCalledWith('/series/reekstag')
  })

  it('is always purple for series context', () => {
    render(
      <MemoryRouter>
        <Tag tagName="reekstag" context="series" />
      </MemoryRouter>,
    )
    const chip = screen.getByRole('button')
    expect(chip).toHaveStyle('background-color: #9333ea')
  })

  it('shows cross icon when selected', () => {
    render(
      <MemoryRouter>
        <Tag tagName="test" selected />
      </MemoryRouter>,
    )
    // The MUI CloseIcon has data-testid="CloseIcon"
    expect(screen.getByTestId('CloseIcon')).toBeInTheDocument()
  })
  afterEach(() => {
    mockNavigate.mockReset()
    jest.resetAllMocks()
  })
})
