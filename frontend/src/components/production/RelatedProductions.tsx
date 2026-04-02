import { useEffect, useState } from 'react'
import { Box, CircularProgress, Stack, Typography } from '@mui/material'
import type { Production } from '../../types/Productions'
import type { Tag } from '../../types/Tags'
import ListCard from '../ListCard'
import { getRelatedProductions } from '../../utils/productions'


// TODO: misschien tjidens het laden een skeleton tonen?
// TODO: overal werken met de locales.

/**
 * Define the props for the RelatedProductions component:
 * - currentProductionId: Optional ID to exclude from related items so we don't show the same production.
 * - tags: Array of Tag objects to find related productions for.
 * - lang: Optional language code used to pick a display name for each tag (falls back to `display_name` or tag id).
 */
interface RelatedProductionsProps {
  tags: Tag[]
  lang?: string
  currentProductionId?: number
}

/**
 * RelatedProductions component fetches and displays a list of productions that share common tags with the current production.
 * The component is currently used in the ProductionDetailPage.
 *
 * @param tagIds - An array of tag IDs to find related productions.
 * @param currentProductionId - Current production ID which should be excluded from related items.
 * @param lang - Optional language code used to pick a display name for each tag (falls back to `display_name` or tag id).
 * @param tags - An array of Tag objects to find related productions for.
 * @returns A React component that displays a list of related productions based on shared tags.
 */
function RelatedProductions({ tags, lang = 'nl', currentProductionId }: RelatedProductionsProps) {
  const [perTagResults, setPerTagResults] = useState<Array<[string, Production[]]>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const fetch = async () => {
      setLoading(true)
      setError(null)

      try {
        if (tags.length === 0) {
          if (!cancelled) setPerTagResults([])
          return
        }

        const data = await getRelatedProductions(tags, lang, currentProductionId)
        if (!cancelled) setPerTagResults(data)
      } catch (err) {
        if (cancelled) return
        console.error('Error fetching related productions:', err)
        setError('Kon gerelateerde producties niet laden')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetch()

    return () => {
      cancelled = true
    }
  }, [tags, lang, currentProductionId])

  if (loading) {
    return (
      <Box sx={{ p: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <CircularProgress size={18} />
          <Typography variant="body2">Laden van gerelateerde producties…</Typography>
        </Stack>
      </Box>
    )
  }

  if (error) {
    // TODO: betere error afhandeling (bv. de popup)
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error" variant="body2">
          {error}
        </Typography>
      </Box>
    )
  }

  if (perTagResults.length === 0) {
    // TODO: hier deftige styling
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2">Geen gerelateerde producties gevonden.</Typography>
      </Box>
    )
  }
   
  // TODO: dit is momenteel een template, maak dit beter
  return (
    <Stack spacing={2} sx={{ p: 2 }}>
      <Typography variant="h6">Gerelateerde producties</Typography>
      {perTagResults.map(([tagName, productions]) => (
        <Box key={tagName}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            {tagName}
          </Typography>
          <Stack spacing={2}>
            {productions.slice(0, 6).map((production) => (
              <ListCard
                key={production.id}
                production={production}
                pathname={`/productions/${production.id}`}
                selectedGenreIds={[]}
                onGenreClick={() => undefined}
              />
            ))}
          </Stack>
        </Box>
      ))}
    </Stack>
  )
}

export default RelatedProductions
