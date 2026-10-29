# Deployment and Operations

**Status:** Deployment definitions implemented; Docker images, network/edge TLS, production permissions and browser behavior **not validated in this environment**.

## Local Windows, including data-free startup
1. Install Python 3.11+/3.12, Node 20+/22. Copy `.env.example` to `.env`; set private user/password hashes and a unique `NEXUS_AUTH_SECRET`. For local-only unauthenticated trial, set `NEXUS_AUTH_ENABLED=0`, but never expose a development server publicly.
2. From the repository root run `powershell -ExecutionPolicy Bypass -File scripts/start_windows.ps1`. This installs dependencies and starts localhost backend/frontend. **No CSV is required**; data-dependent APIs report missing inputs.
3. To ingest approved private source CSVs run `scripts/start_windows.ps1 -Archive 'C:\private\source.zip'` or import/ingest manually. The launcher no longer searches Downloads or silently imports files.
4. UI: `http://127.0.0.1:5173/`, API health: `http://127.0.0.1:8000/api/health`.
5. Secrets are inherited from the parent process environment; Windows script does not embed credentials or pass passwords as command arguments. Do not share screenshots/logs containing private values.

## Docker deployment (staging blueprint, not public production)
- Docker Compose >=2.30 is required for `env_file.format: raw` (literal `$` in PBKDF2 password hashes). Set `.env` with valid production values, including TLS-origin CORS; see `.env.example`.
- On Linux, make local `data/` readable/writable by the backend container UID **10001** using appropriate host volume permissions, without making it world-writable.
- `docker compose build && docker compose up -d`. The front end listens **only** on `127.0.0.1:8080` and proxies `/api` to the internal FastAPI service. The API container isn't directly published.
- **Production must have a separate trusted HTTPS reverse proxy** to `127.0.0.1:8080`, with valid certificate, correct external origin and forwarded HTTPS/proxy headers. `Secure` session cookies won't work for end users over plain HTTP. Don't expose this Compose stack directly as an internet production service.
- Backend container runs without root, drops capabilities, reads source-only image with a mounted data volume, and has a health check. Build reproducibility and full file-system permission checks are still unverified.
- No real data, active secrets or populated DB should be baked into Docker layers.

## Backup and restore
Use `python scripts/db_ops.py backup data/nexus.sqlite /secure-backups/nexus-YYYYMMDD.sqlite`. The script uses SQLite's consistent backup API, checks DB integrity and prints SHA-256. Do NOT store private backups with source or in shared public storage.

To restore: **stop all backend processes first**, securely move the damaged target DB and WAL/SHM aside, then run `python scripts/db_ops.py restore /secure-backups/nexus-YYYYMMDD.sqlite data/nexus.sqlite --force`. Restore deliberately refuses to overwrite an existing DB. Check DB integrity, application readiness and reconciled totals before reopening access. Encrypt and restrict backups; rehearse recovery on staging.

## CI and release gate
`.github/workflows/quality.yml` defines Python full tests, `pip-audit`, frontend Vitest/TypeScript/Vite build, `npm audit`, and a Chromium Playwright data-free smoke. This workflow **has not executed** in this sandbox. Configure hosted CI secrets and network policy and require green checks before release.

## Operations
- Use TLS, private firewall, unique secrets, scoped per-user permissions, safe password rotation and approved admin provisioning.
- Monitor backend health, data completeness, export/audit events, login failures, auth revocations, disk space and SQLite growth.
- Keep ingestion and rebuild jobs controlled; take a verified backup before schema/data changes.
- During incidents, revoke sessions, disable access at the edge and preserve audit/DB snapshots for independent investigation.
- Review `SECURITY_READINESS.md`, `DATA_CONTRACT_AND_RECONCILIATION.md` and `KNOWN_LIMITATIONS.md` before acceptance.
