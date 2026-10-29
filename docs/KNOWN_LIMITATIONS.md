# Known Limitations and Open Risks

| Priority | Area | Current limitation / required action |
|---|---|---|
| RELEASE BLOCKER | Frontend | Updated TypeScript/Vitest/Vite build could not run: `npm ci` timed out. Run in connected CI, correct errors and validate resulting artifact. |
| RELEASE BLOCKER | Runtime | Docker and Windows startup not independently executed in customer network. Validate real TLS front door, persistent volumes, cookies, CSRF, proxy headers, disaster recovery. |
| RELEASE BLOCKER | Company data | No original company CSVs provided. Financial/KPI correctness, source schema mapping, reconciliation and material business value remain unverified. |
| RELEASE BLOCKER | Security | No external vulnerability audit or pen-test pass, IAM/SSO, formal enterprise role review, or production operational sign-off. |
| HIGH | Branch controls | Scope-aware endpoints cover branches and sales mart/filters only. Other organization-wide data/cases/reports/Copilot evidence deliberately return 403 for branch-scoped users. |
| HIGH | Copilot | No prompt-injection proof; regex guard and deterministic tools reduce risk but generated LLM text is not fully fact-validated. No live Ollama connectivity checked. |
| HIGH | Data ingestion | Not fully atomic; downstream marts may be stale after source changes without a rebuild; duplicate detection and FK/cardinality validation incomplete. Use disposable staging DB per ingestion until corrected. |
| HIGH | Authentication | SQLite login throttle is basic; no MFA, account recovery, concurrent session governance, centralized session store, security notifications or enterprise key rotation. |
| HIGH | Audit | DB audit is modifiable by DB administrators; no append-only external sink, retention policies, evidence immutability or tamper detection. |
| HIGH | Dependency management | Python ranges not hash pinned, npm audit/pip-audit configured but unexecuted; Docker base image pinning/SBOM outstanding. |
| MEDIUM | Case rules | Threshold for NEX-001 (default 10) is heuristic; NEX-002 may double-count campaign credit; NEX-003 depends on metadata date correctness. Not proof of financial loss. |
| MEDIUM | Source lineage | Only first 10 samples per source, not full row-level lineage. No certified source-data control framework. |
| MEDIUM | CV | Model training, domain evaluation, licenses and actual checkpoint unavailable. UI must not represent CV feature as validated. |
| MEDIUM | UX | New frontend change not rebuilt in this environment; Arabic/English, RTL, responsive and 19-page regression require browser captures. |
| MEDIUM | Deployment | Compose has no TLS and exposes only localhost. Requires protected edge proxy and hardened production runbook, monitoring and backups. |

| PORTFOLIO | Multi-Agent | Added bounded deterministic role orchestration with a single optional LLM narrator, not an autonomous multi-model system. Workflow trace is not distributed observability; no live Ollama verification or adversarial certification in this delivery. |

**Status classification:** IMPLEMENTED ≠ TESTED ≠ CERTIFIED. Any missing/blocked item above remains open until independently evidenced.
