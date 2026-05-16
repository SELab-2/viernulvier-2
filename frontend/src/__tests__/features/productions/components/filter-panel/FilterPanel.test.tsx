import { ThemeProvider, createTheme } from '@mui/material/styles'
import { act, fireEvent, render, screen } from '@testing-library/react'
import React, { type ReactNode } from 'react'
import { I18nextProvider } from 'react-i18next'

import FilterPanel, {
  type FilterPanelProps,
} from '../../../../../features/productions/components/filter-panel/FilterPanel'
import i18n from '../../../../../i18n'

import type { Genre } from '../../../../../types/Genres'
import type { Tag } from '../../../../../types/Tags'

jest.mock('@mui/x-date-pickers/AdapterDayjs', () => ({
  AdapterDayjs: function AdapterDayjs() {
    return null
  },
}))

jest.mock('@mui/x-date-pickers/LocalizationProvider', () => ({
  LocalizationProvider: ({
    adapterLocale,
    children,
  }: {
    adapterLocale: string
    children: ReactNode
  }) => (
    <div data-testid="localization-provider" data-adapter-locale={adapterLocale}>
      {children}
    </div>
  ),
}))

jest.mock('@mui/x-date-pickers/DatePicker', () => ({
  DatePicker: ({
    label,
    value,
    onChange,
    onClose,
    slotProps,
  }: {
    label: string
    value: { isValid: () => boolean; format: (format: string) => string } | null
    onChange: (
      value: { isValid: () => boolean; format: (format: string) => string } | null,
      context: { validationError: string | null },
    ) => void
    onClose?: () => void
    slotProps?: {
      textField?: {
        onBlur?: () => void
        onKeyDown?: (event: { key: string }) => void
      }
    }
  }) => {
    const createMockDayValue = (rawValue: string) => ({
      isValid: () => !Number.isNaN(Date.parse(rawValue)),
      format: () => rawValue,
    })

    return (
      <div data-testid={`date-picker-${label}`}>
        <input
          aria-label={label}
          value={value?.isValid() ? value.format('YYYY-MM-DD') : ''}
          onChange={(event) => {
            const rawValue = event.target.value

            if (!rawValue) {
              onChange(null, { validationError: null })
              return
            }

            const parsed = createMockDayValue(rawValue)
            onChange(parsed, {
              validationError: parsed.isValid() ? null : 'invalidDate',
            })
          }}
          onBlur={() => slotProps?.textField?.onBlur?.()}
          onKeyDown={(event) => slotProps?.textField?.onKeyDown?.(event)}
        />
        <button
          type="button"
          onClick={() => {
            onChange(createMockDayValue('2026-07-15'), { validationError: null })
            onClose?.()
          }}
        >
          {`Pick ${label}`}
        </button>
        <button type="button" onClick={() => onClose?.()}>
          {`Close ${label}`}
        </button>
      </div>
    )
  },
}))

jest.mock('../../../../../shared/components/chips/GenreAndTagChip', () => ({
  __esModule: true,
  default: ({
    id,
    name,
    chipType,
    selected,
    onToggle,
  }: {
    id: number
    name: string
    chipType: 'genre' | 'seriesTag'
    selected?: boolean
    onToggle?: () => void
  }) => (
    <button
      type="button"
      data-testid={`chip-${chipType}-${String(id)}`}
      data-selected={selected ? 'true' : 'false'}
      onClick={onToggle}
    >
      {name}
    </button>
  ),
}))

const buildGenre = (overrides: Partial<Genre> = {}): Genre => ({
  id: overrides.id ?? 1,
  type: overrides.type ?? 'main',
  name: Object.prototype.hasOwnProperty.call(overrides, 'name')
    ? (overrides.name ?? null)
    : { nl: `Genre ${String(overrides.id ?? 1)}` },
  display_name: Object.prototype.hasOwnProperty.call(overrides, 'display_name')
    ? (overrides.display_name ?? null)
    : null,
  vendor_id: overrides.vendor_id ?? null,
})

const buildTag = (overrides: Partial<Tag> = {}): Tag => ({
  id: overrides.id ?? 1,
  url: overrides.url ?? `/api/v1/tags/${String(overrides.id ?? 1)}/`,
  source: overrides.source ?? 'manual',
  type: overrides.type ?? 'series',
  is_enabled: overrides.is_enabled ?? true,
  image: overrides.image ?? null,
  display_name: Object.prototype.hasOwnProperty.call(overrides, 'display_name')
    ? (overrides.display_name ?? null)
    : null,
  display_short_description: overrides.display_short_description ?? null,
  display_excerpt: overrides.display_excerpt ?? null,
  display_url_title: overrides.display_url_title ?? null,
  first_production_start: overrides.first_production_start ?? null,
  last_production_end: overrides.last_production_end ?? null,
  name: Object.prototype.hasOwnProperty.call(overrides, 'name')
    ? (overrides.name ?? null)
    : { nl: `Tag ${String(overrides.id ?? 1)}` },
  excerpt: overrides.excerpt ?? null,
  short_description: overrides.short_description ?? {},
  url_title: overrides.url_title ?? {},
})

const buildProps = (overrides: Partial<FilterPanelProps> = {}): FilterPanelProps => ({
  firstEventStartAfter: '',
  firstEventStartBefore: '',
  selectedGenreIds: [],
  selectedTagIds: [],
  genres: [],
  tags: [],
  onAttendanceModeToggle: jest.fn(),
  onPerformerTypeToggle: jest.fn(),
  onFirstEventStartAfterChange: jest.fn(),
  onFirstEventStartBeforeChange: jest.fn(),
  onGenreSelectionChange: jest.fn(),
  onTagSelectionChange: jest.fn(),
  onClearFilters: jest.fn(),
  ...overrides,
})

const renderPanel = (overrides: Partial<FilterPanelProps> = {}) => {
  const props = buildProps(overrides)

  return {
    props,
    ...renderWithProps(props),
  }
}

const renderWithProps = (props: FilterPanelProps) =>
  render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={createTheme()}>
        <FilterPanel {...props} />
      </ThemeProvider>
    </I18nextProvider>,
  )

const expandPerformerAndAttendanceFilterSections = () => {
  fireEvent.click(
    screen.getByRole('button', { name: i18n.t('productions.home.filters.performerType') }),
  )
  fireEvent.click(
    screen.getByRole('button', { name: i18n.t('productions.home.filters.attendanceMode') }),
  )
}

describe('FilterPanel', () => {
  beforeEach(async () => {
    jest.clearAllMocks()
    await i18n.changeLanguage('nl')
  })

  it('renders the default panel state with disabled clear action and nl date locale', () => {
    renderPanel()

    expandPerformerAndAttendanceFilterSections()

    expect(
      screen.getByRole('heading', { name: i18n.t('productions.home.filterPanelTitle') }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: i18n.t('productions.home.filters.clear') }),
    ).toBeDisabled()
    expect(screen.getByTestId('localization-provider')).toHaveAttribute('data-adapter-locale', 'nl')
    expect(
      screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.online') }),
    ).not.toBeChecked()
    expect(
      screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.group') }),
    ).not.toBeChecked()
  })

  it('enables clear and forwards checkbox toggles for active filters', () => {
    const { props } = renderPanel({
      attendanceMode: 'online',
      performerType: 'solo',
      selectedGenreIds: [3],
    })

    expandPerformerAndAttendanceFilterSections()

    expect(
      screen.getByRole('button', { name: i18n.t('productions.home.filters.clear') }),
    ).toBeEnabled()
    expect(
      screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.online') }),
    ).toBeChecked()
    expect(
      screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.solo') }),
    ).toBeChecked()

    fireEvent.click(screen.getByRole('button', { name: i18n.t('productions.home.filters.clear') }))
    fireEvent.click(
      screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.offline') }),
    )
    fireEvent.click(
      screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.online') }),
    )
    fireEvent.click(screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.group') }))
    fireEvent.click(screen.getByRole('checkbox', { name: i18n.t('productions.detail.meta.solo') }))

    expect(props.onClearFilters).toHaveBeenCalledTimes(1)
    expect(props.onAttendanceModeToggle).toHaveBeenNthCalledWith(1, 'offline')
    expect(props.onAttendanceModeToggle).toHaveBeenNthCalledWith(2, 'online')
    expect(props.onPerformerTypeToggle).toHaveBeenNthCalledWith(1, 'group')
    expect(props.onPerformerTypeToggle).toHaveBeenNthCalledWith(2, 'solo')
  })

  it('shows empty labels when no genres or tags resolve to a usable name', () => {
    renderPanel({
      genres: [buildGenre({ id: 1, name: {}, display_name: null })],
      tags: [buildTag({ id: 2, name: null, display_name: null })],
    })

    expect(screen.getByText(i18n.t('productions.home.filters.noGenres'))).toBeInTheDocument()
    expect(screen.getByText(i18n.t('productions.home.filters.noTags'))).toBeInTheDocument()
    expect(screen.queryByTestId('chip-genre-1')).not.toBeInTheDocument()
    expect(screen.queryByTestId('chip-seriesTag-2')).not.toBeInTheDocument()
  })

  it('resolves localized chip names from display name, exact match, partial match, and fallback values', async () => {
    await act(async () => {
      await i18n.changeLanguage('en-US')
    })

    renderPanel({
      genres: [
        buildGenre({ id: 1, display_name: 'Display Genre', name: { nl: 'Genre NL' } }),
        buildGenre({ id: 2, name: { 'en-US': 'Exact Genre', en: 'Genre EN' } }),
        buildGenre({ id: 3, name: { en: 'Partial Genre' } }),
        buildGenre({ id: 4, name: { fr: 'Fallback Genre' } }),
        buildGenre({ id: 5, name: null, display_name: 'Display Only Genre' }),
      ],
      tags: [
        buildTag({ id: 11, display_name: 'Display Tag', name: { nl: 'Tag NL' } }),
        buildTag({ id: 12, name: { en: 'Partial Tag' } }),
      ],
    })

    expect(screen.getByTestId('localization-provider')).toHaveAttribute('data-adapter-locale', 'en')
    expect(screen.getByTestId('chip-genre-1')).toHaveTextContent('Display Genre')
    expect(screen.getByTestId('chip-genre-2')).toHaveTextContent('Exact Genre')
    expect(screen.getByTestId('chip-genre-3')).toHaveTextContent('Partial Genre')
    expect(screen.getByTestId('chip-genre-4')).toHaveTextContent('Fallback Genre')
    expect(screen.getByTestId('chip-genre-5')).toHaveTextContent('Display Only Genre')
    expect(screen.getByTestId('chip-seriesTag-11')).toHaveTextContent('Display Tag')
    expect(screen.getByTestId('chip-seriesTag-12')).toHaveTextContent('Partial Tag')
  })

  it('adds and removes genre and tag ids when chips are toggled', () => {
    const { props } = renderPanel({
      genres: [
        buildGenre({ id: 1, name: { nl: 'Alpha' } }),
        buildGenre({ id: 2, name: { nl: 'Bravo' } }),
      ],
      tags: [
        buildTag({ id: 3, name: { nl: 'Premiere' } }),
        buildTag({ id: 4, name: { nl: 'Festival' } }),
      ],
      selectedGenreIds: [2],
      selectedTagIds: [4],
    })

    fireEvent.click(screen.getByTestId('chip-genre-1'))
    fireEvent.click(screen.getByTestId('chip-genre-2'))
    fireEvent.click(screen.getByTestId('chip-seriesTag-3'))
    fireEvent.click(screen.getByTestId('chip-seriesTag-4'))

    expect(props.onGenreSelectionChange).toHaveBeenNthCalledWith(1, [2, 1])
    expect(props.onGenreSelectionChange).toHaveBeenNthCalledWith(2, [])
    expect(props.onTagSelectionChange).toHaveBeenNthCalledWith(1, [4, 3])
    expect(props.onTagSelectionChange).toHaveBeenNthCalledWith(2, [])
  })

  it('applies date drafts on blur, enter, clear, and close while ignoring other keys', () => {
    const { props } = renderPanel()
    const startAfterLabel = i18n.t('productions.home.filters.startAfter')
    const startBeforeLabel = i18n.t('productions.home.filters.startBefore')
    const startAfterInput = screen.getByLabelText(startAfterLabel)
    const startBeforeInput = screen.getByLabelText(startBeforeLabel)

    fireEvent.change(startAfterInput, { target: { value: '2026-05-10' } })
    fireEvent.blur(startAfterInput)
    expect(props.onFirstEventStartAfterChange).toHaveBeenNthCalledWith(1, '2026-05-10')

    fireEvent.change(startAfterInput, { target: { value: '' } })
    fireEvent.keyDown(startAfterInput, { key: 'Enter', code: 'Enter' })
    expect(props.onFirstEventStartAfterChange).toHaveBeenNthCalledWith(2, '')

    fireEvent.change(startBeforeInput, { target: { value: '2026-06-12' } })
    fireEvent.keyDown(startBeforeInput, { key: 'Tab', code: 'Tab' })
    expect(props.onFirstEventStartBeforeChange).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: `Close ${startBeforeLabel}` }))
    expect(props.onFirstEventStartBeforeChange).toHaveBeenCalledWith('2026-06-12')
  })

  it('ignores invalid date drafts and resets local draft state when props change', () => {
    const initialProps = buildProps({
      firstEventStartAfter: '2026-01-02',
      firstEventStartBefore: 'bad-date',
    })
    const view = renderWithProps(initialProps)
    const startAfterLabel = i18n.t('productions.home.filters.startAfter')
    const startBeforeLabel = i18n.t('productions.home.filters.startBefore')
    const startAfterInput = screen.getByLabelText(startAfterLabel)

    expect(startAfterInput).toHaveValue('2026-01-02')
    expect(screen.getByLabelText(startBeforeLabel)).toHaveValue('')

    fireEvent.change(startAfterInput, { target: { value: 'not-a-date' } })
    fireEvent.blur(startAfterInput)
    fireEvent.change(screen.getByLabelText(startBeforeLabel), {
      target: { value: 'still-not-a-date' },
    })
    fireEvent.click(screen.getByRole('button', { name: `Close ${startBeforeLabel}` }))
    expect(initialProps.onFirstEventStartAfterChange).not.toHaveBeenCalled()
    expect(initialProps.onFirstEventStartBeforeChange).not.toHaveBeenCalled()

    const nextProps = {
      ...initialProps,
      firstEventStartAfter: '2026-08-20',
      firstEventStartBefore: '2026-09-21',
    }
    view.rerender(
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <FilterPanel {...nextProps} />
        </ThemeProvider>
      </I18nextProvider>,
    )

    expect(screen.getByLabelText(startAfterLabel)).toHaveValue('2026-08-20')
    expect(screen.getByLabelText(startBeforeLabel)).toHaveValue('2026-09-21')

    fireEvent.blur(screen.getByLabelText(startAfterLabel))
    fireEvent.click(screen.getByRole('button', { name: `Close ${startBeforeLabel}` }))

    expect(initialProps.onFirstEventStartAfterChange).toHaveBeenCalledWith('2026-08-20')
    expect(initialProps.onFirstEventStartBeforeChange).toHaveBeenCalledWith('2026-09-21')
  })

  it('applies the latest date when a calendar selection changes and closes immediately', () => {
    const { props } = renderPanel()
    const startAfterLabel = i18n.t('productions.home.filters.startAfter')

    fireEvent.click(screen.getByRole('button', { name: `Pick ${startAfterLabel}` }))

    expect(props.onFirstEventStartAfterChange).toHaveBeenCalledWith('2026-07-15')
  })

  it('renders a mobile apply button when `onMobileApply` is provided and calls it', () => {
    const onMobileApply = jest.fn()
    renderPanel({ onMobileApply })

    // Button should be present (label comes from searchbar.search)
    const applyButton = screen.getByRole('button', { name: i18n.t('searchbar.search') })
    expect(applyButton).toBeInTheDocument()

    fireEvent.click(applyButton)
    expect(onMobileApply).toHaveBeenCalledTimes(1)
  })
})
