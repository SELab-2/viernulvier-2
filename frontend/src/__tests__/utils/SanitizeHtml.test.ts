import { htmlToPlainText, sanitizeHtml } from '../../utils/SanitizeHtml'

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

  it('removes common event handler attributes while keeping safe style attributes', () => {
    const input = '<div onclick="alert(1)" onmouseover="bad()" style="color:red">Test</div>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('onclick')
    expect(output).not.toContain('onmouseover')
    expect(output).toContain('style')
    expect(output).toContain('Test')
  })

  it('keeps safe image markup while stripping event handlers', () => {
    const input =
      '<img src="https://example.com/x.png" width="999" height="1" onerror="alert(1)" alt="pic" style="float:left;">'
    const output = sanitizeHtml(input)
    expect(output).toBe(
      '<img src="https://example.com/x.png" width="999" height="1" alt="pic" style="float:left;">',
    )
    expect(output).not.toContain('onerror')
  })

  it('decodes escaped html before sanitizing so images render correctly', () => {
    const input =
      '&lt;p&gt;&lt;img src="https://example.com/x.png" alt="pic" width="100" height="80" /&gt;&lt;/p&gt;'
    const output = sanitizeHtml(input)
    expect(output).toBe(
      '<p><img src="https://example.com/x.png" alt="pic" width="100" height="80"></p>',
    )
  })

  it('allows safe inline formatting tags', () => {
    const input = '<strong>Bold</strong> <em>Italic</em>'
    expect(sanitizeHtml(input)).toBe('<strong>Bold</strong> <em>Italic</em>')
  })
})

describe('htmlToPlainText', () => {
  it('strips markup and collapses whitespace', () => {
    const input = '<h4>&nbsp;zxcvzxcv</h4><div><br></div><div><p>Line 1</p><p>Line 2</p></div>'

    expect(htmlToPlainText(input)).toBe('zxcvzxcv Line 1 Line 2')
  })

  it('decodes escaped html before stripping markup', () => {
    const input = '&lt;p&gt;Hello &amp; goodbye&lt;/p&gt;'

    expect(htmlToPlainText(input)).toBe('Hello & goodbye')
  })
})
