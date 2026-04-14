import SearchIcon from '@mui/icons-material/Search'
import { IconButton, InputAdornment, TextField, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'

export interface SearchBarProps {
  placeholder?: string
  searchValue: string
  onSearchChange: (value: string) => void
  onSearchSubmit?: (value: string) => void
}

const SearchBar = ({
  placeholder = 'Search...',
  searchValue,
  onSearchChange,
  onSearchSubmit,
}: SearchBarProps) => {
  const theme = useTheme()
  const { t } = useTranslation()

  const handleSearchSubmit = () => {
    onSearchSubmit?.(searchValue.trim())
  }

  return (
    <TextField
      fullWidth
      variant="outlined"
      placeholder={placeholder}
      value={searchValue}
      onChange={(e) => onSearchChange(e.target.value)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          handleSearchSubmit()
        }
      }}
      slotProps={{
        input: {
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                aria-label={t('searchbar.search')}
                edge="end"
                onClick={handleSearchSubmit}
              >
                <SearchIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ),
        },
      }}
      sx={{
        flex: 1,
        '& .MuiInputBase-root': {
          height: 40,
          backgroundColor: theme.palette.background.default,
        },
      }}
      className="search-bar-textfield"
    />
  )
}

export default SearchBar
