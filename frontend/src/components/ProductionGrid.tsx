import { Box, useTheme } from '@mui/material'
import type { Production } from '../types/Productions'
import ProductionGridCard from './ProductionGridCard'
import { createCommonStyles } from '../theme/styles'

export interface ProductionGridProps {
  productions: Production[]
  selectedGenreIds?: number[]
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
 * @returns The grid container element.
 */
const ProductionGrid = ({ productions, selectedGenreIds }: ProductionGridProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)

  return (
    <Box sx={commonStyles.gridContainer}>
      {productions.map((production) => (
        <ProductionGridCard
          key={production.id}
          production={production}
          selectedGenreIds={selectedGenreIds}
        />
      ))}
    </Box>
  )
}

export default ProductionGrid
