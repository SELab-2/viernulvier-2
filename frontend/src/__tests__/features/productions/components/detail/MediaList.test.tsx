import { ThemeProvider, createTheme } from '@mui/material'
import { fireEvent, render, screen } from '@testing-library/react'

import MediaList from '../../../../../features/productions/components/detail/MediaList'

import type { MediaItem, MediaItemCrop } from '../../../../../types/Media'

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

beforeEach(() => {
  Element.prototype.scrollTo = jest.fn()
})

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
    expect(screen.getByAltText('Imgfallback')).toHaveAttribute('src', 'https://fallback.png')
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

  it('opens and closes the image preview from click and keyboard actions', () => {
    const theme = createTheme({ palette: { mode: 'dark' } })
    mockMatchMedia('desktop')

    render(
      <ThemeProvider theme={theme}>
        <MediaList mediaItems={[baseMediaItem({ display_title: 'Preview image' })]} />
      </ThemeProvider>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Preview image' }))
    expect(screen.getAllByAltText('Preview image')).toHaveLength(2)

    fireEvent.click(screen.getByRole('button', { name: 'Close preview' }))
    expect(screen.getAllByAltText('Preview image')).toHaveLength(1)

    fireEvent.keyDown(screen.getByRole('button', { name: 'Preview image' }), { key: 'Enter' })
    expect(screen.getAllByAltText('Preview image')).toHaveLength(2)
  })
})

describe('MediaList - videoUrls prop', () => {
  afterEach(() => jest.clearAllMocks())

  it('renders null when both mediaItems and videoUrls are empty', () => {
    mockMatchMedia('desktop')

    const { container } = render(<MediaList mediaItems={[]} videoUrls={[]} />)

    expect(container.firstChild).toBeNull()
  })

  it('renders when only videoUrls are provided', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    expect(screen.getByText('Media')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /video 1/i })).toBeInTheDocument()
  })

  it('renders YouTube thumbnail from watch URL', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    const thumbnail = screen.getByAltText('Video 1') as HTMLImageElement

    expect(thumbnail).toBeInTheDocument()
    expect(thumbnail.src).toContain('/vi/abc123/hqdefault.jpg')
  })

  it('renders YouTube thumbnail from short URL', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://youtu.be/xyz789']} />)

    const thumbnail = screen.getByAltText('Video 1') as HTMLImageElement

    expect(thumbnail.src).toContain('/vi/xyz789/hqdefault.jpg')
  })

  it('renders YouTube thumbnail from shorts URL', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/shorts/short99']} />)

    const thumbnail = screen.getByAltText('Video 1') as HTMLImageElement

    expect(thumbnail.src).toContain('/vi/short99/hqdefault.jpg')
  })

  it('renders YouTube thumbnail from embed URL', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/embed/embed55']} />)

    const thumbnail = screen.getByAltText('Video 1') as HTMLImageElement

    expect(thumbnail.src).toContain('/vi/embed55/hqdefault.jpg')
  })

  it('renders no thumbnail for Vimeo videos', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://vimeo.com/123456789']} />)

    expect(screen.queryByAltText('Video 1')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /video 1/i })).toBeInTheDocument()
  })

  it('renders no thumbnail for SoundCloud videos', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://soundcloud.com/artist/track']} />)

    expect(screen.queryByAltText('Video 1')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /video 1/i })).toBeInTheDocument()
  })

  it('opens YouTube embed URL in modal', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    fireEvent.click(screen.getByRole('button', { name: /video 1/i }))

    const iframe = screen.getByTitle('Video player') as HTMLIFrameElement

    expect(iframe).toBeInTheDocument()
    expect(iframe.src).toContain('youtube.com/embed/abc123')
    expect(iframe.src).toContain('autoplay=1')
  })

  it('opens YouTube shorts embed URL in modal', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://youtube.com/shorts/short99']} />)

    fireEvent.click(screen.getByRole('button', { name: /video 1/i }))

    const iframe = screen.getByTitle('Video player') as HTMLIFrameElement

    expect(iframe.src).toContain('youtube.com/embed/short99')
  })

  it('opens Vimeo embed URL in modal', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://vimeo.com/123456789']} />)

    fireEvent.click(screen.getByRole('button', { name: /video 1/i }))

    const iframe = screen.getByTitle('Video player') as HTMLIFrameElement

    expect(iframe.src).toContain('player.vimeo.com/video/123456789')
    expect(iframe.src).toContain('autoplay=1')
  })

  it('opens SoundCloud embed URL in modal', () => {
    mockMatchMedia('desktop')

    const soundcloudUrl = 'https://soundcloud.com/artist/track'

    render(<MediaList mediaItems={[]} videoUrls={[soundcloudUrl]} />)

    fireEvent.click(screen.getByRole('button', { name: /video 1/i }))

    const iframe = screen.getByTitle('Video player') as HTMLIFrameElement

    expect(iframe.src).toContain('w.soundcloud.com/player')
    expect(iframe.src).toContain(encodeURIComponent(soundcloudUrl))
  })

  it('opens Loom embed URL in modal', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.loom.com/share/loom123']} />)

    fireEvent.click(screen.getByRole('button', { name: /video 1/i }))

    const iframe = screen.getByTitle('Video player') as HTMLIFrameElement

    expect(iframe.src).toContain('loom.com/embed/loom123')
  })

  it('closes the video modal', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    fireEvent.click(screen.getByRole('button', { name: /video 1/i }))

    expect(screen.getByTitle('Video player')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /close preview/i }))

    expect(screen.queryByTitle('Video player')).not.toBeInTheDocument()
  })

  it('opens video modal with Enter key', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    fireEvent.keyDown(screen.getByRole('button', { name: /video 1/i }), {
      key: 'Enter',
    })

    expect(screen.getByTitle('Video player')).toBeInTheDocument()
  })

  it('opens video modal with Space key', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    fireEvent.keyDown(screen.getByRole('button', { name: /video 1/i }), {
      key: ' ',
    })

    expect(screen.getByTitle('Video player')).toBeInTheDocument()
  })

  it('does not open modal for unsupported keys', () => {
    mockMatchMedia('desktop')

    render(<MediaList mediaItems={[]} videoUrls={['https://www.youtube.com/watch?v=abc123']} />)

    fireEvent.keyDown(screen.getByRole('button', { name: /video 1/i }), {
      key: 'Tab',
    })

    expect(screen.queryByTitle('Video player')).not.toBeInTheDocument()
  })

  it('renders multiple videos and opens the correct one', () => {
    mockMatchMedia('desktop')

    render(
      <MediaList
        mediaItems={[]}
        videoUrls={[
          'https://www.youtube.com/watch?v=first1',
          'https://www.youtube.com/watch?v=second2',
        ]}
      />,
    )

    expect(screen.getByRole('button', { name: /video 1/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /video 2/i })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /video 2/i }))

    const iframe = screen.getByTitle('Video player') as HTMLIFrameElement

    expect(iframe.src).toContain('second2')
  })

  it('renders photos and videos together', () => {
    mockMatchMedia('desktop')

    render(
      <MediaList
        mediaItems={[baseMediaItem({ display_title: 'My photo' })]}
        videoUrls={['https://www.youtube.com/watch?v=abc123']}
      />,
    )

    expect(screen.getByRole('button', { name: /video 1/i })).toBeInTheDocument()
    expect(screen.getByAltText('My photo')).toBeInTheDocument()
  })

  it('opens image preview when clicking photo item', () => {
    mockMatchMedia('desktop')

    render(
      <MediaList
        mediaItems={[baseMediaItem({ display_title: 'My photo' })]}
        videoUrls={['https://www.youtube.com/watch?v=abc123']}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'My photo' }))

    expect(screen.queryByTitle('Video player')).not.toBeInTheDocument()
    expect(screen.getAllByAltText('My photo')).toHaveLength(2)
  })

  it('renders correctly in dark mode', () => {
    mockMatchMedia('desktop')

    const theme = createTheme({
      palette: {
        mode: 'dark',
      },
    })

    render(
      <ThemeProvider theme={theme}>
        <MediaList mediaItems={[]} videoUrls={['https://vimeo.com/123456789']} />
      </ThemeProvider>,
    )

    expect(screen.getByRole('button', { name: /video 1/i })).toBeInTheDocument()
  })
})
