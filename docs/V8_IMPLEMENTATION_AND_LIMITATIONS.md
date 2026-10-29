# Cottonil Nexus AI V8 — client intelligence continuation

## Implemented in this checkpoint
- Added `/api/client/recommendations`: advisory cards derived solely from recorded unresolved cases and metric trust states. Supports `lang=ar|en`, bounded `limit`, evidence references and explicit human-review status. No invented savings or automated decisions.
- Added `/api/client/ask`: bounded context-aware, read-only analytical assistant accepting `page`, optional validated `case_id`, `sku_id`, or `metric_id`; includes source references and differentiates observations from hypotheses. It does not translate arbitrary natural-language requests to SQL and does not claim an LLM is active.
- Added **Action Center** in client navigation with grounded action cards and working links to investigations and metric passports.
- Added client context analysis view alongside existing LLM/deterministic analyst UI and improved selected-case propagation.
- Maintained V7 KPI explanations, chart explanations, briefing, and prior modules.

## Honest QA summary
- `PYTHONPATH=backend python -m pytest backend/tests/test_client_v8.py backend/tests/test_storytelling_v7.py -q` — 6 passed.
- Full backend suite: 24 passed, 4 failed. Old failures depend on absent original Cottonil ingested data and/or sales mart. No CSV or original database is included in the submitted source ZIP.
- Frontend production build **not verified**: npm installation failed due to DNS error `EAI_AGAIN registry.npmjs.org`; no fabricated build claim.
- No browser E2E screenshots were produced in this environment.
- Arabic translations for existing legacy dashboard pages remain incomplete, though new action center is bilingual and V7 language persistence is retained.
- Full executive story presentation remains a V7 guided prototype rather than a complete slideshow journey.
- LLM remains optional and unverified until configured by an operator; new context API is deterministic, not a real agent loop.

## Windows commands
```powershell
cd cottonil-nexus-ai
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
python -m pytest backend\tests\test_client_v8.py backend\tests\test_storytelling_v7.py -q
# Ingest only with original licensed CSV files copied to data\raw, then consult README for mart creation
uvicorn app.main:app --reload --port 8000
# Separate terminal
cd frontend
npm install
npm run build
npm run dev
```

## Business-evidence boundaries
Reference PDF is a vision illustration. Its graphs and financial figures are not treated as actual results. Recommendations are proposed checks, not savings estimates. Metrics and SKU facts are read from current backend SQLite source-derived tables at request time. Existing CSV datasets are not modified.

## Remaining sign-off requirements
1. Restore original CSVs and build the sales mart, verify KPI reconciliation and all pre-existing tests.
2. Run production frontend build and browser E2E on Windows with dependencies available.
3. Complete legacy-page localization and RTL audit on desktop/mobile.
4. Verify role-based separation and backend authorization before exposing internal technical pages to clients.
5. Validate cross-workspace drilldowns and report contents against the full client dataset.
