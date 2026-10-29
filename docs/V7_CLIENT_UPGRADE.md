# V7 Client Storytelling Upgrade — implemented checkpoint

## Changes shipped in this ZIP

- New deterministic, read-only API endpoints: `/api/story/metrics/{metric_id}?lang=en|ar`, `/api/story/chart/daily-sales?lang=en|ar`, and `/api/story/briefing?lang=en|ar`.
- KPI explanation drawer added to main executive metrics; explanations cover meaning, assessment limits, change limitations, next action, trust and source references.
- Chart explainer added to the executive sales timeline. It compares the first and last *observed dates*, not full periods, and identifies maximum and minimum observed days.
- Client-first executive briefing with metric evidence, unresolved investigations, source reliability flags and deterministic action guidance.
- Minimal executive story mode links evidence to investigations and the executive report; **not** a complete guided full-screen presentation.
- Arabic translations for new features and selected dashboard elements; RTL drawer/layout refinements; persist chosen language in localStorage.
- No new ML models, LLM inference, numeric changes, Computer Vision, GPU or unauthorized data modifications.

## Important boundaries

This archive does NOT contain original Cottonil CSV files, a production SQLite database, credentials, or trained model weights. Live outcomes cannot be audited here. New APIs read the same local tables created by the existing ingestion workflow. No fabricated financial values or demo scenarios are shipped. The chart explainer uses an observed first-last date difference and explicitly warns against treating it as a growth rate or causal explanation.

Backend integration is verified using isolated synthetic **test-only** SQLite databases, which are not shipped as business records.

### Verification status

- Python compilation: successful.
- Isolated new test suite and V6 transformation tests: 4 passed.
- Existing suite against dataset-less ZIP: 18 passed, 4 failed (existing tests expect a populated ingested database and sales mart). These failures were present before changes and were not fixed by inventing datasets.
- Frontend production build: **NOT verified**. `npm install` timed out in this environment. Run locally with Node and network access.
- Browser screenshots / Playwright tests: **NOT executed**; frontend dependencies and running application data were unavailable.
- RTL coverage: new components and primary header/dashboard labels improved. **Full Arabic localization of all existing tabs remains unfinished.**
- Secure production authorization: **NOT implemented**. Existing local write-token scheme requires production authentication hardening.
- Model Center: not present in the supplied V6 navigation; no model artifacts deleted.
- Optional existing LLM adapter: untouched; responses remain explicitly labeled and rely on approved deterministic analytical evidence. No additional agentic tooling implemented.

### Windows quick start

From project root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
# If you own the original Cottonil CSV archive, import and ingest it first:
.\.venv\Scripts\python.exe scripts\import_archive.py "C:\path\to\your\Cottonil_project.zip"
.\.venv\Scripts\python.exe scripts\ingest.py
.\.venv\Scripts\python.exe scripts\build_sales_mart.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000
```

Second PowerShell:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Backend tests: `$env:PYTHONPATH='backend'; py -m pytest backend/tests/test_storytelling_v7.py backend/tests/test_transformation_v6.py -q`

## Reference PDF feasibility assessment (23 visual pages)

Status codes: **existing/partial** means an established related module exists but not necessarily all reference concepts; **unsupported** means current archive does not establish reliable fields or results. This is a source-availability review, not validated end-to-end feasibility on the missing CSV archive.

| PDF page | Concept | Status and constraint |
|---|---|---|
| 2 | Executive dashboard | Partial: existing summary, new explanations and briefing; no audited performance targets. |
| 3 | Sales performance | Partial: sales mart, time/branch/product cuts; completeness cannot be verified offline. |
| 4 | Branch optimization | Partial: branch revenue is present; operational efficiency and justified optimization not established. |
| 5 | Warehouse & inventory | Unsupported for real-time stock: no demonstrated live inventory feed. |
| 6 | Customer segmentation | Unsupported until stable customer IDs, cohorts and permissible attributes verified. |
| 7 | Demand forecasting | Partial historic analytics; no validated production demand model established. |
| 8 | Logistics visibility | Unsupported for real-time logistics: no live milestones established. |
| 9 | Procurement | Partial purchase metrics, units unreconciled; supplier performance needs verified joins. |
| 10 | Returns & quality | Partial returns/refunds summary; defect causation requires more evidence. |
| 11 | ESG | Unsupported; emissions/energy/water sources not verified. |
| 12 | Expansion & site selection | Unsupported; external market/location data not established. |
| 13 | Pricing & promotions | Partial revenue analysis; causal elasticity and uplift not established. |
| 14 | Omnichannel | Partial channel sales mart; visits/conversions unsupported without funnel data. |
| 15 | Marketing ROI | Unverified attribution; no defended causal ROI. |
| 16 | Product profitability | Partial recorded margin; cost reconciliation required. |
| 17 | Workforce productivity | Unsupported; verified hours, shifts and service quality not established. |
| 18 | Smart replenishment | Unsupported for autonomous allocation without validated stock, lead times and constraints. |
| 19 | CLV & churn | Unsupported; no trained calibrated model or verified customer longitudinal keys. |
| 20 | Visual merchandising | Unsupported in non-CV MVP; no store planogram data demonstrated. |
| 21 | Shrinkage control | Partial investigation workflow; no confirmed physical shrinkage evidence. |
| 22 | Wholesale | Unsupported until B2B-specific account, distributor and sell-through data validated. |
| 23 | AI business assistant | Partial: deterministic approved Q&A; optional LLM adapter, no new agent orchestration. |

## P1/P2 backlog, not claimed delivered

Full bilingual translation audit, full guided story with deep links, context-aware AI tooling across pages, stronger recommendations, natural-language filters, report language parity, secure multi-user sessions, end-to-end browser automation and test screenshots.
