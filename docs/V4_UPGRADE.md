# V4 Evidence Intelligence Upgrade — Implementation status

This is an **incremental upgrade to V3**, NOT a claim of complete implementation of the supplied product directive.

## Implemented

- `GET /api/intelligence/risk`: risk summary and evidence-aware signals linked to persisted investigation case IDs and actual metric trust classifications. These are **investigation leads** and are not calibrated predictions.
- `GET /api/intelligence/periods`: available reporting months from the existing source-derived Sales Mart.
- `GET /api/intelligence/compare?current=YYYY-MM&previous=YYYY-MM`: source-derived month comparison, percent change and largest product/branch/channel revenue movements. No causal inference.
- `GET /api/intelligence/sku/{sku_id}`: persisted source-derived SKU summary and explicit limits. No invented linkage from SKU IDs to mart product IDs.
- Frontend Risk Radar 2.0 with severity summaries and case drill-down, What Changed period selectors/contributors, and a richer SKU dossier.
- Four focused V4 API tests.

## Verification performed

- `pytest -q backend/tests/test_intelligence_v4.py`: **4 passed**, using an existing locally constructed Cottonil SQLite sales mart (97 months) as test database.
- Direct HTTP test of `/api/intelligence/risk`, `/api/intelligence/periods`, `/api/intelligence/compare` and a real SKU ID: **200 responses**.
- Backend files compiled with Python `py_compile`.
- **Frontend build unverified**: npm install timed out in this environment. Run `npm install` followed by `npm run build` on Windows.

## Explicitly not implemented by this upgrade

- Full auth/session/RBAC (V3 local token remains a development-only limitation).
- CV-trained fashion/defect models, embedding index and image-text consistency.
- True RAG or an evaluated agentic tool-calling LLM.
- Full case evidence graph, additional validated anomaly rule families, complete mobile/browser E2E tests, and full Arabic localization.

## Windows instructions

1. Make a backup of the existing V3 code and database (`data/nexus.sqlite`) before replacing files.
2. Extract the V4 ZIP. Use the original Cottonil archive to populate `data/raw` if needed:
   `python scripts/import_archive.py "C:\Users\PCCV\Downloads\Cottonil_project (3).zip"`.
3. Install backend requirements using `.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`.
4. Run `python scripts/ingest.py` only if initial ingestion has not been completed; run `python scripts/build_sales_mart.py` after initial ingestion.
5. Run the backend using `.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000`.
6. From `frontend`: `npm install`, `npm run build`, `npm run dev`.
7. Open `http://localhost:5173` and inspect the Risk Radar, What Changed and SKU Autopsy pages.

**Do not copy V4's empty `data/` folder onto an existing populated V3 database; preserve local generated data and decisions.**
