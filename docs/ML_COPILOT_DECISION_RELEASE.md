# ML, Copilot and Decision Engine — Incremental Implementation

Date: 2026-10-28

## Working features

- `POST /api/decision-ai/ml/train` (requires `NEXUS_WRITE_TOKEN`): checks a contiguous observed daily revenue series, evaluates seasonal naive (7 days) against last-observation naive with an unshuffled 28-day holdout, records dataset SHA256 and numeric metrics in SQLite.
- `GET /api/decision-ai/ml/runs`: persisted evaluation registry (not a production MLflow registry).
- `GET /api/decision-ai/ml/forecast?days=7`: produces 1–28 forecast points from the selected historical baseline, only if source fingerprint is unchanged. No calibrated intervals; not deployed production forecasts.
- `POST /api/decision-ai/copilot/query`: read-only deterministic, allowlisted structured intents: metrics, open_cases, decisions, model_status. This is NOT an LLM or free-text/RAG assistant.
- `POST /api/decision-ai/decisions`, `PATCH /api/decision-ai/decisions/{id}`, `GET /api/decision-ai/decisions` and `/history`: authorization token, verified case and metric references, state transition validation and append-only event trail. A captured measurement statement is NOT verified causal attribution.
- Frontend sidebar includes a new ML & Decision Center, with forecast controls, copilot evidence retrieval and decision workflow UI. React compilation was NOT verified due to npm installation timeout.

## Verification

- `PYTHONPATH=backend python -m pytest backend/tests -q` => **43 passed** (39 pre-existing + 4 new).
- `python -m compileall -q backend/app` => success.
- Evaluated against supplied actual daily aggregate (read-only): 2,922 points; 28-day Sep 21–Oct 18 2026 holdout; seasonal-naive MAE **106,405.3454 EGP/day**, last-observation MAE **118,157.3011 EGP/day**, WAPE **13.5462%**. These are observed-sales backtest metrics and not prediction accuracy on future unknown data. Sales reliability remains *warning*.
- `npm ci --no-audit --no-fund --prefer-offline && npm run build` => timed out during dependency installation; frontend build and browser tests **unverified**.

## Important limitations and follow-up engineering work

- Model evaluation uses only a single historical holdout rather than rolling-origin backtesting; no uncertainty interval calibration, drift alerts, or advanced gradient boosting model.
- The workflow uses a shared write token, not per-user RBAC/approvals or sufficiently strong production identity; ensure `NEXUS_WRITE_TOKEN` configured for local testing only.
- ML and decisions tables are created idempotently at request time; convert to versioned database migrations in a production deployment.
- The new UI does not yet use role-based access, and has no verified browser E2E coverage.
- AI Copilot lacks free-form language parsing, LLM/RAG, citations into source documents, branch-level scoping, and conversation persistence.
- Decision measurement is human-supplied narrative, not independently validated before/after control analysis.
- Do not claim this is production-ready or that all requirements from MASTER IMPLEMENTATION PROMPT have been met.

## Local usage

From repository root:

```bash
pip install -r backend/requirements.txt
PYTHONPATH=backend NEXUS_WRITE_TOKEN=your-local-secret uvicorn app.main:app --host 127.0.0.1 --port 8000
# In a separate terminal
cd frontend
npm ci
npm run dev
```

Enter the same `NEXUS_WRITE_TOKEN` in ML & Decision Center to run model evaluation or mutate decision states. Never expose the token on a shared production environment.
