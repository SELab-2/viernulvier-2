import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import i18n from '../../../../i18n'
import GenreAndTagChip from '../../../../shared/components/chips/GenreAndTagChip'
import { toLocalizedPath } from '../../../../utils/localizedRoutes'
import { getTranslatedRecord } from '../../../../utils/translations'

import type { ReactElement } from 'react'

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: {
      main: '#8224E3',
      contrastText: '#ffffff',
    },
  },
})

const baseGenre = (overrides?: {
  id?: number
  name?: Record<string, string> | null
  displayName?: string | null
  language?: string
}) => {
  const id = overrides?.id ?? 7
  const nameRecord =
    overrides && Object.prototype.hasOwnProperty.call(overrides, 'name')
      ? (overrides.name ?? null)
      : { nl: 'Theater', en: 'Theatre' }
  const displayName = overrides?.displayName ?? null
  const language = overrides?.language ?? 'nl'

  return {
    id,
    label: getTranslatedRecord(nameRecord, language, displayName),
  }
}

const renderChip = (ui: ReactElement) =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={accentTheme}>{ui}</ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

beforeEach(() => {
  void i18n.changeLanguage('nl')
})

const LocationEcho = () => {
  const location = useLocation()

  return <div>{`${location.pathname}${location.search}`}</div>
}

afterEach(() => {
  void i18n.changeLanguage('nl')
})

describe('GenreAndTagChip in genre mode', () => {
  it('renders translated genre name and filter aria-label', () => {
    const genre = baseGenre({ language: 'nl' })
    const onToggle = jest.fn()
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
        onToggle={onToggle}
      />,
    )

    expect(screen.getByText('Theater')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter op Theater' })).toBeInTheDocument()
  })

  it('uses English copy when the active language is en', async () => {
    await i18n.changeLanguage('en')
    const genre = baseGenre({ language: 'en' })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
      />,
    )

    expect(screen.getByText('Theatre')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter by Theatre' })).toBeInTheDocument()
  })

  it('sets aria-pressed when the genre id is selected', () => {
    const genre = baseGenre({ language: 'nl' })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
        selected
      />,
    )

    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true')
  })

  it('sets aria-pressed false when not selected', () => {
    const genre = baseGenre({ language: 'nl' })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
      />,
    )

    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'false')
  })

  it('calls onToggle with genre id when pressed', () => {
    const onToggle = jest.fn()
    const genre = baseGenre({ id: 42, language: 'nl' })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
        onToggle={onToggle}
      />,
    )

    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledTimes(1)
    expect(onToggle).toHaveBeenCalledWith(42, 'genre')
  })

  it('uses display_name when name has no translation for the active language', () => {
    const genre = baseGenre({
      name: { en: 'Only English' },
      displayName: 'Weergavenaam',
      language: 'nl',
    })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
      />,
    )

    expect(screen.getByText('Weergavenaam')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter op Weergavenaam' })).toBeInTheDocument()
  })

  it('uses display_name when name is null', () => {
    const genre = baseGenre({
      name: null,
      displayName: 'Alleen display',
      language: 'nl',
    })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
      />,
    )

    expect(screen.getByText('Alleen display')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter op Alleen display' })).toBeInTheDocument()
  })

  it('fires onToggle when activated with the keyboard', async () => {
    const user = userEvent.setup()
    const onToggle = jest.fn()
    const genre = baseGenre({ id: 99, language: 'nl' })
    renderChip(
      <GenreAndTagChip
        name={genre.label}
        labels={{}}
        chipType="genre"
        context="search"
        id={genre.id}
        onToggle={onToggle}
      />,
    )

    const button = screen.getByRole('button')
    await user.tab()
    expect(button).toHaveFocus()

    await user.keyboard('{Enter}')
    expect(onToggle).toHaveBeenCalledWith(99, 'genre')

    onToggle.mockClear()
    await user.keyboard(' ')
    expect(onToggle).toHaveBeenCalledWith(99, 'genre')
  })

  it('navigates to the archive with a genre id in description context', () => {
    renderChip(
      <GenreAndTagChip name="Dans" labels={{}} chipType="genre" id={7} context="description" />,
    )

    expect(screen.getByRole('link')).toHaveAttribute(
      'href',
      `${toLocalizedPath('/archive', 'nl')}?g=7`,
    )
  })

  it('navigates to the archive when a description chip is clicked', () => {
    render(
      <MemoryRouter initialEntries={['/nl/producties/7']}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={accentTheme}>
            <Routes>
              <Route
                path="/nl/producties/7"
                element={
                  <GenreAndTagChip
                    name="Dans"
                    labels={{}}
                    chipType="genre"
                    id={7}
                    context="description"
                  />
                }
              />
              <Route path="/nl/archief" element={<LocationEcho />} />
            </Routes>
          </ThemeProvider>
        </I18nextProvider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('link', { name: 'Dans' }))

    expect(screen.getByText('/nl/archief?g=7')).toBeInTheDocument()
  })

  it('clears page when merging filters in description context with disableLink', () => {
    render(
      <MemoryRouter initialEntries={['/nl/archief?g=5&p=100']}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={accentTheme}>
            <Routes>
              <Route
                path="/nl/archief"
                element={
                  <>
                    <GenreAndTagChip
                      name="Dans"
                      labels={{}}
                      chipType="genre"
                      id={7}
                      context="description"
                      disableLink
                    />
                    <LocationEcho />
                  </>
                }
              />
            </Routes>
          </ThemeProvider>
        </I18nextProvider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Dans' }))

    expect(screen.getByText('/nl/archief?g=5-7')).toBeInTheDocument()
  })

  it('renders static context as non-clickable', () => {
    renderChip(<GenreAndTagChip name="Statisch" labels={{}} id={7} context="static" />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByText('Statisch')).toBeInTheDocument()
  })
})

describe('GenreAndTagChip in series tag mode', () => {
  it('calls onToggle with series tag id and type in search context', () => {
    const onToggle = jest.fn()

    renderChip(
      <GenreAndTagChip
        name="Reekstag"
        labels={{}}
        chipType="seriesTag"
        context="search"
        id={12}
        onToggle={onToggle}
      />,
    )

    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledWith(12, 'seriesTag')
  })

  it('shows selected close icon in search context', () => {
    renderChip(
      <GenreAndTagChip
        name="Reekstag"
        labels={{}}
        chipType="seriesTag"
        context="search"
        id={12}
        selected
      />,
    )

    expect(screen.getByTestId('CloseIcon')).toBeInTheDocument()
  })

  it('navigates to the archive with a tag id in description context', () => {
    renderChip(
      <GenreAndTagChip
        name="Reekstag"
        labels={{}}
        chipType="seriesTag"
        id={12}
        context="description"
      />,
    )

    expect(screen.getByRole('link')).toHaveAttribute(
      'href',
      `${toLocalizedPath('/archive', 'nl')}?t=12`,
    )
  })

  it('navigates to the series page in series context', () => {
    renderChip(
      <GenreAndTagChip name="reekstag" labels={{}} chipType="seriesTag" id={12} context="series" />,
    )

    expect(screen.getByRole('link')).toHaveAttribute('href', toLocalizedPath('/series/12', 'nl'))
  })

  it('navigates to the series page when a series chip is clicked', () => {
    render(
      <MemoryRouter initialEntries={['/nl/producties/7']}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={accentTheme}>
            <Routes>
              <Route
                path="/nl/producties/7"
                element={
                  <GenreAndTagChip
                    name="reekstag"
                    labels={{}}
                    chipType="seriesTag"
                    id={12}
                    context="series"
                  />
                }
              />
              <Route path="/nl/reeksen/12" element={<LocationEcho />} />
            </Routes>
          </ThemeProvider>
        </I18nextProvider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('link', { name: 'reekstag' }))

    expect(screen.getByText('/nl/reeksen/12')).toBeInTheDocument()
  })

  it('gives static chips a colored border', () => {
    const { container } = renderChip(
      <GenreAndTagChip name="Statisch" labels={{}} id={7} context="static" />,
    )

    const chip = container.querySelector('.MuiChip-root')
    expect(chip).toHaveStyle({ borderColor: '#8224E3' })
  })
})
