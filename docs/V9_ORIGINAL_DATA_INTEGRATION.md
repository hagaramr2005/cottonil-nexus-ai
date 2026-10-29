# V9 Original Cottonil Data Integration — validated checkpoint

## Included
- All 25 original CSV files preserved, unmodified, within `data/cottonil_original_source.zip`. Running `scripts/start_windows.ps1` extracts them into `data/raw/` if missing. The supplied SQLite database is already prebuilt.
- Prebuilt SQLite database in `data/nexus.sqlite`, with datasets, metrics, anomaly investigations, evidence samples, daily/branch/SKU aggregations, `sales_mart`, and `sku_profile`.
- Data originated from the supplied archive, not from the 23-slide product vision PDF.

## Reconciliation
- Source CSVs processed: 25.
- Sales orders: 540,000.
- Sales order line items: 1,138,536.
- Sum of `net_line_EGP`: EGP 841,274,176.32.
- Aggregated sales mart net: EGP 841,274,176.32 (reconciles within rounding).
- Sales mart: 768,977 aggregated cells, 695 SKU profiles, 97 reported months.
- Purchase quantity / sold quantity: approximately 99.88; **not a financial loss, not validated as equivalent units**.
- 38,040 source orders were dated before branch opening dates in the joined branch records; needs investigation rather than assigning causality.

## Verification
- SQLite integrity check: `ok`.
- Core data-backed tests: `24 passed`, run with `NEXUS_DB` set to this database and excluding `test_api.py`.
- `test_api.py`: `6 passed` when run separately.
- Running all tests in one pytest command is currently not supported reliably due to `test_api.py` globally setting `NEXUS_DB` at import-time; fix fixture isolation before claiming a green unified run.
- **Frontend production build and end-to-end browser run not validated here.** No claim of sale-ready security or production readiness.

## Run locally (Windows PowerShell)
From project root (extract raw CSV files first only when needed for source-level inspection or reprocessing):
```
.\.venv\Scripts\python.exe scripts\import_archive.py data\cottonil_original_source.zip
```
```
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:NEXUS_DB=(Resolve-Path 'data\nexus.sqlite').Path
$env:NEXUS_WRITE_TOKEN='replace-with-a-long-random-secret'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000
```
In another PowerShell session:
```
cd frontend
npm install
npm run dev
```
Then open http://localhost:5173.

The database is a data analysis checkpoint, not a multi-tenant or production deployment. Protect it as business data. Update credentials and inspect access rules before any external hosting.
