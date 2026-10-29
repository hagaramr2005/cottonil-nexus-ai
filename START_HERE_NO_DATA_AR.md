# COTTONIL NEXUS AI — Full Source, No Client Data

## What this ZIP is

Source-code snapshot of the previously repaired V13 project, with React/Vite frontend, FastAPI backend, business analytics and Copilot modules, scripts, test code, design assets, configuration example and documentation. The **OpenCode changes made later on the user's own laptop are not included unless already in this snapshot**.

## What is intentionally missing

- `data/nexus.sqlite` (business database)
- `data/cottonil_original_source.zip` and raw CSVs
- `docs/screenshots/*.png` (screenshots of the real-data interface)
- Actual `.env` secrets, installed `.venv` and `node_modules`, downloaded ML datasets and trained models.

The archive contains `data/.gitkeep` and `data/raw/.gitkeep` only to show the expected directory structure. The app must not be expected to show real business metrics until authorized source data has been separately connected and ingested. The code is **NOT certified for production**.

## Before using OpenCode

1. Extract to a **new** folder. Do not overwrite newer local OpenCode edits; compare/merge carefully or copy the prompt into the latest local repository instead.
2. Read `OPENCODE_MASTER_ENTERPRISE_UPGRADE.md` in the project root and paste the prompt into OpenCode with the repository open.
3. Ask OpenCode to fix data-free startup, data-dependent tests, security and all business/UI workflows; do not accept claims of completion without the actual test logs.

## Development setup (PowerShell, project root)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
$env:NEXUS_LLM_URL="http://127.0.0.1:11434/v1/chat/completions"
$env:NEXUS_LLM_MODEL="qwen2.5:3b"
python -m uvicorn app.main:app --app-dir backend --port 8001
```

In a separate terminal:

```powershell
cd frontend
npm ci
$env:NEXUS_API="http://127.0.0.1:8001"
npm run dev
```

If newer local OpenCode code changed environment variables, ports or startup, follow its verified README. Install/use local Ollama separately if an LLM is desired. The model weights are not bundled.

## Test truthfulness

A data-free extraction of the repaired V13 source was tested and produced **65 passing, 4 failing backend tests**; all four failures were related to business data not included in this archive (sales mart, SKU profile, and expected metrics). The prompt directs OpenCode to replace those data-dependent assumptions with isolated synthetic test fixtures. Earlier results from a database-populated environment (69 passing) do **not** imply the no-data package passes all tests.

## Final company handover

This package is a **development source handoff**, not a production-ready client delivery. A real Cottonil production handover requires authorized data connection, reconciled KPIs, secure authenticated deployment, frontend build/E2E tests, database backups/restore, role/branch authorization, and actual company UAT sign-off.
