import { Box, Divider, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Production } from '../../types/Productions'
import { formatDate } from '../../utils/formatDate'
import { getHallDisplayName } from '../../utils/hall'
import { Event } from '../../types/Events'

interface EventPricesPanelProps {
  production: Production
}

/**
 * Component to pass as `expandContent` to {@link ListCard}.
 *
 * Renders a list of events, each with its date and available price options.
 * Fully self-contained — it only needs the {@link Production} object.
 *
 * Usage:
 * ```tsx
 * <ListCard
 *   production={production}
 *   pathname={`/productions/${production.id}`}
 *   selectedGenreIds={selectedGenreIds}
 *   onGenreClick={handleGenreClick}
 *   expandContent={<EventPricesPanel production={production} />}
 * />
 * ```
 */
const EventPricesPanel = ({ production }: EventPricesPanelProps) => {
  const { t, i18n } = useTranslation()
  const language = i18n.language

  if (!production.events?.length) return null

  return (
    <Stack divider={<Divider />}>
      {production.events.map((event: Event) => (
        <Stack
          key={event.id}
          direction="row"
          alignItems="flex-start"
          spacing={3}
          sx={{ px: 3, py: 2 }}
        >
          {/* Date column */}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ minWidth: 160, flexShrink: 0, pt: 0.25 }}
          >
            {formatDate(event.starts_at, language)}
          </Typography>

          {/* Venue column */}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ minWidth: 180, flexShrink: 0, pt: 0.25 }}
          >
            {getHallDisplayName(event, language)}
          </Typography>

          {/* Prices */}
          <Stack direction="row" flexWrap="wrap" gap={1}>
            {event.prices.map((p) => (
              <Box
                key={p.id}
                sx={(theme) => ({
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: '4px',
                  px: 1.5,
                  py: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                })}
              >
                <Typography variant="body2" color="text.primary">
                  {p.price_display}
                </Typography>
                <Typography variant="body2" fontWeight="bold" color="text.primary">
                  €{Number(p.amount).toFixed(2)}
                </Typography>
                {p.available != null && (
                  <Typography variant="caption" color="text.disabled">
                    {t('events.availableQuantity', '{{count}} beschikbaar', { count: p.available })}
                  </Typography>
                )}
              </Box>
            ))}
          </Stack>
        </Stack>
      ))}
    </Stack>
  )
}

export default EventPricesPanel
