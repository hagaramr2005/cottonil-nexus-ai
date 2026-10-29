# V12 — Evidence-backed decision loop

This is a verified incremental feature, **not** certification of a complete enterprise AI platform.

## Added

- `POST /api/decision-loop/scan`: authenticated historical same-weekday MAD outlier detection. 8 prior comparator observations required; up to 12 used. No look-ahead; idempotent persisted evidence incidents.
- `GET /api/decision-loop/insights`: inspect ranked-by-recency findings, method, evidence, limitations and human-review recommendations.
- `POST /api/decision-loop/decisions/from-insight`: generate a **proposed** governed decision referencing the exact statistical evidence; never auto-approve or change business data.
- `POST /api/decision-loop/decisions/{id}/measure`: authenticated descriptive before/after net sales measurement, available only after implementation. Requires complete, non-overlapping daily windows; records source limitations and excludes causal claims.
- `GET /api/decision-loop/decisions/{id}/measurements`: persisted outcome evidence.
- Frontend ML & Decision Center can launch a scan, inspect findings, propose decisions, and request a documented before/after comparison.

## Verification

`PYTHONPATH=backend python -m pytest backend/tests -q --disable-warnings`: **47 passed** (on build machine, 2026-10-28). Four new tests exercise detection, persistence idempotency, authorization, approval sequencing, measurement, and invalid windows. See test file `backend/tests/test_decision_loop.py`.

## Truth and security caveats

- Detecting an anomaly is not root-cause analysis. Recommendations only propose investigation. Source daily_sales is `warning` reliability in the current metric registry.
- A before/after mean is descriptive; does **not** establish incremental impact or causality. No seasonal/control group adjustment.
- `NEXUS_WRITE_TOKEN` is a development-grade shared secret, not enterprise identity-based RBAC; configure it securely. Users lacking the token cannot mutate via these endpoints. Read APIs have no branch-specific authorization.
- A hosted LLM, advanced supervised forecasting, a trained risk classifier, reliable business optimizer, full production authorization and end-to-end verified browser build are **not delivered** by this patch.
- The ML & Decision UI was wired to the new API but its complete production build and browser E2E verification have not been established in this environment.

## Operator steps

1. Start backend following `README.md`, with `NEXUS_WRITE_TOKEN` set. Existing SQLite data is retained.
2. Open ML & Decision Center, supply the write token, run evidence scan.
3. Review source caveats, propose a decision with an existing case ID, advance it through governed approval and implementation.
4. Measure with complete date windows *only after implementation*; report it as an observed association, not business impact caused by the decision.
