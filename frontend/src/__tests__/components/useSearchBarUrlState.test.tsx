import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import { useSearchBarUrlState } from '../../components/searchbar/useSearchBarUrlState'

type HarnessProps = {
  isMobile?: boolean
}

const Harness = ({ isMobile = false }: HarnessProps) => {
  const location = useLocation()
  const {
    attendanceMode,
    firstEventStartAfter,
    firstEventStartBefore,
    page,
    performerType,
    selectedGenreIds,
    selectedTagIds,
    searchValue,
    clearFilters,
    setAttendanceMode,
    setFirstEventStartAfter,
    setFirstEventStartBefore,
    setPage,
    setPerformerType,
    setSelectedGenreIds,
    setSelectedTagIds,
    setSearchValue,
    setSortDirection,
    setSortTarget,
    setViewMode,
  } = useSearchBarUrlState({ isMobile })

  return (
    <div>
      <div data-testid="page">{page}</div>
      <div data-testid="query">{searchValue}</div>
      <div data-testid="attendance-mode">{attendanceMode ?? ''}</div>
      <div data-testid="performer-type">{performerType ?? ''}</div>
      <div data-testid="start-after">{firstEventStartAfter}</div>
      <div data-testid="start-before">{firstEventStartBefore}</div>
      <div data-testid="genres">{selectedGenreIds.join(',')}</div>
      <div data-testid="tags">{selectedTagIds.join(',')}</div>
      <div data-testid="url-search">{location.search}</div>

      <button onClick={() => setPage(3)}>set-page-3</button>
      <button onClick={() => setPage(1)}>set-page-1</button>
      <button onClick={() => setPage(1.5)}>set-page-1-5</button>
      <button onClick={() => setSearchValue('romeo')}>set-query</button>
      <button onClick={() => setSearchValue('  romeo  ')}>set-query-whitespace</button>
      <button onClick={() => setSortTarget('name')}>sort-name</button>
      <button onClick={() => setSortDirection('asc')}>sort-asc</button>
      <button onClick={() => setViewMode('list')}>view-list</button>
      <button onClick={() => setAttendanceMode('online')}>attendance-online</button>
      <button onClick={() => setPerformerType('group')}>performer-group</button>
      <button onClick={() => setFirstEventStartAfter('2026-03-01')}>start-after</button>
      <button onClick={() => setFirstEventStartBefore('2026-03-31')}>start-before</button>
      <button onClick={() => setSelectedGenreIds([5, 9])}>genre-5-9</button>
      <button onClick={() => setSelectedTagIds([8, 12])}>tag-8-12</button>
      <button onClick={() => clearFilters()}>clear-filters</button>
    </div>
  )
}

const renderHarness = (initialEntry = '/?p=2', isMobile = false) => {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/" element={<Harness isMobile={isMobile} />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('useSearchBarUrlState pagination sync', () => {
  it('reads page from URL', () => {
    renderHarness('/?p=3')

    expect(screen.getByTestId('page')).toHaveTextContent('3')
  })

  it('falls back to page 1 when URL value is invalid', () => {
    renderHarness('/?p=abc')

    expect(screen.getByTestId('page')).toHaveTextContent('1')
  })

  it('writes page to URL when setPage is called', () => {
    renderHarness('/?q=hamlet')

    fireEvent.click(screen.getByText('set-page-3'))

    expect(screen.getByTestId('url-search')).toHaveTextContent('q=hamlet')
    expect(screen.getByTestId('url-search')).toHaveTextContent('p=3')
    expect(screen.getByTestId('page')).toHaveTextContent('3')
  })

  it('removes page query when selecting first page', () => {
    renderHarness('/?q=hamlet&p=3')

    fireEvent.click(screen.getByText('set-page-1'))

    expect(screen.getByTestId('url-search')).toHaveTextContent('?q=hamlet')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
    expect(screen.getByTestId('page')).toHaveTextContent('1')
  })

  it('resets to page 1 when search value changes', () => {
    renderHarness('/?p=4')

    fireEvent.click(screen.getByText('set-query'))

    expect(screen.getByTestId('query')).toHaveTextContent('romeo')
    expect(screen.getByTestId('url-search')).toHaveTextContent('?q=romeo')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
    expect(screen.getByTestId('page')).toHaveTextContent('1')
  })

  it('trims whitespace in search query values', () => {
    renderHarness('/?p=4')

    fireEvent.click(screen.getByText('set-query-whitespace'))

    expect(screen.getByTestId('query')).toHaveTextContent('romeo')
    expect(screen.getByTestId('url-search')).toHaveTextContent('?q=romeo')
  })

  it('resets to page 1 when sort changes and keeps page when view changes', () => {
    const { unmount } = renderHarness('/?p=6')

    fireEvent.click(screen.getByText('sort-name'))
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
    expect(screen.getByTestId('page')).toHaveTextContent('1')

    fireEvent.click(screen.getByText('sort-asc'))
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
    expect(screen.getByTestId('page')).toHaveTextContent('1')

    unmount()
    renderHarness('/?p=6')
    fireEvent.click(screen.getByText('view-list'))
    expect(screen.getByTestId('url-search')).toHaveTextContent('p=6')
    expect(screen.getByTestId('page')).toHaveTextContent('6')
  })

  it('does not encode p=1 when setting a non-integer page close to 1', () => {
    renderHarness('/?q=hamlet&p=3')

    fireEvent.click(screen.getByText('set-page-1-5'))

    expect(screen.getByTestId('url-search')).toHaveTextContent('?q=hamlet')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
    expect(screen.getByTestId('page')).toHaveTextContent('1')
  })

  it('reads production filter state from URL params', () => {
    renderHarness('/?am=on&pt=g&fa=2026-03-01&fb=2026-03-31&g=5-9&t=8-12')

    expect(screen.getByTestId('attendance-mode')).toHaveTextContent('online')
    expect(screen.getByTestId('performer-type')).toHaveTextContent('group')
    expect(screen.getByTestId('start-after')).toHaveTextContent('2026-03-01')
    expect(screen.getByTestId('start-before')).toHaveTextContent('2026-03-31')
    expect(screen.getByTestId('genres')).toHaveTextContent('5,9')
    expect(screen.getByTestId('tags')).toHaveTextContent('8,12')
  })

  it('resets page when production filters change and removes them when cleared', () => {
    renderHarness('/?q=hamlet&p=4')

    fireEvent.click(screen.getByText('attendance-online'))
    fireEvent.click(screen.getByText('performer-group'))
    fireEvent.click(screen.getByText('start-after'))
    fireEvent.click(screen.getByText('start-before'))
    fireEvent.click(screen.getByText('genre-5-9'))
    fireEvent.click(screen.getByText('tag-8-12'))

    expect(screen.getByTestId('url-search')).toHaveTextContent('q=hamlet')
    expect(screen.getByTestId('url-search')).toHaveTextContent('am=on')
    expect(screen.getByTestId('url-search')).toHaveTextContent('pt=g')
    expect(screen.getByTestId('url-search')).toHaveTextContent('fa=2026-03-01')
    expect(screen.getByTestId('url-search')).toHaveTextContent('fb=2026-03-31')
    expect(screen.getByTestId('url-search')).toHaveTextContent('g=5-9')
    expect(screen.getByTestId('url-search')).toHaveTextContent('t=8-12')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
    expect(screen.getByTestId('page')).toHaveTextContent('1')

    fireEvent.click(screen.getByText('clear-filters'))

    expect(screen.getByTestId('attendance-mode')).toHaveTextContent('')
    expect(screen.getByTestId('performer-type')).toHaveTextContent('')
    expect(screen.getByTestId('start-after')).toHaveTextContent('')
    expect(screen.getByTestId('start-before')).toHaveTextContent('')
    expect(screen.getByTestId('genres')).toHaveTextContent('')
    expect(screen.getByTestId('tags')).toHaveTextContent('')
    expect(screen.getByTestId('url-search')).toHaveTextContent('?q=hamlet')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('am=')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('pt=')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('fa=')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('fb=')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('g=')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('t=')
  })
})
