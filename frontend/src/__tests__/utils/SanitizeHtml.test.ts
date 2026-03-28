import sanitizeHtml from '../../utils/SanitizeHtml'

describe('sanitizeHtml', () => {
  it('returns empty string for empty input', () => {
    expect(sanitizeHtml('')).toBe('')
  })

  it('removes <script> tags', () => {
    const input = '<p>Hello</p><script>alert(1)</script>'
    expect(sanitizeHtml(input)).toBe('<p>Hello</p>')
  })

  it('removes unsafe event handlers and style attributes', () => {
    const input = '<div onclick="alert(1)" style="color:red">Test</div>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('onclick')
    expect(output).not.toContain('style')
    expect(output).toContain('Test')
  })

  it('allows safe HTML tags', () => {
    const input = '<strong>Bold</strong> <em>Italic</em>'
    expect(sanitizeHtml(input)).toBe('<strong>Bold</strong> <em>Italic</em>')
  })
})
