import { useMediaQuery, useTheme } from '@mui/material'
import { useMemo } from 'react'

import ProductionGrid from './ProductionGrid'
import ProductionList from './ProductionList'

import type { Production } from '../types/Productions'

export type LayoutMode = 'grid' | 'list'

export interface ProductionViewProps {
  productions: Production[]
  layout?: LayoutMode
  selectedGenreIds?: number[]
  selectedTagIds?: number[]
}

/**
 * Renders either a {@link ProductionGrid} or a {@link ProductionList} based on
 * the requested {@link LayoutMode}.
 *
 * On viewports narrower than the `md` breakpoint, the component always falls back
 * to grid regardless of the requested `layout` because the list layout does not
 * fit comfortably on small screens.
 *
 * When `selectedGenreIds` is provided, productions whose genres include at least
 * one selected id are sorted to the front of the list. Chip interactivity is
 * handled by the card components themselves, so this view only controls layout
 * and genre-based sorting.
 *
 * @param props.productions List of productions to display.
 * @param props.selectedGenreIds Genre ids currently active in the parent filter state.
 * @param props.layout Requested layout mode; defaults to 'list'.
 * @returns The production view element.
 */
const ProductionView = ({
  productions,
  layout = 'list',
  selectedGenreIds,
  selectedTagIds,
}: ProductionViewProps) => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))

  const activeLayout: LayoutMode = isSmall ? 'grid' : layout

  // Stable-sort: productions that match at least one selected genre float to the top.
  const sortedProductions = useMemo(() => {
    if (!selectedGenreIds || selectedGenreIds.length === 0) {
      return productions
    }
    return [...productions].sort((a, b) => {
      const aMatches = a.genres.some((g) => selectedGenreIds.includes(g.id))
      const bMatches = b.genres.some((g) => selectedGenreIds.includes(g.id))
      if (aMatches && !bMatches) {
        return -1
      }
      if (!aMatches && bMatches) {
        return 1
      }
      return 0
    })
  }, [productions, selectedGenreIds])

  if (activeLayout === 'list') {
    return (
      <ProductionList
        productions={sortedProductions}
        selectedGenreIds={selectedGenreIds}
        selectedTagIds={selectedTagIds}
      />
    )
  }
  if (activeLayout === 'grid') {
    return (
      <ProductionGrid
        productions={sortedProductions}
        selectedGenreIds={selectedGenreIds}
        selectedTagIds={selectedTagIds}
      />
    )
  }
}

export default ProductionView
