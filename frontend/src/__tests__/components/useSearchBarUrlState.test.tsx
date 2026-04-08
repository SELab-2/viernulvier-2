import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { useSearchBarUrlState } from '../../components/searchbar/useSearchBarUrlState'

const UrlStateHarness = () => {
  const location = useLocation()
  const { selectedGenreIds, selectedSeriesTagIds, toggleGenreId, toggleSeriesTagId } =
    useSearchBarUrlState({ isMobile: false })

  return (
    <div>
      <button onClick={() => toggleGenreId(7)}>ToggleGenre7</button>
      <button onClick={() => toggleSeriesTagId(12)}>ToggleTag12</button>
      <div data-testid="location-search">{location.search}</div>
      <div data-testid="selected-genres">{selectedGenreIds.join(',')}</div>
      <div data-testid="selected-tags">{selectedSeriesTagIds.join(',')}</div>
    </div>
  )
}

describe('useSearchBarUrlState', () => {
  it('parses compact params using the configured separator', () => {
    render(
      <MemoryRouter initialEntries={['/?g=7~8&t=12~13']}>
        <Routes>
          <Route path="/" element={<UrlStateHarness />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('selected-genres').textContent).toBe('7,8')
    expect(screen.getByTestId('selected-tags').textContent).toBe('12,13')
  })

  it('parses initial genres and tags from URL', () => {
    render(
      <MemoryRouter initialEntries={['/?g=7~8&t=12~13']}>
        <Routes>
          <Route path="/" element={<UrlStateHarness />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('selected-genres').textContent).toBe('7,8')
    expect(screen.getByTestId('selected-tags').textContent).toBe('12,13')
  })

  it('toggles genres and tags in URL params', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<UrlStateHarness />} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'ToggleGenre7' }))
    expect(screen.getByTestId('location-search').textContent).toContain('g=7')
    expect(screen.getByTestId('location-search').textContent).not.toContain('%2C')

    fireEvent.click(screen.getByRole('button', { name: 'ToggleTag12' }))
    expect(screen.getByTestId('location-search').textContent).toContain('t=12')

    fireEvent.click(screen.getByRole('button', { name: 'ToggleGenre7' }))
    expect(screen.getByTestId('location-search').textContent).not.toContain('g=7')
  })
})
