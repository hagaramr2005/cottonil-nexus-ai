# V6 — Evidence Intelligence checkpoint

## Scope decision
Computer Vision is excluded from this MVP. Catalog Detective and Textile Quality AI were removed from the main navigation, but previous source files/scripts remain available for later work. No GPU, Kaggle, or scraping is required.

## Implemented
- Added `backend/app/transformation.py` and registered the router in `backend/app/main.py`.
- `GET /api/transform/passports`: metric definitions, trust qualifications and cross-links to cases.
- `GET /api/transform/anomalies`: bounded rolling median/MAD branch-month revenue alerts; statistical leads, not certified business issues.
- `POST /api/transform/anomalies/open`: token-protected persistent case creation with stable case IDs and case event, avoiding duplicates.
- `GET /api/transform/revenue-xray`: filtered monthly change and additive branch contributions with reconciliation indicator.
- `GET /api/transform/graph/sku/{sku_id}`: bounded verified SKU-to-source relationships, no invented joins.
- Frontend navigation was changed to focus on Anomaly Detective, Revenue X-Ray, Data Reliability Passport, Retail Knowledge Graph, Decision DNA and AI Investigation Copilot. Added read-only visualizations for anomaly signals, passport and bounded SKU graph.

## Not complete
- Frontend production build could not be completed in this environment due to dependency installation timeout. Test on Windows with `npm install && npm run build`.
- Attempted full CSV ingestion timed out in this environment. Dataset ingestion was previously demonstrated on the user's Windows environment; V6 analytical results on the complete data were NOT verified here.
- Knowledge graph is a bounded lineage explorer, NOT a full Cytoscape graph.
- No secure production session-auth / RBAC. Write-token is development-only and remains in existing UI flows.
- AI Copilot is still the existing deterministic and optional OpenAI-compatible adapter; no LangGraph, agent tools, or broad RAG were added.
- Decision DNA full lifecycle, richer investigative timeline, and reporting upgrades remain unfinished.
- Seasonal baselines and false-positive rates are not validated; anomalies require human investigation.

## Windows setup (new folder)
In PowerShell from the V6 project root:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe scripts\import_archive.py "$HOME\Downloads\Cottonil_project (3).zip"
.\.venv\Scripts\python.exe scripts\ingest.py
.\.venv\Scripts\python.exe scripts\build_sales_mart.py
$env:NEXUS_WRITE_TOKEN = 'change-this-local-dev-secret'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
In a separate PowerShell:
```powershell
cd frontend
npm install
npm run build
npm run dev
```
`/api/transform/anomalies`, `/api/transform/passports`, `/api/transform/revenue-xray?current=2026-10&previous=2026-09` are available after ingesting the dataset and building the mart.

## Preservation
Original CSV sources must remain unmodified. Never replace existing `data/nexus.sqlite` without backing it up; this ZIP deliberately excludes any live database, original CSVs, model weights, and secrets.
