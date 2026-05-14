// Simple reusable checkbox wrapper for filter UI

import { Checkbox, FormControlLabel } from '@mui/material'

type FilterCheckboxProps = {
  label: string
  checked: boolean
  onChange: () => void
}

// Stateless presentational component: delegates all state handling to parent
const FilterCheckbox = ({ label, checked, onChange }: FilterCheckboxProps) => (
  <FormControlLabel
    // Typography styling for consistent filter panel text sizing
    slotProps={{ typography: { variant: 'body2' } }}
    // Compact height to keep filter list visually tight
    sx={{ height: 24 }}
    label={label}
    control={<Checkbox size="small" checked={checked} onChange={onChange} color="secondary" />}
  />
)

export default FilterCheckbox
