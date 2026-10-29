# Quality Assurance Report — 2026-10-29

**Test scope:** Code in supplied Snapshot 2 plus current release modifications. All API integration tests use transient SQLite and, where needed, explicitly labeled synthetic CSV fixtures. Never interpret fixture numbers as company sales.

| Verification | Result | Evidence / qualification |
|---|---|---|
| Original backend baseline, single pytest session | PASS: 86/86 | `PYTHONPATH=backend python -m pytest backend/tests -q` before changes |
| Snapshot 3 security milestone | PASS: 91/91 | Session auth, audit, branch access, RBAC, cookie/CSRF, production config |
| Earlier release backend regression | **PASS: 98/98** | Earlier full pytest run, before optional Ollama and multi-agent additions |
| Multi-Agent extension backend regression | **PASS: 113/113** | Current full pytest session, synthetic tests including workflow and safe demo seeder |
| Updated Copilot.tsx syntax check | PASS | Transpiled using installed global TypeScript; NOT a complete type-check or bundler build |
| Changed Python module syntax | PASS | `python -m compileall` on app/scripts |
| Synthetic findings gating | PASS | NEX-001/002/003 absent when predicates false; source-provenance entries exist |
| Missing CSV suppression | PASS | Absent purchase/marketing sources suppress dependent metrics |
| Branch SQL isolation | PASS | Synthetic `SYN-B1` and `SYN-B2`, filtered query and branch rejection |
| Prompt injection output numeric claim rejection | PASS | Synthetic mocked model asserts unsupported 999000 claim is discarded |
| Session expiration / logout revocation | PASS | Token expiration legacy test and new revocation regression |
| CSRF / viewer write prevention | PASS | Role-bound writes and cookie CSRF tests |
| Export/auth/sensitive audit | PASS | Recorded in transient SQLite and queried in test |
| Backup/restore basic integrity | PASS | Synthetic SQLite copy, SHA-256, refusal to overwrite, guarded restore |
| Frontend TypeScript syntax-only transpilation | PASS | Previous 15-file parsing; changed Copilot.tsx independently parsed with global TypeScript; no type-check/build verified |
| Frontend Vitest current code | BLOCKED | `npm ci --offline` returned ENOTCACHED (missing yallist package), so not run. Prior Snapshot 2 report: 7 passing, **not re-run**. |
| Frontend TypeScript/build current code | BLOCKED | Unavailable dependency installation; no claim of successful frontend compilation |
| Playwright browser smoke current code | NOT RUN | Browser setup not verified; `e2e/test_release_smoke.py` added for CI |
| Docker deployment | NOT RUN | Definitions available; no executable runtime test in this session |
| Dependency vulnerability checks | NOT RUN | CI configured with `pip-audit` and `npm audit`; require live runners |
| Live LLM/Ollama, bidi/RTL visual QA | NOT RUN | Provider/browser not tested |
| Live company datasets / financial reconciliation | BLOCKED | Client datasets excluded from uploaded snapshot |

## Reproduction

```bash
PYTHONPATH=backend python -m pytest backend/tests -q
cd frontend && npm ci && npm run test && npm run build
# With app servers and Chromium: python -m pytest e2e/test_release_smoke.py -q
```

## Acceptance criteria before release
- Re-run frontend CI on networked runner and fix any build/test failures.
- Run Playwright on desktop/mobile, Arabic/English, viewer/admin/branch-user routes; capture screenshots and test login/logout.
- Provision TLS, scoped users, access controls and backups in staging. Verify cold start, CSRF, CORS, session revocation and audit persistence.
- Reconcile real ingested data and obtain Cottonil stakeholder sign-off for KPI definitions.
- Verify external dependency scan and perform an independent penetration test.

**Verdict: QA partially complete — release gate not satisfied.**

## Multi-Agent portfolio extension verification (2026-10-29)

- **PASS: 113 backend tests** from a full single-process run after the added role-based workflow and isolated synthetic seeder. No company database, real customer records or network Ollama provider were used.
- New `test_agent_workflow.py`: role registry, missing data, sales provenance, risk/case evidence, empty case list behavior, prompt injection fallback, invalid provenance suppression, narrative mock call boundary, branch user denial, exact unverified financial loss refusal and private request content omitted from trace.
- New `test_synthetic_demo_setup.py`: demo fixture creates in a new isolated directory, refuses overwriting it, and rejects execution with `NEXUS_ENV=production`.
- **PASS: TSX syntax-level parse** for changed `frontend/src/components/Copilot.tsx`, using global TypeScript 5.8.3.
- **BLOCKED: frontend dependency install**: `npm ci --offline` reported `ENOTCACHED` (missing `yallist@3.1.1` tarball). Therefore **no current `tsc -b`, Vitest, Vite build, React render, or Playwright pass is claimed**.
- **NOT RUN:** real Ollama inference, Docker runtime, Windows startup, user acceptance testing, real company data comparison.

**Portfolio demo verdict:** candidate for **local demonstration after Windows startup, browser UI and actual Ollama verification**. **Production verdict:** NO-GO.
