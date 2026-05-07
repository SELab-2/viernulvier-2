import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import dayjs, { type Dayjs } from 'dayjs'
import { useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react'

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
 * A controlled date picker that buffers edits as a draft and commits when the user
 * confirms (blur, Enter, or calendar close). Clearing via the field clear control or
 * calendar commits immediately. External `value` changes reset the draft.
 */
const FilterDatePicker = ({ label, value, onChange }: FilterDatePickerProps) => {
  const [field, setField] = useState<DateFieldState>(() => createFieldState(value))
  // Ref keeps the latest field state accessible from stale event-handler closures.
  const fieldRef = useRef(field)

  const [prevExternalValue, setPrevExternalValue] = useState(value)
  if (value !== prevExternalValue) {
    setPrevExternalValue(value)
    const next = createFieldState(value)
    setField(next)
  }

  useLayoutEffect(() => {
    fieldRef.current = field
  }, [field])

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
