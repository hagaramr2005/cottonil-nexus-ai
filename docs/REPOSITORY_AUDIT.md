# COTTONIL NEXUS AI — Repository Audit (2026-10-28)

## Observed repository baseline
- Frontend: React 18, TypeScript, Vite, Recharts, Lucide; existing Arabic/English localization and numerous connected views.
- Backend: FastAPI, file-based SQLite, source-data ingestion, sales data marts, deterministic analytical services, export and case handling.
- Raw source archive and populated `data/nexus.sqlite` are included. These are not newly generated business figures.
- Existing anomaly and risk views and optional computer-vision integration require evaluating their actual endpoints and model artifacts; file presence is not evidence of trained ML deployment.
- Authentication is OPT-IN (`NEXUS_AUTH_ENABLED`), with HMAC bearer tokens and only viewer/admin roles. Not production IAM, branch-scoped RBAC, SSO, or hardened session management.

## Data availability and trust
- `daily_sales`: 2,922 rows, range 2018-10-19 to 2026-10-18.
- Local metric ledger includes net sales about EGP 841.27M but marks this metric `warning`, not `verified`.
- Purchase/sales units have unreconciled measurement scales; don't use as inventory or claim loss.
- Data contains evidence for analytics and reliability investigations, but is not proof of valid model-training labels for every proposed predictive target.

## Current test baseline
- `PYTHONPATH=backend python -m pytest backend/tests -q --disable-warnings`: 32 passed, 7 failed in this environment. Failures include missing PDF dependencies, missing sales mart when test suites share DB configuration, and an empty analyst result.
- Focused `test_auth_v10.py`, `test_product_v9.py`, and `test_intelligence_v4.py`: 12 passed.
- Frontend build NOT verified; `npm ci` could not complete within execution timeout here. Avoid claiming it passed.

## Actual change scope of this delivery
1. Persisted dark/light color-token system with system-preference fallback and pre-render initialization.
2. Theme switch in the authenticated/unlocked app header with bilingual accessible labeling.
3. Authentication-state verification changed to fail closed in the UI if backend returns an error or cannot be reached; no longer automatically presents an unauthenticated application.

## Risks and dependencies
- Production backend still has opt-in authentication and insufficient enterprise RBAC; enable and harden auth before exposing it.
- No complete event-sourced decisions, approved reconciliations, validated model registry, training pipelines, or comprehensive audit log were added here.
- Existing source and database archives are large; never treat this ZIP as a production deployment image.
- Test fixtures should have isolated temp DBs and deterministic sales-mart setup. PDFs require optional dependencies.

## Dependency map
Security and trustworthy data ingestion -> certified KPI services -> ML evaluation and registry -> insights and decision workflow -> alerts/reports -> end-to-end verification. Backend authorization must accompany every mutating or scoped feature, not follow it.
