# Cottonil Copilot repair — V13 snapshot patch

**Source of truth:** `COTTONIL_NEXUS_AI_V13_SECURITY_HARDENED_NOT_YET_PRODUCTION.zip` supplied earlier in the conversation. The user's later, OpenCode-modified working directory **was not available here**. This is **not** a verified repair of that newer directory. Review and merge this patch; never overwrite newer changes blindly.

## Implemented changes in this V13 snapshot

- Introduced bounded `/api/copilot/chat` and `/api/copilot/status` endpoints.
- Normalized frontend API paths so a caller supplying `/api/...` or `/api/api/...` cannot double-prefix the proxy URL.
- Routed Arabic and English greetings and explicit language-switch requests independently of analytical tooling.
- Preserved the original historical role-based access restrictions, including admin-only write/POST behavior in auth-enabled mode. **Viewer access to chat remains restricted** to preserve V13's existing policy.
- Added bounded, caller-supplied conversation history for follow-up reference resolution. Case ordinal references are resolved deterministically against stored cases; history is never treated as factual evidence.
- Business metrics and cases are fetched from the existing SQLite ledger only. The LLM can explain those records but cannot directly write records, execute SQL, or choose its own URL/model.
- Exposed response mode and provider failure reasons, with a non-LLM fallback. Provider availability is based on an Ollama model list check, not proof of answer quality.
- Updated React Copilot to call new endpoints, show a distinct model/response mode, render auto-direction text, show user-friendly evidence, clear the current chat, support short greetings, and preserve current-page/case identifiers.
- Added frontend API path regression tests, backend Copilot tests, and a PowerShell local read-only smoke-test helper.

## Verification actually performed here

- `PYTHONPATH=backend pytest -q backend/tests --disable-warnings` — **69 passed**, including existing security/production tests and 18 new Copilot tests.
- Node's TS stripping engine executed `frontend/src/apiPath.ts` and verified all test paths normalize to one `/api` prefix.
- Python `compileall` compiled the updated backend modules.
- **Not verified:** TypeScript production build, Vitest, Playwright browser tests, Windows runtime, real local Ollama Qwen integration. `npm ci` could not complete in the container because dependency retrieval stalled. Do not report these as passing.

## Scope limitations / deferred requirements

- This snapshot does **not** provide durable, per-user conversation storage or an authenticated conversation-history database. Conversation history exists only in the active React chat and is submitted as bounded, untrusted context. Do not claim persistence across refreshes or devices.
- Dashboard context includes the current page and selected investigation; date range, branch and product filters are **not yet** captured and independently revalidated.
- This release does **not** implement unrestricted conversations, agentic free-form SQL, streaming, or autonomous decisions.
- Prompt injection resistance is *risk reduction*, not a guarantee against model-originated hallucinations. Check source chips and original data; model answers are not independently fact-checked.
- The raw `svg` strings in the user's browser-text transcript may reflect screenshot/text extraction of Lucide icons. That issue cannot be proven or fixed against the unavailable OpenCode-specific frontend. The V13 snapshot already uses Lucide icon components.
- The original `GET /api/api/copilot/status` 404 was seen in the **newer local log**, but that endpoint did not exist in the archived V13; its precise root cause cannot be proven without the newer source.

## Local startup (after review/merge)

From the repository root, with your existing Python venv:

```powershell
.\.venv\Scripts\Activate.ps1
$env:NEXUS_LLM_URL='http://127.0.0.1:11434/v1/chat/completions'
$env:NEXUS_LLM_MODEL='qwen2.5:3b'
python -m uvicorn app.main:app --app-dir backend --port 8001
```

In another terminal:

```powershell
cd frontend
$env:NEXUS_API='http://127.0.0.1:8001'
npm install
npm run dev
```

Then in another terminal from the repository root:

```powershell
.\scripts\verify_copilot_v14.ps1 -ApiBase 'http://127.0.0.1:8001' -FrontendBase 'http://localhost:5174'
```

Use the actual Vite port printed in the terminal. Authentication-enabled setups require an admin bearer token in `NEXUS_TEST_BEARER`. Run backend tests and `npm run build` on Windows before declaring success.

## How to merge safely into OpenCode's modified directory

1. Back up the entire newer working directory (including `.env`, datasets, and local work; never commit secrets).
2. Inspect the unified `COTTONIL_COPILOT_V13_PATCH.patch` against the newer code. Some chunks may conflict since the patch targets archived V13.
3. In the project root, run `git apply --check <path-to-patch>`. Apply only if this succeeds; review diffs. **Never use `git apply --reject` or force-overwrite source files to bypass conflicts.**
4. If check fails, cherry-pick the concepts and test cases into OpenCode's latest code rather than overwriting it.
5. Re-run regression tests, actual model smoke tests and a browser interaction test against the local working directory.
