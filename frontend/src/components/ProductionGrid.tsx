import { Box } from '@mui/material'
import type { Production } from '../types/Productions'
import ProductionGridCard from './ProductionGridCard'

export interface ProductionGridProps {
  productions: Production[]
  selectedGenreIds?: number[]
  onGenreClick?: (genreId: number) => void
}

/**
 * Renders a responsive wrap-grid of {@link ProductionGridCard} items.
 *
 * Cards are laid out with `flex-wrap` so they reflow naturally across screen sizes.
 * Each card maintains its own fixed width (350 px) and the gap between cards is
 * uniform in both axes.
 *
 * @param props.productions List of productions to display.
 * @param props.selectedGenreIds Genre ids currently active in the parent filter state.
 * @param props.onGenreClick Forwarded to every card; called with the clicked genre id.
 * @returns The grid container element.
 */
const ProductionGrid = ({ productions, selectedGenreIds, onGenreClick }: ProductionGridProps) => {
  return (
    <Box display="flex" flexWrap="wrap" gap={3} justifyContent="center">
      {productions.map((production) => (
        <ProductionGridCard
          key={production.id}
          production={production}
          selectedGenreIds={selectedGenreIds}
          onGenreClick={onGenreClick}
        />
      ))}
    </Box>
  )
}

export default ProductionGrid
