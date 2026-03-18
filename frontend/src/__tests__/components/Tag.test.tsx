import { render, screen, fireEvent } from '@testing-library/react'
import Tag from '../../components/Tag'
import { MemoryRouter } from 'react-router-dom'

// Mock useNavigate globally for all tests
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

describe('Tag component', () => {
  it('renders the displayName', () => {
    render(
      <MemoryRouter>
        <Tag name="test" displayName="Test Tag" />
      </MemoryRouter>,
    )
    expect(screen.getByText('Test Tag')).toBeInTheDocument()
  })

  it('calls onTagToggle when clicked in search context', () => {
    const onTagToggle = jest.fn()
    render(
      <MemoryRouter>
        <Tag name="test" displayName="Test Tag" onTagToggle={onTagToggle} context="search" />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(onTagToggle).toHaveBeenCalledWith('test')
  })

  it('navigates to series page in series context', () => {
    render(
      <MemoryRouter>
        <Tag name="reekstag" displayName="Reeks" context="series" />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(mockNavigate).toHaveBeenCalledWith('/series/reekstag')
  })

  it('is always purple for series context', () => {
    render(
      <MemoryRouter>
        <Tag name="reekstag" displayName="Reeks" context="series" />
      </MemoryRouter>,
    )
    const chip = screen.getByRole('button')
    expect(chip).toHaveStyle('background-color: #9333ea')
  })

  it('shows cross icon when selected', () => {
    render(
      <MemoryRouter>
        <Tag name="test" displayName="Test Tag" selected />
      </MemoryRouter>,
    )
    // The MUI CloseIcon has data-testid="CloseIcon"
    expect(screen.getByTestId('CloseIcon')).toBeInTheDocument()
  })
  afterEach(() => {
    mockNavigate.mockReset()
  })
})
