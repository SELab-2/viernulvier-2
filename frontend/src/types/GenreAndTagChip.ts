import { Theme } from '@mui/material/styles'

export type ChipLabels = Record<string, string>

export type GenreAndTagChipContext = 'search' | 'description' | 'series' | 'static'
export type GenreAndTagChipType = 'genre' | 'seriesTag'
export type GenreAndTagChipId = string | number

export type GenreAndTagChipToggle = (
  value: GenreAndTagChipId,
  chipType: GenreAndTagChipType,
) => void

export interface GenreAndTagChipProps {
  /** Fallback label. */
  name: string
  /** Translated labels by locale code. */
  labels: ChipLabels
  /** Is the chip selected? */
  selected?: boolean
  /** Identifier used for URL state and callback payloads. */
  id: GenreAndTagChipId
  /** Semantic chip type; affects styles and URL query key mapping. */
  chipType?: GenreAndTagChipType
  /** Interaction context. */
  context?: GenreAndTagChipContext
  /** Selection callback used in search context. */
  onToggle?: GenreAndTagChipToggle
  /** Optional explicit aria label override. */
  ariaLabel?: string
}

export interface SearchChipOption {
  id: number
  name: string
  labels: ChipLabels
}

/**
 * Input for `getGenreAndTagChipStyles`.
 */
export type GetGenreAndTagChipStylesInput = {
  theme: Theme
  selected: boolean
  context: GenreAndTagChipContext
  chipType: GenreAndTagChipType
}
