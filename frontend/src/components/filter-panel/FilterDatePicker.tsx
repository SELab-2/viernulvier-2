import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import dayjs, { type Dayjs } from 'dayjs'
import { useRef, useState, type KeyboardEvent } from 'react'

const DATE_PICKER_FORMAT = 'DD/MM/YYYY'

type DateFieldState = {
  /** The external prop value at the time this state was last set. */
  sourceValue: string
  draft: Dayjs | null
  hasError: boolean
}

const parseDateValue = (value: string): Dayjs | null => {
  if (!value) {
    return null
  }
  const parsed = dayjs(value)
  return parsed.isValid() ? parsed : null
}

const formatDateValue = (value: Dayjs | null): string => {
  if (!value?.isValid()) {
    return ''
  }
  return value.format('YYYY-MM-DD')
}

const createFieldState = (sourceValue: string): DateFieldState => ({
  sourceValue,
  draft: parseDateValue(sourceValue),
  hasError: false,
})

type FilterDatePickerProps = {
  label: string
  /** ISO date string (e.g. 'YYYY-MM-DD') or empty string for no value. */
  value: string
  onChange: (value: string) => void
}

/**
 * A controlled date picker that buffers user input as a "draft" and only
 * calls `onChange` when the user confirms (blur, Enter, or calendar close).
 * Externally-driven `value` changes reset the draft automatically.
 */
const FilterDatePicker = ({ label, value, onChange }: FilterDatePickerProps) => {
  const [field, setField] = useState<DateFieldState>(() => createFieldState(value))
  // Ref keeps the latest field state accessible from stale event-handler closures.
  const fieldRef = useRef(field)

  // If the external value changed (e.g. cleared from outside), ignore local draft.
  const effectiveField = field.sourceValue === value ? field : createFieldState(value)

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
      value={effectiveField.draft}
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
      }}
      onClose={applyDraft}
      slotProps={{
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
