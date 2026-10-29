# Cottonil Nexus AI — Local LinkedIn demo with Ollama

**Scope:** a Windows **training/portfolio demonstration**, not a public production deployment or a validated live client system.

## 1. Get the local model working

Install Ollama for Windows from <https://ollama.com/download>. On the same Windows laptop as the FastAPI backend, open PowerShell **inside the extracted repo** and run:

```powershell
.\scripts\enable_ollama_demo.ps1
```

The script checks the Ollama server, starts it if necessary, pulls `qwen3:4b-instruct` (~2.5 GB model file) only when absent, tests real local inference with a harmless prompt, and updates these settings in a local, **gitignored** `.env`:

```dotenv
NEXUS_LLM_URL=http://127.0.0.1:11434/v1/chat/completions
NEXUS_LLM_MODEL=qwen3:4b-instruct
NEXUS_LLM_TIMEOUT=60
NEXUS_LLM_API_KEY=
```

Do **not** point this endpoint at a publicly reachable Ollama server; no public network exposure or client secret is needed.

## 2. Configure demo sign-in (once)

If `.env` did not already have a local account, generate a hash with:

```powershell
py scripts\make_user_hash.py
```

Enter a new demonstration password at the prompt, then copy the printed `pbkdf2$...` value into `.env`:

```dotenv
NEXUS_ENV=development
NEXUS_AUTH_ENABLED=1
NEXUS_USERS=demo:pbkdf2$...:admin
NEXUS_AUTH_SECRET=REPLACE_WITH_A_NEW_RANDOM_48_PLUS_CHARACTER_SECRET
```

For `NEXUS_AUTH_SECRET`, generate a unique random string rather than leaving the placeholder (e.g. `py -c "import secrets; print(secrets.token_urlsafe(48))"`). Do not publish `.env`, your password, login screen credentials, or any access tokens.

## 3. Start the app

```powershell
.\scripts\start_windows.ps1
```

Two local windows start: FastAPI on <http://127.0.0.1:8000> and Vite on the local port it prints (normally <http://127.0.0.1:5173>). Log in as `demo` using the demonstration password.

Ollama must remain running during the demo; the **first generation may be slower** while the model loads.

## 4. Prove Ollama actually participates

* Check **Ollama installed and serving:** `ollama list` and <http://127.0.0.1:11434/api/tags>.
* After login, open the Copilot screen. Its status should display `qwen3:4b-instruct` as detected.
* **Status alone does not prove generation.** Ask an evidence-backed question *after* ingesting authorized or clearly labeled synthetic demonstration data (for example, **"ما هو صافي المبيعات المسجل في البيانات التجريبية؟"**).
* Inspect the chat reply mode: **"شرح بمساعدة النموذج مع أدلة" / `grounded-llm`** means the response was generated using the LLM; **"إجابة من أدوات تحليل محددة" / `deterministic-fallback`** means Ollama was not used for that answer.
* A greeting or an unsupported question intentionally does NOT call the model. With **no ingested data**, most business queries give a truthful missing-data reply.

### Troubleshooting

* **Model unavailable:** run `ollama list` and `ollama pull qwen3:4b-instruct`, then rerun the setup script.
* **Copilot only uses fallback:** ensure `.env` was loaded before starting FastAPI; reboot both API and frontend after changing it. Ask about a metric actually present in the evidence store.
* **403 forbidden:** the user may have a branch-restricted scope; use an authorized local **admin** demonstration account rather than bypassing permissions.
* **Slow response / timeout:** close memory-intensive apps; use the model only for one short evidence-grounded question; check `NEXUS_LLM_TIMEOUT=60`.
* **401:** configure `NEXUS_USERS` properly and log in.
* **Frontend does not start:** run `npm ci`, `npm run test` and `npm run build` within `frontend`; do not record a broken page.

## 5. Before publishing the LinkedIn video

1. Show a brief executive overview, one functioning chart/table, one business insight with a valid source, and one actual Ollama-generated bilingual Copilot answer. Test **Arabic and English** before recording.
2. **Use only permission-approved, anonymized data or clearly labeled SYNTHETIC / DEMO DATA.** No real Cottonil customer records, sensitive KPIs, credentials, secrets or private branch information should appear publicly without explicit permission.
3. Avoid suggesting that hardcoded examples are factual Cottonil findings or that this is an enterprise-certified production deployment.
4. Run the demo **locally** and screen-record it. The fact that Ollama is local does not make its endpoint publicly accessible or provide public hosting for the app.
5. Optional caption: **"COTTONIL NEXUS AI — training project prototype. React + FastAPI analytics and locally hosted Ollama Copilot. Demonstrated using labeled synthetic/approved data. Not a production release."**

## What has and has not been verified in the source delivery

The source already contains the compatible Ollama adapter. In this Ollama-demo package, its integration is covered by additional **mocked** tests. **Real Ollama inference, frontend build, browser E2E and actual Windows startup must still be run on the user's machine**. Do not claim these were verified here.

## Optional Multi-Agent extension (implemented)

The current prototype adds a **bounded five-role orchestration pipeline**, an expandable per-reply execution trace, and a completely optional **synthetic-only dataset**. Use `py scripts\seed_synthetic_demo.py` to create a dedicated database if you do not have approved data. Set the printed `NEXUS_DB` and `NEXUS_RAW` paths in your ignored `.env` before starting the Windows launcher. **Never claim synthetic figures are client results.**

For the architecture, permissions, evidence routing, and verified QA, read `docs/MULTI_AGENT_ARCHITECTURE.md`. For a ready-to-record Arabic walkthrough, read `docs/MULTI_AGENT_DEMO_SCRIPT_AR.md`.
