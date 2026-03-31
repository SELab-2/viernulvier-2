import sanitizeHtml from '../../utils/SanitizeHtml'

describe('sanitizeHtml', () => {
  it('returns empty string for empty input', () => {
    expect(sanitizeHtml('')).toBe('')
  })

  it('removes <script> tags (FORBID_TAGS)', () => {
    const input = '<p>Hello</p><script>alert(1)</script>'
    expect(sanitizeHtml(input)).toBe('<p>Hello</p>')
  })

  it('removes <br> tags (FORBID_TAGS)', () => {
    expect(sanitizeHtml('<p>Line one<br>Line two</p>')).toBe('<p>Line oneLine two</p>')
    expect(sanitizeHtml('<br>')).toBe('')
  })

  it('removes style and common event handler attributes (FORBID_ATTR)', () => {
    const input = '<div onclick="alert(1)" onmouseover="bad()" style="color:red">Test</div>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('onclick')
    expect(output).not.toContain('onmouseover')
    expect(output).not.toContain('style')
    expect(output).toContain('Test')
  })

  it('strips onerror and dimensions from images while keeping safe src', () => {
    const input =
      '<img src="https://example.com/x.png" width="999" height="1" onerror="alert(1)" alt="pic">'
    const output = sanitizeHtml(input)
    expect(output).toBe('<img src="https://example.com/x.png" alt="pic">')
    expect(output).not.toContain('onerror')
    expect(output).not.toContain('width')
    expect(output).not.toContain('height')
  })

  it('allows safe inline formatting tags', () => {
    const input = '<strong>Bold</strong> <em>Italic</em>'
    expect(sanitizeHtml(input)).toBe('<strong>Bold</strong> <em>Italic</em>')
  })
})
