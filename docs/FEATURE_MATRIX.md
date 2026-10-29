# Feature Matrix — Measured Delivery Status

| Requirement | Backend | Frontend | Data | Tests | Status |
|---|---|---|---|---|---|
| Dark/light theme | n/a | Implemented token switching + persistence | n/a | Build pending | Partially verified |
| Bilingual UI | n/a | Existing localization | n/a | Prior tests included | Existing; not newly verified |
| Authentication | Existing opt-in token system | Login + fail-closed status update | Environment config | Targeted backend tests passed | Partial / not enterprise ready |
| Source KPIs and lineage | Existing metrics | Existing dashboard | SQLite populated | Partial | Source trust warnings persist |
| Reconciliation approval | Existing cases only | Existing investigation views | Source samples | Not verified | Incomplete |
| Return and branch fairness | Existing analytics portions | Existing views | CSV and marts | Full suite fails | Partial |
| Forecasting/model registry | Unverified | Not added | Daily sales available | Not run | Not verified |
| Anomaly detection | Existing modules | Existing anomaly page | Available | Targeted tests passed | Method must be audited |
| AI Copilot | Deterministic contextual module | Existing Copilot | Metric ledger | Partial | Not full autonomous AI agent |
| Decision outcome cycle | Existing limited case decisions | Existing UI | SQLite | Not verified | Incomplete |
| Enterprise report and alerts | Partial | Partial | SQLite | PDF tests blocked | Incomplete |
| Enterprise RBAC | Viewer/admin only | Admin conditional UI | No branch scopes verified | Auth tests passed | Incomplete |
