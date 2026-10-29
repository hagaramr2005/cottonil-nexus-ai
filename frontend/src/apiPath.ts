/** Normalize the caller path once; the Vite proxy owns the upstream host. */
export function normalizeApiPath(path: string): string {
  if (!path.startsWith('/')) throw new Error('API path must be relative to this origin')
  if (path.startsWith('//')) throw new Error('Network-path URLs are not allowed')
  const trimmed = path.replace(/^(?:\/api)+(?=\/|$)/, '')
  return '/api' + (trimmed || '/')
}
