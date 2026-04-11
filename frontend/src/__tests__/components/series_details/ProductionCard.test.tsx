import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter } from 'react-router-dom'
import ProductionCard from '../../../components/series_details/ProductionCard'
import type { Tag } from '../../../types/Tags'

describe('ProductionCard', () => {
  const makeTag = (id: number, nameNl: string, nameEn?: string): Tag => ({
    id,
    url: `/api/v1/tags/${id}/`,
    source: 'test',
    source_type: 'internal',
    type: 'series',
    is_external: false,
    is_enabled: true,
    display_name: null,
    display_short_description: null,
    display_url_title: null,
    name: nameEn ? { nl: nameNl, en: nameEn } : { nl: nameNl },
    short_description: null,
    url_title: null,
  })

  const defaultProps = {
    title: 'VIDEODROOM 2024',
    meta: '11e editie · 3–5 mei 2024',
    description: 'Een audiovisuele editie met live visuals en performances.',
    tags: [makeTag(1, 'Festival'), makeTag(2, 'Audiovisueel'), makeTag(3, '3 dagen')],
  }

  const renderCard = (props = defaultProps) => {
    return render(
      <MemoryRouter>
        <ProductionCard {...props} />
      </MemoryRouter>,
    )
  }

  it('renders title, meta, description and tags', () => {
    renderCard()

    expect(screen.getByText(defaultProps.title)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.meta)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.description)).toBeInTheDocument()

    defaultProps.tags.forEach((tag) => {
      expect(screen.getByText(tag.name?.nl ?? String(tag.id))).toBeInTheDocument()
    })
  })

  it('renders all provided tags as clickable chips', () => {
    const tags = [
      makeTag(11, 'Festival'),
      makeTag(12, 'Live visuals'),
      makeTag(13, '25 artiesten'),
      makeTag(14, '3 dagen'),
    ]

    renderCard({
      title: 'VIDEODROOM 2023',
      meta: '10e editie',
      description: 'Beschrijving',
      tags,
    })

    tags.forEach((tag) => {
      expect(screen.getByText(tag.name?.nl ?? String(tag.id))).toBeInTheDocument()
    })

    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(tags.length)
    expect(links[0]).toHaveAttribute('href', '/series/11')
  })

  it('uses the provided lang prop to resolve translated tag names', () => {
    const tags = [makeTag(21, 'Nederlands', 'English')]

    renderCard({
      title: 'Localized card',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.queryByText('Nederlands')).not.toBeInTheDocument()
  })

  it('falls back to display_name when translation for lang is missing', () => {
    const tags: Tag[] = [
      {
        ...makeTag(31, 'Alleen Nederlands'),
        name: { nl: 'Alleen Nederlands' },
        display_name: 'Fallback display',
      },
    ]

    renderCard({
      title: 'Fallback card',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('Fallback display')).toBeInTheDocument()
    expect(screen.queryByText('Alleen Nederlands')).not.toBeInTheDocument()
  })

  it('falls back to id when no translation and no display_name are available', () => {
    const tags: Tag[] = [
      {
        ...makeTag(41, 'Alleen Nederlands'),
        name: { nl: 'Alleen Nederlands' },
        display_name: null,
      },
    ]

    renderCard({
      title: 'Id fallback card',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('41')).toBeInTheDocument()
    expect(screen.queryByText('Alleen Nederlands')).not.toBeInTheDocument()
  })

  it('renders an empty tags row without crashing when name is null', () => {
    const tags: Tag[] = [
      {
        ...makeTag(51, 'unused'),
        name: null,
        display_name: null,
      },
    ]

    renderCard({
      title: 'Null name card',
      meta: 'meta',
      description: 'description',
      tags,
    })

    expect(screen.getByText('51')).toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', '/series/51')
  })

  it('renders no chips when tags is empty', () => {
    renderCard({
      title: 'No tags',
      meta: 'meta',
      description: 'description',
      tags: [],
    })

    expect(screen.queryAllByRole('link')).toHaveLength(0)
  })

  it('keeps duplicate labels stable through unique ids', () => {
    const tags = [makeTag(61, 'Same label'), makeTag(62, 'Same label')]

    renderCard({
      title: 'Duplicate labels',
      meta: 'meta',
      description: 'description',
      tags,
    })

    expect(screen.getAllByText('Same label')).toHaveLength(2)
    const sameLabelLinks = screen.getAllByRole('link', { name: 'Same label' })
    expect(sameLabelLinks).toHaveLength(2)
    expect(sameLabelLinks[0]).toHaveAttribute('href', '/series/61')
    expect(sameLabelLinks[1]).toHaveAttribute('href', '/series/62')
  })

  it('renders links for every chip in series context', () => {
    const tags = [makeTag(71, 'One'), makeTag(72, 'Two')]

    renderCard({
      title: 'Series links',
      meta: 'meta',
      description: 'description',
      tags,
    })

    expect(screen.getByRole('link', { name: 'One' })).toHaveAttribute('href', '/series/71')
    expect(screen.getByRole('link', { name: 'Two' })).toHaveAttribute('href', '/series/72')
  })

  it('resolves empty translation object with display_name fallback', () => {
    const tags: Tag[] = [
      {
        ...makeTag(81, 'unused'),
        name: {},
        display_name: 'Display only',
      },
    ]

    renderCard({
      title: 'Display fallback only',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('Display only')).toBeInTheDocument()
  })

  it('keeps default lang as nl when lang prop is not passed', () => {
    const tags = [makeTag(91, 'Nederlands', 'English')]

    renderCard({
      title: 'Default lang',
      meta: 'meta',
      description: 'description',
      tags,
    })

    expect(screen.getByText('Nederlands')).toBeInTheDocument()
    expect(screen.queryByText('English')).not.toBeInTheDocument()
  })

  it('renders an id fallback for empty translation record and missing display_name', () => {
    const tags: Tag[] = [
      {
        ...makeTag(101, 'unused'),
        name: {},
        display_name: null,
      },
    ]

    renderCard({
      title: 'Numeric fallback',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('101')).toBeInTheDocument()
  })

  it('renders correctly with mixed translated and fallback tags', () => {
    const tags: Tag[] = [
      makeTag(111, 'NL only', 'EN value'),
      {
        ...makeTag(112, 'NL without en'),
        name: { nl: 'NL without en' },
        display_name: 'Display fallback 112',
      },
    ]

    renderCard({
      title: 'Mixed tags',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('EN value')).toBeInTheDocument()
    expect(screen.getByText('Display fallback 112')).toBeInTheDocument()
  })

  it('renders title and metadata independent from tag translation language', () => {
    const tags = [makeTag(121, 'Nederlands', 'English')]

    renderCard({
      title: 'Static title',
      meta: 'Static meta',
      description: 'Static description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('Static title')).toBeInTheDocument()
    expect(screen.getByText('Static meta')).toBeInTheDocument()
    expect(screen.getByText('Static description')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
  })

  it('supports rendering a single translated tag', () => {
    const tags = [makeTag(131, 'Enkel', 'Single')]

    renderCard({
      title: 'Single tag',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('Single')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Single' })).toHaveAttribute('href', '/series/131')
  })

  it('renders multiple tags with distinct href targets', () => {
    const tags = [makeTag(141, 'A'), makeTag(142, 'B'), makeTag(143, 'C')]

    renderCard({
      title: 'Multiple hrefs',
      meta: 'meta',
      description: 'description',
      tags,
    })

    expect(screen.getByRole('link', { name: 'A' })).toHaveAttribute('href', '/series/141')
    expect(screen.getByRole('link', { name: 'B' })).toHaveAttribute('href', '/series/142')
    expect(screen.getByRole('link', { name: 'C' })).toHaveAttribute('href', '/series/143')
  })

  it('renders translated english value when available with lang en', () => {
    const tags = [makeTag(151, 'Nederlands', 'Translated EN')]

    renderCard({
      title: 'English language test',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('Translated EN')).toBeInTheDocument()
  })

  it('renders nl value by default when both nl and en are present', () => {
    const tags = [makeTag(161, 'Standaard NL', 'Alternative EN')]

    renderCard({
      title: 'Default NL preference',
      meta: 'meta',
      description: 'description',
      tags,
    })

    expect(screen.getByText('Standaard NL')).toBeInTheDocument()
    expect(screen.queryByText('Alternative EN')).not.toBeInTheDocument()
  })

  it('uses display_name over missing language key in name', () => {
    const tags: Tag[] = [
      {
        ...makeTag(171, 'Bestaat enkel in nl'),
        name: { nl: 'Bestaat enkel in nl' },
        display_name: 'Display wins',
      },
    ]

    renderCard({
      title: 'Display precedence',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('Display wins')).toBeInTheDocument()
  })

  it('renders numeric label when tag has no name and no display_name', () => {
    const tags: Tag[] = [
      {
        ...makeTag(181, 'unused'),
        name: null,
        display_name: null,
      },
    ]

    renderCard({
      title: 'Numeric label',
      meta: 'meta',
      description: 'description',
      tags,
      lang: 'en',
    })

    expect(screen.getByText('181')).toBeInTheDocument()
  })
})
