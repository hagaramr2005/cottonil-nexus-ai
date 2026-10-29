import { describe, it, expect } from 'vitest'
import { normalizeApiPath } from './apiPath'
describe('API prefix normalization', () => {
  it('adds /api exactly once', () => {
    expect(normalizeApiPath('/copilot/status')).toBe('/api/copilot/status')
    expect(normalizeApiPath('/api/copilot/status')).toBe('/api/copilot/status')
    expect(normalizeApiPath('/api/api/copilot/status')).toBe('/api/copilot/status')
    expect(normalizeApiPath('/api/overview')).toBe('/api/overview')
    expect(normalizeApiPath('/overview')).toBe('/api/overview')
  })
  it('rejects external / network-path URLs', () => {
    expect(() => normalizeApiPath('https://example.com')).toThrow()
    expect(() => normalizeApiPath('//example.com')).toThrow()
  })
})
