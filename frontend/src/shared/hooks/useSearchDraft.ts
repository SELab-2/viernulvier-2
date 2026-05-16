import { useMemo, useState } from 'react'

/**
 * Configuration for {@link useSearchDraft}.
 *
 * `value` is the canonical search value (usually from URL state).
 * `trackDirty` controls whether the UI should prefer the local draft value
 * while the user is typing.
 */
type UseSearchDraftOptions = {
  value: string
  trackDirty?: boolean
  onCommit: (value: string) => void
  onSameQuery?: (value: string) => void
}

/**
 * Result contract from {@link useSearchDraft}.
 */
type UseSearchDraftResult = {
  draft: string
  isDirty: boolean
  displayedValue: string
  setDraft: (value: string) => void
  submit: (value: string) => void
  reset: () => void
}

/** Normalize search input for comparisons and commits. */
const normalizeQuery = (value: string): string => value.trim()

/**
 * Tracks search input separately from the canonical query value.
 *
 * Typical usage:
 * - Use `displayedValue` for the input value.
 * - Use `setDraft` on input change.
 * - Use `submit` on search submit (button/enter).
 * - Use `reset` when external state should overwrite the draft.
 */
const useSearchDraft = ({
  value,
  trackDirty = false,
  onCommit,
  onSameQuery,
}: UseSearchDraftOptions): UseSearchDraftResult => {
  const [draft, setDraft] = useState(value)
  const [isDirty, setIsDirty] = useState(false)

  /** Update the draft and mark it dirty when tracking is enabled. */
  const updateDraft = (nextValue: string) => {
    setDraft(nextValue)
    if (trackDirty) {
      setIsDirty(true)
    }
  }

  /**
   * Commit the provided value:
   * - triggers `onSameQuery` when the normalized value did not change
   * - otherwise calls `onCommit` with the normalized value
   */
  const submit = (nextValue: string) => {
    const normalized = normalizeQuery(nextValue)
    const currentNormalized = normalizeQuery(value)

    if (normalized === currentNormalized) {
      onSameQuery?.(normalized)
    } else {
      onCommit(normalized)
    }

    setDraft(normalized)
    if (trackDirty) {
      setIsDirty(false)
    }
  }

  /** Reset the draft back to the canonical value and clear dirty state. */
  const reset = () => {
    setDraft(value)
    setIsDirty(false)
  }

  /**
   * Value to show in the search input.
   * When tracking dirty state, prefer the draft while the user is typing.
   */
  const displayedValue = useMemo(
    () => (trackDirty ? (isDirty ? draft : value) : value),
    [draft, isDirty, trackDirty, value],
  )

  return { draft, isDirty, displayedValue, setDraft: updateDraft, submit, reset }
}

export default useSearchDraft
