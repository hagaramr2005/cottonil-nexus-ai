# Sales chart provenance

| Chart | Endpoint | Fields | Interpretation |
|---|---|---|---|
| Revenue and discounts monthly | `GET /api/sales/intelligence` | `monthly[].label`, `.revenue`, `.discount` | Monthly sales-mart net and discounts in EGP |
| Branch performance | same | `branches[].label`, `.revenue` | Ranked aggregated net by branch |
| Product performance | same | `products[].label`, `.revenue` | Ranked aggregated net by product |

The backend derives these fields from `sales_mart`, itself built from sales-order source files. Charts honor the existing server-side start/end/branch/channel filters because they consume the existing filtered response. No static values or generated financial predictions are introduced. All three are pending live dataset checks because the uploaded ZIP lacks CSV data. Interpretation retains the API's existing caveat: source cost assumptions and sales mart granularity limit financial reconciliation.
