import { useMediaQuery, useTheme } from '@mui/material'
import { useMemo, type Key, type ReactNode } from 'react'

import GenericGrid from './GenericGrid'
import GenericList from './GenericList'

import type { SearchViewMode } from './search/types'

/**
 * Props shared by list/grid item rendering in CollectionView.
 *
 * These define how individual items are keyed and rendered
 * in both layout modes.
 */
type CollectionViewItemProps<T> = {
  /**
   * Returns a stable unique key for each item.
   */
  getKey: (item: T) => Key

  /**
   * Render function for list layout.
   */
  renderListItem: (item: T) => ReactNode

  /**
   * Render function for grid layout.
   */
  renderGridItem: (item: T) => ReactNode

  /**
   * Spacing between list items (only used in list mode).
   */
  listSpacing?: number

  /**
   * Optional transformation applied before rendering.
   * Useful for mapping API data into UI-friendly shape.
   */
  transformItems?: (items: T[]) => T[]

  /**
   * Optional sorting function applied after transformItems.
   */
  sortItems?: (items: T[]) => T[]
}

/**
 * Props for CollectionView component.
 *
 * A responsive abstraction that switches between list and grid layouts
 * depending on user preference and screen size.
 */
export type CollectionViewProps<T> = {
  /**
   * Items to render.
   */
  items: T[]

  /**
   * Preferred layout mode.
   * Will be overridden on small screens.
   */
  layout?: SearchViewMode
} & CollectionViewItemProps<T>

/**
 * CollectionView
 *
 * A responsive data renderer that:
 * - Switches between list and grid layouts
 * - Forces grid on small screens (mobile-first behavior)
 * - Supports optional data transformation pipeline
 * - Supports custom sorting
 *
 * Layout logic:
 * - Mobile (md and down): always grid
 * - Desktop: uses provided layout prop
 *
 * Data pipeline:
 * items -> transformItems -> sortItems -> render
 */
const CollectionView = <T,>(props: CollectionViewProps<T>) => {
  const { items, layout = 'list', transformItems, sortItems } = props
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))
  const activeLayout: SearchViewMode = isSmall ? 'grid' : layout

  /**
   * Derived items after transformation + sorting.
   * Memoized to avoid unnecessary recalculations.
   */
  const viewItems = useMemo(() => {
    let result = transformItems ? transformItems(items) : items
    if (sortItems) {
      result = sortItems(result)
    }
    return result
  }, [items, transformItems, sortItems])

  if (activeLayout === 'list') {
    return (
      <GenericList
        items={viewItems}
        getKey={props.getKey}
        renderItem={props.renderListItem}
        spacing={props.listSpacing}
      />
    )
  }

  return <GenericGrid items={viewItems} getKey={props.getKey} renderItem={props.renderGridItem} />
}

export default CollectionView
