import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import dayjs, { type Dayjs } from 'dayjs'
import { useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react'

/**
 * FilterDatePicker
 *
 * Controlled date picker used inside filter panels.
 *
 * Key behavior:
 * - Keeps a "draft" state separate from committed value
 * - Only commits value on blur / Enter / calendar close
 * - Clears immediately when user clears input
 * - Resets draft when external value changes
 */

const DATE_PICKER_FORMAT = 'DD/MM/YYYY'

/**
 * Internal state model for managing controlled + draft behavior.
 */
type DateFieldState = {
  /** The external prop value at the time this state was last set. */
  sourceValue: string
  /** Draft value shown in the picker before commit */
  draft: Dayjs | null
  /** Whether current draft has validation errors */
  hasError: boolean
}

/**
 * Parses ISO date string into Dayjs instance.
 */
const parseDateValue = (value: string): Dayjs | null => {
  if (!value) {
    return null
  }

  const parsed = dayjs(value)
  return parsed.isValid() ? parsed : null
}

/**
 * Formats Dayjs into API-compatible ISO string.
 */
const formatDateValue = (value: Dayjs | null): string => {
  if (!value?.isValid()) {
    return ''
  }
  return value.format('YYYY-MM-DD')
}

/**
 * Creates initial field state from external value.
 */
const createFieldState = (sourceValue: string): DateFieldState => ({
  sourceValue,
  draft: parseDateValue(sourceValue),
  hasError: false,
})

type FilterDatePickerProps = {
  label: string
  /** ISO date string (YYYY-MM-DD) or empty string for no value */
  value: string
  onChange: (value: string) => void
}

/**
 * Controlled date picker with buffered draft state.
 *
 * Why this exists:
 * MUI DatePicker updates can be noisy while typing/choosing dates.
 * This component ensures:
 * - controlled external state stays stable
 * - internal edits are buffered until commit
 */
const FilterDatePicker = ({ label, value, onChange }: FilterDatePickerProps) => {
  // Local state holding draft value + validation state
  const [field, setField] = useState<DateFieldState>(() => createFieldState(value))

  // Ref used to avoid stale closures in event handlers
  const fieldRef = useRef(field)

  /**
   * Track external value changes to reset internal draft state.
   * (Ensures UI stays in sync with URL / parent state updates)
   */
  const [prevExternalValue, setPrevExternalValue] = useState(value)

  if (value !== prevExternalValue) {
    setPrevExternalValue(value)
    const next = createFieldState(value)
    setField(next)
  }

  /**
   * Keep ref in sync with latest field state.
   */
  useLayoutEffect(() => {
    fieldRef.current = field
  }, [field])

  /**
   * Commits draft value back to parent if valid.
   */
  const applyDraft = () => {
    const latest =
      fieldRef.current.sourceValue === value ? fieldRef.current : createFieldState(value)

    if (!latest.hasError) {
      onChange(formatDateValue(latest.draft))
    }
  }

  return (
    <DatePicker
      label={label}
      value={field.draft}
      format={DATE_PICKER_FORMAT}
      disableFuture
      onChange={(newValue, context) => {
        const next: DateFieldState = {
          sourceValue: value,
          draft: newValue,
          hasError: context.validationError != null,
        }

        fieldRef.current = next
        setField(next)

        // Immediate commit when cleared
        if (newValue === null) {
          onChange('')
        }
      }}
      onClose={applyDraft}
      slotProps={{
        field: { clearable: true },
        textField: {
          size: 'small',
          fullWidth: true,
          slotProps: { inputLabel: { shrink: true } },
          onBlur: applyDraft,
          onKeyDown: (event: KeyboardEvent) => {
            if (event.key === 'Enter') {
              applyDraft()
            }
          },
        },
        actionBar: { actions: ['clear', 'accept'] },
      }}
    />
  )
}

export default FilterDatePicker
