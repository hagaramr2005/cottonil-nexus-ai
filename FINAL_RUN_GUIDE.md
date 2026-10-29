# Windows local run guide

Open **Command Prompt** at the project root and run:

```cmd
scripts\start_windows.cmd
```

This invokes the bundled PowerShell script for a single process without permanently relaxing machine-wide execution policy. Its backend and frontend are launched on localhost. The script installs Python packages, executes `npm ci`, and opens backend/frontend terminals. Check both terminal outputs; startup is not confirmed by the presence of windows alone.

For test verification from project root, with the Python environment activated:

```cmd
set PYTHONPATH=backend
python -m pytest backend/tests -q
cd frontend
npm ci
npm run build
npm run test
```

For CSV import, see existing `README.md` and `START_HERE_NO_DATA_AR.md` for required inputs and ingestion commands. The supplied archive does not include raw CSVs; no live dashboard KPIs can be validated without them.
