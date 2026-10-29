# V9 product enhancement checkpoint — 2026-10-27

## Implemented changes
- Added read-only `/api/product/readiness`: dataset/metric counts, last ingestion, source CSV presence, analytical mart presence, write token configuration, AI configuration, and explicit production-readiness caveats. This is not a security scanner or uptime monitor.
- Added client-visible bilingual Product Readiness screen and navigation route.
- Replaced the one-panel Executive Story Mode with a 5-stage, fullscreen, evidence-backed presentation workflow covering pulse, trust, investigations, next actions, and reports. Uses the existing V7/V8 briefing, no synthetic metrics.
- Refined interactive states, keyboard focus visibility, spacing, fullscreen presentation responsiveness, and reduced-motion support.
- Added optional organization display name environment variables for future branding work; **no tenant isolation or actual UI branding engine is implied**.

## Tests performed
- V7, V8, V9 targeted backend tests: **8 passed**.
- Complete backend suite: **26 passed, 4 failed**. Three failures need the missing sales mart; one analyst regression assertion requires ingested metrics. The original datasets were not shipped in this checkpoint.
- React production build: **not run**. Offline npm install failed because npm cache lacks @types/react. Do not describe this release as frontend-verified.
- Playwright/browser E2E: not executed. No screenshots are claimed.

## Commercial blockers (must resolve before customer deployment)
1. Provide and reconcile all 25 source CSV files and rebuild sales marts in controlled environment.
2. Install npm dependencies on a machine with access to the registry and run `npm run build`; fix all TypeScript errors (if any).
3. Run Playwright desktop/mobile checks in English and Arabic.
4. Security: authenticate read endpoints, implement enforceable authorization by user, add per-user audit identity, secure tokens, and perform deployment hardening review. `NEXUS_WRITE_TOKEN` alone is not a production-grade RBAC system.
5. Audit legacy English-only screens, report localization, and all KPI definitions.
6. Validate model/LLM configuration and measurable user-facing quality before claiming production AI.
7. Review permissions and licensing for resale of Cottonil-specific data, branding, and source files.
8. Build proper white-label organization settings and tenant isolation before selling as multi-tenant SaaS.

## Quickstart
Use Windows PowerShell inside project root. Install backend dependencies with `python -m pip install -r backend/requirements.txt`. Define `NEXUS_WRITE_TOKEN` and other required environment variables. Put authorized raw CSV files in `data/raw/` and run data preparation scripts per README. Start backend: `python -m uvicorn backend.app.main:app --reload --port 8000` (requires project-root Python path). Start frontend: `cd frontend; npm install; npm run dev`. See vite proxy configuration. If running tests, from project root use `$env:PYTHONPATH='backend'; python -m pytest backend/tests -q`.

This release is a focused, incremental V9 checkpoint. It is **not** a verified, complete implementation of the full V9 specification and should not be sold as production-ready software without closing the blockers.
