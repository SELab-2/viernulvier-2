/**
 * Common Styles Tests
 *
 * Tests for reusable MUI sx pattern styles.
 */

import { createTheme, SxProps, Theme } from '@mui/material/styles'
import { createCommonStyles } from '../../theme/styles'
import { tokens } from '../../theme/tokens'

describe('theme/styles - createCommonStyles', () => {
  const lightTheme = createTheme({
    palette: {
      mode: 'light',
    },
  })

  const darkTheme = createTheme({
    palette: {
      mode: 'dark',
    },
  })

  it('should create common styles object with all expected properties', () => {
    const commonStyles = createCommonStyles(lightTheme)

    expect(commonStyles).toHaveProperty('cardBase')
    expect(commonStyles).toHaveProperty('gridContainer')
    expect(commonStyles).toHaveProperty('navbar')
    expect(commonStyles).toHaveProperty('footer')
    expect(commonStyles).toHaveProperty('responseImage')
    expect(commonStyles).toHaveProperty('linkHover')
    expect(commonStyles).toHaveProperty('chipBase')
    expect(commonStyles).toHaveProperty('container')
    expect(commonStyles).toHaveProperty('stack')
    expect(commonStyles).toHaveProperty('textTruncate')
    expect(commonStyles).toHaveProperty('centerContent')
  })

  it('cardBase should have correct properties', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const cardBaseSx = commonStyles.cardBase as SxProps<Theme>

    const cardBaseRecord = cardBaseSx as Record<string, unknown>
    expect(cardBaseRecord.borderRadius).toBe(tokens.card.borderRadiusPx)
    expect(cardBaseRecord.overflow).toBe('hidden')
    expect(cardBaseRecord.textDecoration).toBe('none')
  })

  it('cardBase should have hover shadow transition', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const cardBaseSx = commonStyles.cardBase as SxProps<Theme>
    const cardBaseRecord = cardBaseSx as Record<string, unknown>

    expect(cardBaseRecord.transition).toBe(tokens.transitions.base)
    expect(cardBaseRecord['&:hover']).toBeDefined()
  })

  it('gridContainer should have flex layout properties', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const gridContainerSx = commonStyles.gridContainer as SxProps<Theme>
    const gridContainerRecord = gridContainerSx as Record<string, unknown>

    expect(gridContainerRecord.display).toBe('flex')
    expect(gridContainerRecord.flexWrap).toBe('wrap')
    expect(gridContainerRecord.gap).toBe(tokens.spacing.numericLg)
    expect(gridContainerRecord.justifyContent).toBe('flex-start')
  })

  it('navbar should have sticky positioning with dark background', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const navbarSx = commonStyles.navbar as SxProps<Theme>
    const navbarRecord = navbarSx as Record<string, unknown>

    expect(navbarRecord.bgcolor).toBe(tokens.colors.neutral.black)
    expect(navbarRecord.position).toBe('sticky')
    expect(navbarRecord.top).toBe(0)
    expect(navbarRecord.zIndex).toBe(tokens.zIndex.sticky)
  })

  it('navbar should consistently be black even in dark theme', () => {
    const commonStylesDark = createCommonStyles(darkTheme)
    const navbarSx = commonStylesDark.navbar as SxProps<Theme>
    const navbarRecord = navbarSx as Record<string, unknown>

    expect(navbarRecord.bgcolor).toBe(tokens.colors.neutral.black)
  })

  it('footer should have correct styling', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const footerSx = commonStyles.footer as SxProps<Theme>
    const footerRecord = footerSx as Record<string, unknown>

    expect(footerRecord.bgcolor).toBe(tokens.colors.neutral.gray900)
    expect(footerRecord.color).toBe(tokens.colors.neutral.white)
    expect(footerRecord.mt).toBe(tokens.spacing.numericLg)
  })

  it('responseImage should have 16/9 aspect ratio', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const responseImageSx = commonStyles.responseImage as SxProps<Theme>
    const responseImageRecord = responseImageSx as Record<string, unknown>

    expect(responseImageRecord.aspectRatio).toBe('16 / 9')
    expect(responseImageRecord.objectFit).toBe('cover')
    expect(responseImageRecord.width).toBe('100%')
  })

  it('linkHover should have opacity transition', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const linkHoverSx = commonStyles.linkHover as SxProps<Theme>
    const linkHoverRecord = linkHoverSx as Record<string, unknown>

    expect(linkHoverRecord.transition).toBe(tokens.transitions.fast)
    expect((linkHoverRecord['&:hover'] as Record<string, unknown>)?.opacity).toBe(0.7)
  })

  it('chipBase should have proper styling', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const chipBaseSx = commonStyles.chipBase as SxProps<Theme>
    const chipBaseRecord = chipBaseSx as Record<string, unknown>

    expect(chipBaseRecord.borderRadius).toBe(tokens.borderRadius.md)
    expect(chipBaseRecord.cursor).toBe('pointer')
    expect(chipBaseRecord.transition).toBe(tokens.transitions.fast)
  })

  it('container should have responsive padding', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const containerSx = commonStyles.container as SxProps<Theme>
    const containerRecord = containerSx as Record<string, unknown>

    expect(containerRecord.maxWidth).toBe('1264px')
    expect(containerRecord.mx).toBe('auto')
    expect(containerRecord.px).toBeDefined()
  })

  it('stack should have flex column layout', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const stackSx = commonStyles.stack as SxProps<Theme>
    const stackRecord = stackSx as Record<string, unknown>

    expect(stackRecord.display).toBe('flex')
    expect(stackRecord.flexDirection).toBe('column')
    expect(stackRecord.gap).toBe(tokens.spacing.numericMd)
  })

  it('textTruncate should have ellipsis styling', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const textTruncateSx = commonStyles.textTruncate as SxProps<Theme>
    const textTruncateRecord = textTruncateSx as Record<string, unknown>

    expect(textTruncateRecord.overflow).toBe('hidden')
    expect(textTruncateRecord.textOverflow).toBe('ellipsis')
    expect(textTruncateRecord.whiteSpace).toBe('nowrap')
  })

  it('centerContent should have flex center alignment', () => {
    const commonStyles = createCommonStyles(lightTheme)
    const centerContentSx = commonStyles.centerContent as SxProps<Theme>
    const centerContentRecord = centerContentSx as Record<string, unknown>

    expect(centerContentRecord.display).toBe('flex')
    expect(centerContentRecord.alignItems).toBe('center')
    expect(centerContentRecord.justifyContent).toBe('center')
  })

  it('should return same structure regardless of theme mode', () => {
    const lightStyles = createCommonStyles(lightTheme)
    const darkStyles = createCommonStyles(darkTheme)

    expect(Object.keys(lightStyles)).toEqual(Object.keys(darkStyles))
  })
})
