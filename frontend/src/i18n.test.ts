import { describe, it, expect } from 'vitest'
import { D, fmtMoney, fmtNumber, t } from './i18n'
describe('translation coverage', () => {
  it('every key has non-empty ar and en', () => {
    for (const [k, v] of Object.entries(D)) {
      expect(v.ar.trim().length, k + ' ar').toBeGreaterThan(0)
      expect(v.en.trim().length, k + ' en').toBeGreaterThan(0)
    }
  })
  it('Arabic strings contain Arabic script (not copied English)', () => {
    const allowed = new Set(['lang_en', 'app_name'])
    for (const [k, v] of Object.entries(D)) if (!allowed.has(k)) expect(/[\u0600-\u06FF]/.test(v.ar), k).toBe(true)
  })
})
describe('number formatting never changes the value', () => {
  it('uses Western digits in both languages', () => {
    expect(fmtNumber('ar', 1234.5)).toBe(fmtNumber('en', 1234.5))
    expect(fmtNumber('ar', 841274176.32)).toBe(fmtNumber('en', 841274176.32))
    expect(/[٠-٩]/.test(fmtMoney('ar', 841274176.32))).toBe(false)
  })
  it('missing values are explicit, never zero', () => {
    expect(fmtNumber('en', null)).toBe('N/A')
    expect(fmtMoney('ar', undefined)).toBe('غير متاح')
  })
})

describe('t() resilience', () => {
  it('never throws on an unknown key (regression: n_ml-workspace white screen)', () => {
    expect(() => t('ar', 'n_ml-workspace' as never)).not.toThrow()
    expect(t('en', 'n_ml-workspace' as never)).toBe('n_ml-workspace')
  })
})
