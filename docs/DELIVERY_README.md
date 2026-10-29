# Limited Verified Upgrade, not full Master Prompt completion

This archive contains the original V10 project and narrowly scoped improvements. It does not implement all 21 sections of the master prompt. Changes are deliberately honest and incremental.

## Running locally
Follow the project's existing README. In `frontend`, run `npm ci` and `npm run build` on a machine with npm registry access. For backend tests from project root run `PYTHONPATH=backend python -m pytest backend/tests -q`. Enabling auth and setting strong hashed users is required for even a restricted deployment; do not publish with default development configuration. Use separate isolated staging and production databases.

## Validation still required
1. Full npm/TypeScript/Vite build.
2. Manual dark/light and Arabic/English walkthrough on desktop and mobile.
3. Fix suite-level test DB isolation and optional PDF dependencies.
4. Security review with backend RBAC, rate limiting, audit events, secret management and unauthorized-access tests.
5. ML leakage-safe temporal backtests and actual model registry before claiming ML deployment.
