import type { Theme } from '@mui/material/styles'

/**
 * Mapping of locale codes to translated chip labels.
 */
export type ChipLabels = Record<string, string>

/**
 * Defines where a chip is used in the UI, which affects styling and behavior.
 */
export type GenreAndTagChipContext = 'search' | 'description' | 'series' | 'static'

/**
 * Defines the semantic type of a chip.
 */
export type GenreAndTagChipType = 'genre' | 'seriesTag'

/**
 * Unique identifier for a chip.
 */
export type GenreAndTagChipId = string | number

/**
 * Callback triggered when a chip is toggled in interactive contexts.
 */
export type GenreAndTagChipToggle = (
  value: GenreAndTagChipId,
  chipType: GenreAndTagChipType,
) => void

/**
 * Props for a Genre/Tag chip component.
 */
export interface GenreAndTagChipProps {
  /** Fallback label used when no translation is available. */
  name: string

  /** Translated labels keyed by locale code. */
  labels: ChipLabels

  /** Whether the chip is currently selected. */
  selected?: boolean

  /** Unique identifier used for state management and URL syncing. */
  id: GenreAndTagChipId

  /** Semantic chip type influencing styling and behavior. */
  chipType?: GenreAndTagChipType

  /** UI context in which the chip is rendered. */
  context?: GenreAndTagChipContext

  /** Callback triggered when the chip is toggled. */
  onToggle?: GenreAndTagChipToggle

  /** Optional accessibility label override. */
  ariaLabel?: string
}

/**
 * Simplified chip representation used in search results.
 */
export interface SearchChipOption {
  id: number
  name: string
  labels: ChipLabels
}

/**
 * Input parameters for computing chip styles.
 */
export type GetGenreAndTagChipStylesInput = {
  theme: Theme
  selected: boolean
  context: GenreAndTagChipContext
  chipType: GenreAndTagChipType
}