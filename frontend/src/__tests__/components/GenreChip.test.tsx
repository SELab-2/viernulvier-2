import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { I18nextProvider } from 'react-i18next'
import GenreChip from '../../components/GenreChip'
import i18n from '../../i18n'
import type { Genre } from '../../types/Genres'

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: {
      main: '#8224E3',
      contrastText: '#ffffff',
    },
  },
})

const baseGenre = (overrides: Partial<Genre> = {}): Genre => ({
  id: 7,
  type: 'primary',
  use_as: { id: 1, name: 'theatre' },
  name: { nl: 'Theater', en: 'Theatre' },
  display_name: null,
  vendor_id: null,
  ...overrides,
})

const renderChip = (ui: ReactElement) =>
  render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={accentTheme}>{ui}</ThemeProvider>
    </I18nextProvider>,
  )

beforeEach(() => {
  void i18n.changeLanguage('nl')
})

afterEach(() => {
  void i18n.changeLanguage('nl')
})

describe('GenreChip', () => {
  it('renders translated genre name and filter aria-label', () => {
    const onClick = jest.fn()
    renderChip(<GenreChip genre={baseGenre()} selectedIds={[]} onClick={onClick} />)

    expect(screen.getByText('Theater')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter op Theater' })).toBeInTheDocument()
  })

  it('uses English copy when the active language is en', async () => {
    const onClick = jest.fn()
    await i18n.changeLanguage('en')
    renderChip(<GenreChip genre={baseGenre()} selectedIds={[]} onClick={onClick} />)

    expect(screen.getByText('Theatre')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter by Theatre' })).toBeInTheDocument()
  })

  it('sets aria-pressed when the genre id is selected', () => {
    const onClick = jest.fn()
    renderChip(<GenreChip genre={baseGenre()} selectedIds={[7, 8]} onClick={onClick} />)

    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true')
  })

  it('sets aria-pressed false when not selected', () => {
    const onClick = jest.fn()
    renderChip(<GenreChip genre={baseGenre()} selectedIds={[99]} onClick={onClick} />)

    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'false')
  })

  it('calls onClick with genre id when pressed', () => {
    const onClick = jest.fn()
    renderChip(<GenreChip genre={baseGenre({ id: 42 })} selectedIds={[]} onClick={onClick} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
    expect(onClick).toHaveBeenCalledWith(42)
  })

  it('uses display_name when name has no translation for the active language', () => {
    const onClick = jest.fn()
    renderChip(
      <GenreChip
        genre={baseGenre({
          name: { en: 'Only English' },
          display_name: 'Weergavenaam',
        })}
        selectedIds={[]}
        onClick={onClick}
      />,
    )

    expect(screen.getByText('Weergavenaam')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter op Weergavenaam' })).toBeInTheDocument()
  })

  it('uses display_name when name is null', () => {
    const onClick = jest.fn()
    renderChip(
      <GenreChip
        genre={baseGenre({ name: null, display_name: 'Alleen display' })}
        selectedIds={[]}
        onClick={onClick}
      />,
    )

    expect(screen.getByText('Alleen display')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter op Alleen display' })).toBeInTheDocument()
  })

  it('fires onClick when activated with the keyboard', async () => {
    const user = userEvent.setup()
    const onClick = jest.fn()
    renderChip(<GenreChip genre={baseGenre({ id: 99 })} selectedIds={[]} onClick={onClick} />)

    const button = screen.getByRole('button')
    await user.tab()
    expect(button).toHaveFocus()

    await user.keyboard('{Enter}')
    expect(onClick).toHaveBeenCalledWith(99)

    onClick.mockClear()
    await user.keyboard(' ')
    expect(onClick).toHaveBeenCalledWith(99)
  })
})
