import SearchIcon from '@mui/icons-material/Search'
import { IconButton, InputAdornment, TextField, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'

/**
 * SearchBarProps
 *
 * Controlled search input component used across collection/search pages.
 *
 * Responsibilities:
 * - Displays search input field
 * - Emits value changes immediately
 * - Supports optional "submit" action (Enter key or button click)
 */
export interface SearchBarProps {
  placeholder?: string
  searchValue: string
  onSearchChange: (value: string) => void
  onSearchSubmit?: (value: string) => void
}

/**
 * SearchBar
 *
 * Simple controlled input for search functionality.
 *
 * Behavior:
 * - Fully controlled via `searchValue`
 * - Calls `onSearchChange` on every keystroke
 * - Calls `onSearchSubmit` on Enter or click (if provided)
 */
const SearchBar = ({
  placeholder = 'Search...',
  searchValue,
  onSearchChange,
  onSearchSubmit,
}: SearchBarProps) => {
  const theme = useTheme()
  const { t } = useTranslation()

  /**
   * Triggers submit callback with trimmed input value.
   */
  const handleSearchSubmit = () => {
    onSearchSubmit?.(searchValue.trim())
  }

  return (
    <TextField
      fullWidth
      variant="outlined"
      placeholder={placeholder}
      autoComplete="off"
      value={searchValue}
      onChange={(e) => onSearchChange(e.target.value)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          handleSearchSubmit()
        }
      }}
      slotProps={{
        htmlInput: {
          autoComplete: 'off',
          autoCapitalize: 'none',
          autoCorrect: 'off',
          spellCheck: false,
          inputMode: 'search',
        },
        input: {
          endAdornment: (
            <InputAdornment position="end">
              {/* Submit search button */}
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
