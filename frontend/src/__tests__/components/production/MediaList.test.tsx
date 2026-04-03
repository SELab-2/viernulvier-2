import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material'
import type { MediaItem, MediaItemCrop } from '../../../types/Media'
import MediaList from '../../../components/production/MediaList'

const baseCrop = (overrides: Partial<MediaItemCrop> = {}): MediaItemCrop => ({
  id: 1,
  name: 'hd_ready',
  image_url: 'https://default.png',
  ...overrides,
})

const baseMediaItem = (overrides: Partial<MediaItem> = {}): MediaItem => ({
  id: 1,
  gallery: 1,
  type: 'foto',
  format: 'jpg',
  original_filename: 'default.jpg',
  position: 0,
  width: null,
  height: null,
  title: null,
  display_title: 'Default',
  description: null,
  credits: null,
  link: null,
  crops: [baseCrop()],
  ...overrides,
})

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (_k: string, d: string) => d }),
}))

function mockMatchMedia(mode: 'mobile' | 'tablet' | 'desktop') {
  window.matchMedia = jest.fn().mockImplementation((query) => {
    const isDownSm = query.includes('max-width') && !query.includes('min-width')
    const isBetweenSmMd = query.includes('min-width') && query.includes('max-width')

    let matches = false
    if (mode === 'mobile') {
      matches = isDownSm
    } else if (mode === 'tablet') {
      matches = isBetweenSmMd
    } else {
      matches = !isDownSm && !isBetweenSmMd
    }

    return {
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }
  })
}

describe('MediaList component', () => {
  afterEach(() => jest.clearAllMocks())

  it('renders null when there are no media items or no images', () => {
    mockMatchMedia('desktop')
    const { container } = render(<MediaList mediaItems={[]} />)
    expect(container.firstChild).toBeNull()

    // item exists but no foto type -> nothing to render
    const noneContainer = render(
      <MediaList
        mediaItems={[
          baseMediaItem({
            id: 1,
            gallery: null,
            type: 'video',
            format: 'mp4',
            original_filename: 'nope.png',
            display_title: 'nope',
            crops: [],
          }),
        ]}
      />,
    )
    expect(noneContainer.container.firstChild).toBeNull()
  })

  it('selectsFE3header and renders with pagination buttons and labels', () => {
    // desktop wide, 3 items per slide
    mockMatchMedia('desktop')

    const items = [
      baseMediaItem({
        id: 1,
        display_title: 'Img1',
        original_filename: 'orig1.png',
        crops: [{ id: 1, name: 'FE3_header', image_url: 'https://a.png' }],
      }),
      baseMediaItem({
        id: 2,
        display_title: 'Img2',
        original_filename: 'orig2.png',
        crops: [{ id: 2, name: 'hd_ready', image_url: 'https://b.png' }],
      }),
      baseMediaItem({
        id: 3,
        display_title: 'Img3',
        original_filename: 'orig3.png',
        crops: [{ id: 3, name: 'other', image_url: 'https://c.png' }],
      }),
      baseMediaItem({
        id: 4,
        display_title: 'Img4',
        original_filename: 'orig4.png',
        crops: [{ id: 4, name: 'other', image_url: 'https://d.png' }],
      }),
    ]

    render(<MediaList mediaItems={items} />)

    // image from FE3_header should be visible as first slide
    const firstImage = screen.getByAltText('Img1') as HTMLImageElement
    expect(firstImage).toHaveAttribute('src', 'https://a.png')

    // check counter and carousel controls work
    expect(screen.getByText('1 / 4')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next media' }))
    expect(screen.getByText('4 / 4')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Previous media' }))
    expect(screen.getByText('1 / 4')).toBeInTheDocument()
  })

  it('uses hd_ready when FE3_header is absent and falls back to first crop', () => {
    mockMatchMedia('mobile') // mobile -> 1 item per slide

    const items = [
      {
        id: 1,
        gallery: null,
        type: 'foto',
        format: 'jpg',
        original_filename: 'orig-hd.png',
        position: 0,
        width: null,
        height: null,
        title: null,
        display_title: 'Imghd',
        description: null,
        credits: null,
        link: null,
        crops: [{ name: 'hd_ready', image_url: 'https://hd.png' }],
      },
      {
        id: 2,
        gallery: null,
        type: 'foto',
        format: 'jpg',
        original_filename: 'orig-fallback.png',
        position: 1,
        width: null,
        height: null,
        title: null,
        display_title: 'Imgfallback',
        description: null,
        credits: null,
        link: null,
        crops: [{ name: 'other', image_url: 'https://fallback.png' }],
      },
    ] as unknown as MediaItem[]

    render(<MediaList mediaItems={items} />)

    expect(screen.getByAltText('Imghd')).toHaveAttribute('src', 'https://hd.png')
    fireEvent.click(screen.getByRole('button', { name: 'Next media' }))
    expect(screen.getByAltText('Imgfallback')).toHaveAttribute('src', 'https://fallback.png')
  })

  it('renders with tablet mode (2 items per slide) and dark theme style', () => {
    mockMatchMedia('tablet')

    const theme = createTheme({
      palette: {
        mode: 'dark',
      },
    })

    const items = [
      baseMediaItem({
        id: 1,
        display_title: 'T1',
        original_filename: 't1.png',
        crops: [{ id: 5, name: 'hd_ready', image_url: 'https://t1.png' }],
      }),
      baseMediaItem({
        id: 2,
        display_title: 'T2',
        original_filename: 't2.png',
        crops: [{ id: 6, name: 'hd_ready', image_url: 'https://t2.png' }],
      }),
      baseMediaItem({
        id: 3,
        display_title: 'T3',
        original_filename: 't3.png',
        crops: [{ id: 7, name: 'other', image_url: 'https://t3.png' }],
      }),
    ]

    render(
      <ThemeProvider theme={theme}>
        <MediaList mediaItems={items} />
      </ThemeProvider>,
    )

    expect(screen.getByText('1 / 3')).toBeInTheDocument()

    const buttons = screen.getAllByRole('button', { name: /Previous media|Next media/ })
    const prevBtn = buttons.find((btn) => btn.getAttribute('aria-label') === 'Previous media')
    const nextBtn = buttons.find((btn) => btn.getAttribute('aria-label') === 'Next media')
    expect(prevBtn).toBeDefined()
    expect(nextBtn).toBeDefined()

    expect(prevBtn).toHaveStyle('background: rgba(10, 14, 40, 0.65)')
    expect(nextBtn).toHaveStyle('background: rgba(10, 14, 40, 0.65)')

    const firstSlide = screen.getByAltText('T1')
    expect(firstSlide).toBeInTheDocument()

    fireEvent.click(nextBtn!)
    expect(screen.getByText('3 / 3')).toBeInTheDocument()
  })

  it('covers MediaList line 150 fallback alt text', () => {
    const theme = createTheme({ palette: { mode: 'dark' } })

    mockMatchMedia('tablet')

    const fallbackItems = [
      baseMediaItem({
        id: 4,
        display_title: '',
        original_filename: '',
        crops: [{ id: 8, name: 'other', image_url: 'https://fallback.png' }],
      }),
    ]

    render(
      <ThemeProvider theme={theme}>
        <MediaList mediaItems={fallbackItems} />
      </ThemeProvider>,
    )
    expect(screen.getByAltText('Media item')).toBeInTheDocument()
  })
})
