import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material'

import { tokens } from '../../../../theme/tokens'

import type { ReactNode } from 'react'

/**
 * FilterSection
 *
 * Reusable collapsible section used inside filter panels.
 *
 * Purpose:
 * - Groups related filter controls under a collapsible header
 * - Keeps filter UI compact while still accessible
 * - Uses MUI Accordion for built-in expand/collapse behavior
 */
type FilterSectionProps = {
  title: string
  children: ReactNode
  defaultExpanded?: boolean
}

const FilterSection = ({ title, children, defaultExpanded = true }: FilterSectionProps) => (
  <Accordion defaultExpanded={defaultExpanded} disableGutters elevation={0}>
    {/* Section header */}
    <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />}>
      <Typography
        variant="body2"
        sx={{ fontWeight: tokens.typography.weights.medium }}
        component="h2"
      >
        {title}
      </Typography>
    </AccordionSummary>

    {/* Section content */}
    <AccordionDetails sx={{ paddingTop: 0 }}>{children}</AccordionDetails>
  </Accordion>
)

export default FilterSection
