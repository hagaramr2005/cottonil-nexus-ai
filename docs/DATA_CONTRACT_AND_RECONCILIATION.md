# Data Contract and Reconciliation

## Scope and provenance
- The final ZIP intentionally contains **no** Cottonil CSV, populated SQLite, customer records, API credentials, or model checkpoints.
- Raw input directory: `data/raw`. Each ingested CSV is recorded in SQLite `datasets` with name, source SHA-256, row count, header columns, null counts and ingestion time. Original CSVs are not overwritten during an ordinary ingest.
- Calculated metrics record expression description, source filenames, trust (`verified`, `warning`, `unverified`, `blocked`) and last update. Metrics with missing source prerequisites are **removed**, not returned as false zero values.
- `GET /api/reconciliation/status` returns case detection results, required source lists, observed values, threshold, source hashes and evaluation time. This is an **investigation lead**, not confirmation of fraud, profit loss or causal attribution.

## Conditional detection logic
| ID | Required files | Condition to create case | Interpretation |
|---|---|---|---|
| NEX-001 | `purchase_order_items.csv`, `sales_order_items.csv` | sold quantity positive AND purchase/sold source-unit ratio >= `NEXUS_RECONCILIATION_RATIO_THRESHOLD` (default 10) | Mismatch to investigate, **not** comparable confirmed physical units |
| NEX-002 | `marketing_campaigns.csv`, `sales_orders.csv` | Sales order count positive AND summed campaign `orders_attributed` > sales order count | Attribution overcount signal; cross-campaign duplicates may be legitimate |
| NEX-003 | `sales_orders.csv`, `branches.csv` | At least 1 joined sales order earlier than that branch's stored opening date | Metadata/date consistency warning |

- Conditions are evaluated only on source data actually ingested. Cases are not generated from constants on empty data.
- Existing legitimate investigator decisions/events are preserved; obsolete pristine auto-seeded open cases are deleted after failed predicates. Review changed-data behavior before re-ingesting in production.
- Detection results and source hashes are persisted in `case_detection` and exposed for review.
- Observed ratio threshold is a **policy heuristic**, not a calibrated business/ML finding. Any claim of business loss requires UOM conversions, period consistency, inventory transfers, receipts, adjustments, returns and external financial reconciliation.

## Input assumptions / currently unsupported validation
- `branches.csv`: `branch_id`, `opening_date` in `MM/DD/YYYY`.
- `sales_orders.csv`: `sales_order_id`, `order_date` in `YYYY-MM-DD`, `branch_id`, `paid_total_EGP`.
- `sales_order_items.csv`: product/SKU IDs, branch ID, date, quantity, net/margin columns as modeled by `core.ingest`.
- `purchase_order_items.csv`: `sku_id`, `quantity`, `line_cost_EGP`.
- `marketing_campaigns.csv`: `orders_attributed`; counting one attribution as one unique order is **not established**.
- `sales_returns.csv`: `return_id`, `refund_amount_EGP`.
- Schema strictness, duplicates, full join-cardinality/orphans and end-to-end transactionality are **not implemented**. Source sampling stores only the first 10 rows of each CSV and is not full lineage.
- Core base aggregates and stale source samples are cleared on successful rerun, but downstream marts and other derived tables require explicit rebuilding; reruns are not guaranteed atomic. Prefer a clean isolated staging database for each data reload. CSV parsing and DB ingest are not fully atomic across files.

## Operator reconciliation checklist
1. Obtain authorized client CSVs separately; keep out of source control and release ZIP.
2. Validate file names, headers, encoding, dates, branch IDs, units-of-measure and period coverage against a signed client dictionary.
3. Import into a backed-up **staging database**, compare source SHA-256 and row counts to approved inputs.
4. Run ingestion and sales mart build; record case ledger and trust statuses; investigate any changes across runs.
5. Reconcile POS, procurement, stock movement and reported margin independently. Approve source-to-metric definitions with named Cottonil owners before publishing any executive KPI.
6. Never quote synthetic fixture totals or historical screenshots as validated company facts.
