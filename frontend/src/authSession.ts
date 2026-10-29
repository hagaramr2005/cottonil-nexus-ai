// CSRF exists in JS memory only; the signed session token is HttpOnly and never exposed.
let csrf = "";
export function setCsrf(value: string) { csrf = value; }
export function authFetch(input: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (csrf && init.method && !["GET", "HEAD", "OPTIONS"].includes(init.method.toUpperCase())) headers.set("X-Nexus-CSRF", csrf);
  return fetch(input, { ...init, headers, credentials: "same-origin" });
}
