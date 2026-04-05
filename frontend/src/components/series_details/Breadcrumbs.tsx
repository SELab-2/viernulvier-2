import { Breadcrumbs, Link, Typography } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

type BreadcrumbItem = {
  label: string
  to?: string
}

type Props = {
  items: BreadcrumbItem[]
}

const SeriesDetailsBreadcrumbs = ({ items }: Props) => {
  return (
    <Breadcrumbs aria-label="breadcrumb">
      {items.map((item, index) => {
        const isLast = index === items.length - 1

        if (isLast || !item.to) {
          return (
            <Typography key={`${item.label}-${index}`} color="text.primary">
              {item.label}
            </Typography>
          )
        }

        return (
          <Link
            key={`${item.label}-${index}`}
            component={RouterLink}
            to={item.to}
            underline="hover"
            color="inherit"
          >
            {item.label}
          </Link>
        )
      })}
    </Breadcrumbs>
  )
}

export default SeriesDetailsBreadcrumbs
