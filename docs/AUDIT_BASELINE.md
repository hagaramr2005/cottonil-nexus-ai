# AUDIT BASELINE — Snapshot 2 → Final security implementation

Date: 2026-10-29. This document supersedes the earlier Snapshot 1 audit in this path; the historic audit remains in `docs/REPOSITORY_AUDIT.md`.

## Input and constraints
- Source: `cottonil-nexus-ai_snapshot2_source.zip` (116 ZIP entries). The historical `AUDIT_BASELINE.md` and upgrade brief were embedded in that archive. No separate original CSV archive was provided.
- The supplied ZIP contained application source, prior tests and docs, no `.git` directory, no customer CSVs and no populated database. A fresh local Git history was established before editing; nothing was rebuilt from scratch.
- Prior-session baseline (audit): 86 backend passing, 7 frontend Vitest passing, TypeScript and Vite build passed **in the prior environment**. Live Ollama was blocked. Never re-label these as current-session results.
- Current-session reproduction: **86/86** backend tests in a single pytest invocation before edits. The earlier claim that one-file-per-process is required did not reproduce under the current test fixture setup.

## Verified change set
1. Role-aware POST permissions allow read-only Copilot and Analyst access for organization-level viewers; all writes still require an administrator.
2. SQLite-backed session revocation, TTL, persistent failed-login throttling and identity-bound audit records. HttpOnly/SameSite session cookies, Secure in production, CSRF for cookie-authenticated mutations. Signed bearer tokens are returned only in development for API client compatibility.
3. Branch-bound users: SQL predicates on branch listing, sales mart and sales filters. Other business endpoints and data-bearing Copilot tools **deny** branch-limited access rather than leaking organization-wide values.
4. Persistent authentication, export and sensitive action audit records; admin-only audit API.
5. Strong headers, explicit CORS allow-list, protected production OpenAPI pages and scoped write authorization (frontend shared token inputs removed).
6. Data-derived investigations with source presence gates, observed predicates and a recorded detection ledger. Missing CSV sources suppress derived metrics.
7. Frontend source switched to cookie/CSRF session. No browser sessionStorage authentication token.
8. Added Docker/Compose definitions, Windows startup, DB backup/restore, CI configuration and Playwright smoke test source.

## Executed verification
- After security milestone: **91/91 backend tests passed**.
- After evidence and deployment work: **98/98 backend tests passed** (includes new security, reconciliation, backup/restore and branch mart tests).
- Python `compileall` on changed backend and scripts: succeeded.
- ZIP archives and patches must be verified on export; their hashes are tracked separately by delivery artifacts.

## Not executed / blockers
- TypeScript source-only syntax transpilation: **PASS** for 15 TS/TSX files (not type validation).
- Current Frontend Vitest, `tsc` and Vite build: **BLOCKED**. `npm ci` did not complete in the sandbox (dependency fetching unavailable/timed out). No verified `dist/` exists for this release.
- Playwright browser execution: **NOT EXECUTED** (no running compiled frontend or installed Chromium was verified). E2E test source exists.
- Docker images/Compose startup: **NOT EXECUTED**. Definition files are not deployment certification.
- Real Cottonil data ingestion, data reconciliation and KPI certification: **BLOCKED** (datasets not supplied).
- Live Ollama/LLM, remote model, production cookie TLS, security penetration test, MFA/SSO, full dependency scanner: **NOT VERIFIED**.

**Audit conclusion:** Valuable security implementation verified by unit/integration tests, but **NOT PRODUCTION READY**. See `SECURITY_READINESS.md`, `QA_REPORT.md`, `KNOWN_LIMITATIONS.md`.
