/**
 * Design Tokens Tests
 *
 * Tests for design system token constants and exports.
 */

import { tokens } from '../../theme/tokens'

describe('theme/tokens - Design System Tokens', () => {
  it('should export tokens object with all required sections', () => {
    expect(tokens).toHaveProperty('colors')
    expect(tokens).toHaveProperty('spacing')
    expect(tokens).toHaveProperty('shadows')
    expect(tokens).toHaveProperty('typography')
    expect(tokens).toHaveProperty('borderRadius')
    expect(tokens).toHaveProperty('transitions')
    expect(tokens).toHaveProperty('zIndex')
    expect(tokens).toHaveProperty('breakpoints')
    expect(tokens).toHaveProperty('navbar')
    expect(tokens).toHaveProperty('card')
    expect(tokens).toHaveProperty('chip')
  })

  describe('colors', () => {
    it('should have accent colors', () => {
      expect(tokens.colors.accent.main).toBe('#8224E3')
      expect(tokens.colors.accent.contrastText).toBe('#ffffff')
    })

    it('should have light mode colors', () => {
      expect(tokens.colors.light.background).toBeDefined()
      expect(tokens.colors.light.surface).toBeDefined()
      expect(tokens.colors.light.text).toBeDefined()
    })

    it('should have dark mode colors', () => {
      expect(tokens.colors.dark.background).toBeDefined()
      expect(tokens.colors.dark.surface).toBeDefined()
      expect(tokens.colors.dark.text).toBeDefined()
    })

    it('should have neutral colors', () => {
      expect(tokens.colors.neutral.black).toBe('#000000')
      expect(tokens.colors.neutral.white).toBe('#ffffff')
    })

    it('should have semantic colors', () => {
      expect(tokens.colors.semantic.success).toBeDefined()
      expect(tokens.colors.semantic.error).toBeDefined()
      expect(tokens.colors.semantic.warning).toBeDefined()
      expect(tokens.colors.semantic.info).toBeDefined()
    })
  })

  describe('spacing', () => {
    it('should have px-based spacing values', () => {
      expect(tokens.spacing.xs).toBe('4px')
      expect(tokens.spacing.sm).toBe('8px')
      expect(tokens.spacing.md).toBe('16px')
      expect(tokens.spacing.lg).toBe('24px')
      expect(tokens.spacing.xl).toBe('32px')
    })

    it('should have numeric spacing values for MUI', () => {
      expect(tokens.spacing.numericXs).toBe(0.5)
      expect(tokens.spacing.numericSm).toBe(1)
      expect(tokens.spacing.numericMd).toBe(2)
      expect(tokens.spacing.numericLg).toBe(3)
      expect(tokens.spacing.numericXl).toBe(4)
    })
  })

  describe('shadows', () => {
    it('should have multiple shadow levels', () => {
      expect(tokens.shadows.subtle).toBeDefined()
      expect(tokens.shadows.sm).toBeDefined()
      expect(tokens.shadows.md).toBeDefined()
      expect(tokens.shadows.lg).toBeDefined()
      expect(tokens.shadows.xl).toBeDefined()
      expect(tokens.shadows.navbar).toBeDefined()
    })

    it('should have navbar shadow', () => {
      expect(tokens.shadows.navbar).toContain('rgba(255')
      expect(tokens.shadows.navbar).toContain('0.1')
    })
  })

  describe('typography', () => {
    it('should have font family set', () => {
      expect(tokens.typography.fontFamily).toContain('ABC Monument Grotesk')
    })

    it('should have font weights', () => {
      expect(tokens.typography.weights.light).toBe(300)
      expect(tokens.typography.weights.regular).toBe(400)
      expect(tokens.typography.weights.bold).toBe(700)
    })

    it('should have font sizes', () => {
      expect(tokens.typography.sizes.xs).toBe('12px')
      expect(tokens.typography.sizes.base).toBe('16px')
      expect(tokens.typography.sizes['5xl']).toBe('48px')
    })

    it('should have line heights', () => {
      expect(tokens.typography.lineHeights.tight).toBe(1.2)
      expect(tokens.typography.lineHeights.normal).toBe(1.5)
      expect(tokens.typography.lineHeights.relaxed).toBe(1.7)
    })
  })

  describe('borderRadius', () => {
    it('should have border radius values', () => {
      expect(tokens.borderRadius.none).toBe('0px')
      expect(tokens.borderRadius.md).toBe('8px')
      expect(tokens.borderRadius.full).toBe('9999px')
    })
  })

  describe('transitions', () => {
    it('should have transition timing values', () => {
      expect(tokens.transitions.fast).toBe('150ms ease')
      expect(tokens.transitions.base).toBe('200ms ease')
      expect(tokens.transitions.slow).toBe('300ms ease')
    })
  })

  describe('zIndex', () => {
    it('should have z-index values', () => {
      expect(tokens.zIndex.base).toBe(0)
      expect(tokens.zIndex.sticky).toBe(1020)
      expect(tokens.zIndex.modal).toBe(1060)
      expect(tokens.zIndex.tooltip).toBe(1080)
    })
  })

  describe('breakpoints', () => {
    it('should have responsive breakpoints', () => {
      expect(tokens.breakpoints.xs).toBe('0px')
      expect(tokens.breakpoints.sm).toBe('600px')
      expect(tokens.breakpoints.md).toBe('960px')
      expect(tokens.breakpoints.lg).toBe('1264px')
      expect(tokens.breakpoints.xl).toBe('1920px')
    })
  })

  describe('component-specific tokens', () => {
    it('should have navbar min height', () => {
      expect(tokens.navbar.minHeight).toBe(64)
    })

    it('should have card configuration', () => {
      expect(tokens.card.borderRadius).toBe(4)
      expect(tokens.card.borderRadiusPx).toBe('16px')
      expect(tokens.card.padding).toBe(3)
    })

    it('should have chip configuration', () => {
      expect(tokens.chip.borderRadius).toBeDefined()
      expect(tokens.chip.paddingY).toBeDefined()
      expect(tokens.chip.paddingX).toBeDefined()
    })
  })
})
