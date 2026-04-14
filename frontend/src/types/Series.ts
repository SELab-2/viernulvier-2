import type { Tag } from './Tags'

/**
 * Series view model used on the series overview page.
 *
 * A series is represented by a frontend tag plus derived metadata from
 * the first and last production in that series.
 */
export interface Series {
  tag: Tag
  firstProductionStart: string | null
  lastProductionEnd: string | null
  lastProductionImage: string | null
}
