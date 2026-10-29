# Security Readiness — final checkpoint

**Overall production verdict: NOT READY.** Source-level security mitigations are present and backend regressions pass, but environment validation, browser verification, penetration testing and third-party dependency checks remain outstanding.

## Implemented and backed by tests
- Role-based server authorization. `viewer`: approved read-only Copilot and Analyst POSTs. `admin`: eligible for write operations (still gated by CSRF for cookie-based sessions). Read-only POST is not reclassified as write to achieve access.
- Per-user branch membership: `NEXUS_BRANCH_SCOPES=user:BR1,BR2;user2:BR3`. For a scoped identity, only branch list, sales mart, sales filters and safe conversational greetings can be accessed; other business routes fail closed with HTTP 403. Sales aggregation uses SQL branch predicates, not JS filters. Global access is granted to users with **no** branch assignment; assign scopes to all branch-level staff.
- Token/session expiration with server-side `auth_sessions` revocation; login failures throttled per username/IP hash in SQLite; production requires PBKDF2 passwords, long auth secret, explicit HTTPS CORS origins and short TTL.
- Production browser auth uses `HttpOnly; Secure; SameSite=Strict` cookie (`/api` path); bearer returned only in development. `auth/me` refreshes per-session CSRF; JS stores only CSRF in memory, not the signed session token. Logout revokes session and deletes cookie.
- Role-bound audit in `audit_log` for logins, failed logins, denied access, report exports and sensitive actions. `GET /api/auth/audit` requires admin. Audit rows exclude submitted secrets. Audit is **not tamper-evident**, immutable or shipped to SIEM.
- Production CSP, HSTS, `no-store` API caching, no-sniff, anti-clickjacking, restrictive CORS and disabled production Swagger/OpenAPI pages.
- No arbitrary SQL from Copilot; pre-selected evidence only. Detected injection-like prompts skip LLM call. Histories are untrusted. Scoped users cannot invoke non-scoped evidence retrieval. Write operations are not exposed to the Copilot.

## Known security gaps and follow-ups
1. **Critical operational requirement:** HTTPS reverse proxy, production cookie and CSRF in a browser, CORS, role/group provisioning and session storage backed by durable protected database must be tested in staging. The example `compose.yaml` binds to localhost and does **not** terminate TLS.
2. **High:** Multi-process/distributed credential rotation, external identity management/MFA/SSO, reset/recovery, administrator provisioning and organizational access reviews not implemented.
3. **High:** Many analytics/Copilot endpoints are intentionally unavailable to branch-scoped users, pending full row-level isolation across their datasets and all read-only tools.
4. **High:** Regex-based injection screening is defense-in-depth, **not proof** of LLM prompt-injection safety; model output is not independently fact-checked. Do not provide LLM data access until model/authorization evaluation completes.
5. **High:** Audit DB has no cryptographic integrity or external retention; same DB administrator can modify evidence and audit entries.
6. **High:** No external vulnerability scan results, WAF, SIEM, incident process or pen-test approval yet. Python dependency ranges are not frozen with reproducible hashes.
7. **Medium:** Failed-login throttling is limited to individual username/IP hash. Distributed attempts, reverse-proxy real-client IP and account enumeration attacks require an external rate-limit tier. HTTP request volume quotas not implemented.
8. **Medium:** Frontend uses inline CSS, so CSP allows `'unsafe-inline'` for styles. No full nonce/hash CSP program.
9. **Medium:** JWT-like development bearer tokens may appear in API clients; do not log or distribute them. URL access tokens were removed.
10. **Medium:** Initial `.env` and local backup files are operator responsibility; no secret vault, encryption at rest or automated key rotation.

## Required sign-off
Security owner must verify signed-off production TLS, secrets, session handling and scoped role matrices against every endpoint, test dependencies, and approve residual risk. Until then restrict access to a controlled development/staging network.
