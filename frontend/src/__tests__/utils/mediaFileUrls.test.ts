import { getPublicMediaFileUrl } from '../../utils/mediaFileUrls'

describe('getPublicMediaFileUrl', () => {
  it('returns an empty URL unchanged', () => {
    expect(getPublicMediaFileUrl('')).toBe('')
  })

  it('rewrites an absolute HTTP URL to the current frontend origin', () => {
    const result = getPublicMediaFileUrl(
      'http://localhost:8000/media/uploads/example.pdf?download=1#page=2',
    )

    expect(result).toBe(`${window.location.origin}/media/uploads/example.pdf?download=1#page=2`)
  })

  it('rewrites an absolute HTTPS URL with uppercase protocol to the current frontend origin', () => {
    const result = getPublicMediaFileUrl('HTTPS://backend.example.com/media/uploads/poster.png')

    expect(result).toBe(`${window.location.origin}/media/uploads/poster.png`)
  })

  it('returns the original URL when an absolute URL cannot be parsed', () => {
    expect(getPublicMediaFileUrl('http://%')).toBe('http://%')
  })

  it('returns a root-relative URL unchanged', () => {
    expect(getPublicMediaFileUrl('/media/uploads/example.pdf')).toBe('/media/uploads/example.pdf')
  })

  it('prefixes a relative URL with a leading slash', () => {
    expect(getPublicMediaFileUrl('media/uploads/example.pdf')).toBe('/media/uploads/example.pdf')
  })
})
