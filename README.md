# COTTONIL NEXUS AI — Security & Data Integrity Candidate

**Status (2026-10-29): NOT PRODUCTION READY.** Upgraded source repository from verified Snapshot 2 baseline; no real Cottonil data or secrets included.

## What is implemented
FastAPI + SQLite backend, React/Vite frontend source, deterministic bilingual Copilot and optional unverified LLM connector, scoped sales intelligence, source integrity/provenance, investigation rule ledger, reports, governed decisions, secure cookies/CSRF, role-based permissions, persisted audit/sessions, Docker/Windows/CI/backup blueprints.

## Verified today
**113 backend tests passed** after updates, including synthetic branch-isolation and data integrity checks. Current frontend Vitest/TypeScript/Vite build and Playwright **NOT RUN** because npm dependency installation timed out. Live customer data and Ollama tests **BLOCKED**. Historic Snapshot 2 documented 7 Vitest and successful build, which do not validate these updated files.

## Quick start (Windows)
```powershell
Copy-Item .env.example .env
# Edit .env: set NEXUS_AUTH_SECRET and NEXUS_USERS with real password hashes (see scripts/make_user_hash.py)
.\scripts\start_windows.ps1
# Optional approved client archive, separately: .\scripts\start_windows.ps1 -Archive 'C:\secure\client.zip'
```
The application can run without business CSVs. Development stays on localhost. Do NOT use unauthenticated mode or HTTP for company data.

## Optional LOCAL Ollama demo (not production validation)
```powershell
# Install Ollama for Windows separately (https://ollama.com/download)
.\scripts\enable_ollama_demo.ps1
.\scripts\start_windows.ps1
```
The setup script pulls **qwen3:4b-instruct** if missing, tests live local inference, and updates a **gitignored** `.env` without changing authentication credentials. An actual model test has not been run in this delivery environment. See `docs/LINKEDIN_LIVE_DEMO_OLLAMA_AR.md`. **Only evidence-backed business questions call Ollama; greetings and missing-data queries use deterministic responses.**

## NEW — Bounded Multi-Agent Copilot (portfolio implementation)
Five specialized software roles now run in a real read-only workflow: Supervisor, Sales Analyst, Risk Investigator, Grounding & Safety Reviewer, and optional Ollama Narrative Agent. The chat response includes `agent_trace`, displayed in an expandable UI panel. These are deterministic agents plus **one optional LLM**, not five autonomous language models. See `docs/MULTI_AGENT_ARCHITECTURE.md` and `docs/MULTI_AGENT_DEMO_SCRIPT_AR.md`.

For a **clearly labeled, isolated SYNTHETIC demo** only:
```powershell
py scripts\seed_synthetic_demo.py
# Point gitignored .env at the two printed demo paths, then restart
```
Never present synthetic fixture metrics as actual company performance.

## Test
```bash
PYTHONPATH=backend python -m pytest backend/tests -q
cd frontend && npm ci && npm run test && npm run build
```

## Key docs
- `docs/MULTI_AGENT_ARCHITECTURE.md` — actual design, Mermaid data flow, API contract, security and validation
- `docs/COTTONIL_MULTI_AGENT_ARCHITECTURE.pdf` — three-page visual architecture handout
- `docs/MULTI_AGENT_DEMO_SCRIPT_AR.md` — Arabic LinkedIn demo walkthrough
- `docs/AUDIT_BASELINE.md` — baseline and verified changes
- `docs/QA_REPORT.md` — actual tests versus unverified checks
- `docs/SECURITY_READINESS.md` — security controls and gaps
- `docs/DATA_CONTRACT_AND_RECONCILIATION.md` — source and investigation predicates
- `docs/DEPLOYMENT_AND_OPERATIONS.md` — TLS, startup, backup/restore and CI
- `docs/CLIENT_HANDOVER.md` — acceptance process
- `docs/RELEASE_NOTES.md` — version and compatibility changes
- `docs/KNOWN_LIMITATIONS.md` — production blockers

**Production verdict: NO-GO** until networked frontend builds, browser E2E, deployment/rollback, vulnerability evaluation, client data reconciliation and security sign-off are complete.
