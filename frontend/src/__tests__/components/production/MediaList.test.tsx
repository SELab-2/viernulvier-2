import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material'
import MediaList from '../../../components/production/MediaList'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (k: string, d: string) => d }),
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
    mockMatchMedia(false)
    const { container } = render(<MediaList mediaItems={[]} />)
    expect(container.firstChild).toBeNull()

    // item exists but no foto type -> nothing to render
    const noneContainer = render(
      <MediaList
        mediaItems={[
          {
            id: 1,
            type: 'video',
            display_title: 'nope',
            original_filename: 'nope.png',
            crops: [],
          },
        ]}
      />,
    )
    expect(noneContainer.container.firstChild).toBeNull()
  })

  it('selectsFE3header and renders with pagination buttons and labels', () => {
    // desktop wide, 3 items per slide
    mockMatchMedia(false)

    const items = [
      {
        id: 1,
        display_title: 'Img1',
        original_filename: 'orig1.png',
        type: 'foto',
        crops: [{ name: 'FE3_header', image_url: 'https://a.png' }],
      },
      {
        id: 2,
        display_title: 'Img2',
        original_filename: 'orig2.png',
        type: 'foto',
        crops: [{ name: 'hd_ready', image_url: 'https://b.png' }],
      },
      {
        id: 3,
        display_title: 'Img3',
        original_filename: 'orig3.png',
        type: 'foto',
        crops: [{ name: 'other', image_url: 'https://c.png' }],
      },
      {
        id: 4,
        display_title: 'Img4',
        original_filename: 'orig4.png',
        type: 'foto',
        crops: [{ name: 'other', image_url: 'https://d.png' }],
      },
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
        display_title: 'Imghd',
        original_filename: 'orig-hd.png',
        type: 'foto',
        crops: [{ name: 'hd_ready', image_url: 'https://hd.png' }],
      },
      {
        id: 2,
        display_title: 'Imgfallback',
        original_filename: 'orig-fallback.png',
        type: 'foto',
        crops: [{ name: 'other', image_url: 'https://fallback.png' }],
      },
    ]

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
      {
        id: 1,
        display_title: 'T1',
        original_filename: 't1.png',
        type: 'foto',
        crops: [{ name: 'hd_ready', image_url: 'https://t1.png' }],
      },
      {
        id: 2,
        display_title: 'T2',
        original_filename: 't2.png',
        type: 'foto',
        crops: [{ name: 'hd_ready', image_url: 'https://t2.png' }],
      },
      {
        id: 3,
        display_title: 'T3',
        original_filename: 't3.png',
        type: 'foto',
        crops: [{ name: 'other', image_url: 'https://t3.png' }],
      },
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
      {
        id: 4,
        display_title: '',
        original_filename: '',
        type: 'foto',
        crops: [{ name: 'other', image_url: 'https://fallback.png' }],
      },
    ]
    render(
      <ThemeProvider theme={theme}>
        <MediaList mediaItems={fallbackItems} />
      </ThemeProvider>,
    )
    expect(screen.getByAltText('Media item')).toBeInTheDocument()
  })
})
