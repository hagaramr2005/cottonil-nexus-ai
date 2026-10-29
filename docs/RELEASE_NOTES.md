# Release Notes — Security and Data Integrity Upgrade (2026-10-29)

## Snapshot 2 baseline
- Existing source-derived KPI backend, React/Vite UI, deterministic/bilingual Copilot, optional LLM integration, reports, investigations and decision workflow preserved.
- Reproduced original **86 backend passing tests in one process**.

## Snapshot 3 — committed security milestone
- Read-only POST RBAC for approved Copilot/Analyst routes.
- Server-side signed sessions, expiration/revocation, persistent login throttling, CSRF-protected cookie mutations, role-bound audit log and secure HTTP response headers.
- Branch-limited filtering for branch data and sales-mart queries; fail-closed policy for non-scope-aware endpoints and unsafe Copilot evidence retrieval.
- Browser auth changed to cookie/CSRF. Removed frontend shared write-token fields and fixed-secret launcher value.
- Case creation gated by observed ingestion conditions.
- Security regression tests: **91 passed** when checkpointed. Standalone ZIP and `.patch` exported.

## Subsequent milestone additions
- `case_detection` provenance ledger with source hashes, observed values, thresholds and support verdict.
- Missing source prerequisite suppresses dependent metrics.
- Added full synthetic reconciliation, branch SQL and SQLite backup/restore regression tests.
- Added deployment blueprints, controlled Windows data-free startup, backup/restore, CI and E2E test source.
- Later `backend/tests` regression result: **98 passed**.

## Backward compatibility / intentional changes
- Production login now returns no bearer token (HttpOnly cookie instead). API clients depending on bearer production login must migrate to a suitable server-to-server identity solution.
- Browser session does not persist credentials in sessionStorage. After a refresh, `/api/auth/me` rehydrates authenticated UI state.
- Shared browser write token removed when authenticated; legacy token fallback remains only for unauthenticated local development.
- Branch-restricted identities cannot use organization-wide analytics/Copilot evidence routes until row-level isolation is completed.
- URL query `access_token` support removed. Existing clients must use cookies or development Authorization header.
- Investigation cases may disappear when their required data or signal is absent, unless a human action/decision must be retained.

## Unverified
- Updated frontend compilation/bundle (dependency installation blocked), Chromium E2E, Docker runtime, live LLM, real Cottonil metrics and dependency audits. No certification or production approval implied.


## Portfolio Multi-Agent extension — 2026-10-29
- New `backend/app/agent_workflow.py`: supervisor, sales evidence analyst, risk investigator, grounding reviewer and optional Ollama narrative; read-only tool discipline.
- New `GET /api/copilot/agents` metadata and `agent_trace` on chat responses; React expandable localized trace panel.
- Opt-in isolated synthetic-only demo seeding, guarded against overwrites and forbidden in production.
- New architecture design and Arabic LinkedIn script in `docs/MULTI_AGENT_*.md`.
- Retains existing endpoints, auth gates, numeric claim guard, deterministic fallback and model status. This is not a production-readiness declaration.
