import { Chip, useTheme } from '@mui/material'
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CloseIcon from '@mui/icons-material/Close'

/**
 * Tag context determines click/navigation behavior.
 * - 'search': toggles tag selection
 * - 'description': navigates to homepage with tag in URL
 * - 'series': navigates to series detail page
 */
export type TagContext = 'search' | 'description' | 'series'

/**
 * Props for the Tag component.
 * - name: tag identifier (used for logic and navigation)
 * - displayName: human-readable label
 * - selected: whether the tag is currently selected
 * - onTagToggle: callback for toggling tag selection
 * - context: determines click/navigation behavior
 * - className: optional custom className
 */
interface TagProps {
  name: string
  displayName: string
  selected?: boolean
  onTagToggle?: (tag: string) => void
  context?: TagContext
  className?: string
}

// TODO: Tag displayNames must come from the API so they are correctly translated and all tags are included.

/**
 * Context-aware Tag chip component using MUI Chip.
 * - Pill-shaped, accessible, consistent color scheme.
 * - Handles context-aware click: search (toggle), description (to homepage), series (to series detail).
 */
const Tag: React.FC<TagProps> = ({
  name,
  displayName,
  selected = false,
  onTagToggle,
  context = 'search',
  className = '',
}) => {
  const theme = useTheme()
  const navigate = useNavigate()

  // Color palette for tag states
  const purple = '#9333ea'
  const purpleHover = '#7c22d6'
  const white = '#fff'
  const black = '#000'

  // Track hover state for cross icon highlight
  const [hovered, setHovered] = useState(false)

  /**
   * Handle tag click based on context.
   * - 'series': navigate to series detail page
   * - 'search': toggle tag selection
   * - 'description': navigate to homepage with tag selected in URL
   */
  const handleClick = () => {
    if (context === 'series') {
      // Navigate to series detail page
      // TODO: adjust route as needed
      navigate(`/series/${name}`)
      return
    }
    if (context === 'search') {
      // Toggle tag selection in search context
      if (onTagToggle) onTagToggle(name)
    } else if (context === 'description') {
      // Navigate to homepage with tag selected in URL
      navigate(`/?tags=${encodeURIComponent(name)}`)
    }
  }

  return (
    <Chip
      key={name}
      // Tag label: show displayName and cross icon if selected
      label={
        <span style={{ display: 'flex', alignItems: 'center' }}>
          {displayName}
          {selected && (
            <span
              // Cross icon hover highlight
              style={{
                display: 'flex',
                alignItems: 'center',
                marginLeft: 6,
                borderRadius: '50%',
                transition: 'background 0.15s, color 0.15s',
                background: hovered ? white : 'transparent',
                color: hovered ? purple : white,
                padding: 0.1,
                boxShadow: hovered ? '0 0 0 1px #fff' : undefined,
              }}
            >
              <CloseIcon fontSize="small" />
            </span>
          )}
        </span>
      }
      clickable
      onClick={handleClick}
      className={className}
      sx={{
        borderRadius: '9999px', // pill shape
        fontWeight: 500,
        fontSize: '0.95rem',
        px: 0.1,
        py: 0.3,
        minWidth: 0,
        transition: 'background 0.2s, color 0.2s, border 0.1s, padding 0.1s',
        userSelect: 'none',
        borderWidth: selected ? 2 : 1,
        borderStyle: 'solid',
        position: 'relative',
        // Color and border logic for selected/unselected, series and theme
        ...(context === 'series'
          ? {
              backgroundColor: `${purple} !important`,
              color: white,
              borderColor: purple,
              boxShadow: 'none',
              '&:hover': {
                backgroundColor: `${purpleHover} !important`,
                color: white,
                borderColor: purple,
              },
            }
          : selected
            ? {
                backgroundColor: `${purple} !important`,
                color: white,
                borderColor: purple,
                boxShadow: 'none',
                '&:hover': {
                  backgroundColor: `${purpleHover} !important`,
                  color: white,
                  borderColor: purple,
                },
              }
            : theme.palette.mode === 'light'
              ? {
                  backgroundColor: white,
                  color: black,
                  borderColor: black,
                  '&:hover': {
                    backgroundColor: purple,
                    color: white,
                    borderColor: purple,
                  },
                }
              : {
                  backgroundColor: theme.palette.background.paper,
                  color: white,
                  borderColor: white,
                  '&:hover': {
                    backgroundColor: purple,
                    color: white,
                    borderColor: purple,
                  },
                }),
        '&:focus': {
          boxShadow: 'none',
        },
      }}
      aria-pressed={selected}
      tabIndex={0}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    />
  )
}

export default Tag
