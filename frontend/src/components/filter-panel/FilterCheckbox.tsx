import { Checkbox, FormControlLabel } from '@mui/material'

type FilterCheckboxProps = {
  label: string
  checked: boolean
  onChange: () => void
}

const FilterCheckbox = ({ label, checked, onChange }: FilterCheckboxProps) => (
  <FormControlLabel
    slotProps={{ typography: { variant: 'body2' } }}
    sx={{ height: 24 }}
    label={label}
    control={<Checkbox size="small" checked={checked} onChange={onChange} color="secondary" />}
  />
)

export default FilterCheckbox
