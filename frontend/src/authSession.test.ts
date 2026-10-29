import { afterEach, expect, it, vi } from 'vitest';
import { authFetch, setCsrf } from './authSession';

afterEach(() => { vi.unstubAllGlobals(); setCsrf(''); });
it('adds CSRF header only to state-changing calls, no bearer token', async () => {
  const fake = vi.fn().mockResolvedValue({ ok: true });
  vi.stubGlobal('fetch', fake);
  setCsrf('test-csrf');
  await authFetch('/api/auth/logout', { method: 'POST' });
  const [url,init] = fake.mock.calls[0];
  expect(url).toBe('/api/auth/logout');
  expect(init.headers.get('X-Nexus-CSRF')).toBe('test-csrf');
  expect(init.headers.get('Authorization')).toBe(null);
  expect(init.credentials).toBe('same-origin');
  await authFetch('/api/auth/me');
  expect(fake.mock.calls[1][1].headers.get('X-Nexus-CSRF')).toBe(null);
});
