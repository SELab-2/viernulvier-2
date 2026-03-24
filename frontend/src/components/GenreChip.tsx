import { Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Genre } from '../types/Genres'
import { getTranslatedRecord } from '../utils/translations'

export interface GenreChipProps {
  genre: Genre
  selectedIds: number[]
  onClick: (genreId: number) => void
}

/**
 * Genre toggle chip. Uses the theme `accent` palette when this genre’s
 * id is in `selectedIds`.
 *
 * @param props.genre Backend {@link Genre}.
 * @param props.selectedIds Genre ids treated as active for styling.
 * @param props.onClick Called with the genre id when the chip is activated.
 * @returns The chip element.
 */
const GenreChip = ({ genre, selectedIds, onClick }: GenreChipProps) => {
  const { i18n } = useTranslation()
  const language = i18n.language

  const name = getTranslatedRecord(genre.name, language, genre.display_name)
  const isActive = selectedIds.includes(genre.id)

  return (
    <Button
      onClick={() => onClick(genre.id)}
      aria-pressed={isActive}
      aria-label={`Filter by ${name}`}
      sx={(theme) => ({
        flexShrink: 0,
        px: 2,
        minWidth: 'max-content',
        border: 'none',
        borderRadius: '12px',
        color: isActive ? theme.palette.accent.contrastText : theme.palette.text.secondary,
        backgroundColor: isActive ? theme.palette.accent.main : theme.palette.action.selected,
      })}
    >
      <Typography variant="caption" noWrap sx={{ lineHeight: 1 }}>
        {name}
      </Typography>
    </Button>
  )
}

export default GenreChip
