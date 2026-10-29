"""SYNTHETIC TEST DATA — NOT COTTONIL DATA.

Minimal, hand-countable CSV fixture written to a pytest tmp dir. It exists only so
code-level tests (API shape, filters, 404s, trust flags) can run without the
company's private datasets. No value here may be quoted as a business metric.

Known expected values (computed by hand, asserted in tests):
  12 orders, one per month 2025-01..2025-12, alternating branches SYN-B1 / SYN-B2
  each order has one line: qty 2, gross 120, discount 20, net 100, margin 30
  => net 1200.00, units 24, 2 orders predate SYN-B2 opening (2025-02, 2025-04)
"""
import csv
from pathlib import Path

LABEL = "SYNTHETIC TEST DATA"
EXPECTED = {"net": 1200.00, "units": 24.0, "orders": 12, "orders_before_open": 2}


def _w(path: Path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_fixture(raw: Path) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    _w(raw / "branches.csv", ["branch_id", "opening_date"],
       [["SYN-B1", "01/01/2025"], ["SYN-B2", "06/01/2025"]])
    orders, items = [], []
    for m in range(1, 13):
        oid, branch = f"SYN-O{m:02d}", ("SYN-B1" if m % 2 else "SYN-B2")
        date = f"2025-{m:02d}-15"
        sku = "SYN-SKU-1" if m <= 6 else "SYN-SKU-2"
        orders.append([oid, date, branch, "100", "Store" if m % 3 else "Online", f"SYN-C{m}"])
        items.append([oid, f"SYN-L{m:02d}", date, branch, "SYN-P1", sku, 2, 100, 120, 20, 30])
    _w(raw / "sales_orders.csv",
       ["sales_order_id", "order_date", "branch_id", "paid_total_EGP", "sales_channel", "customer_id"], orders)
    _w(raw / "sales_order_items.csv",
       ["sales_order_id", "sales_line_id", "order_date", "branch_id", "product_id", "sku_id",
        "quantity", "net_line_EGP", "gross_line_EGP", "discount_line_EGP", "margin_EGP"], items)
    _w(raw / "purchase_order_items.csv", ["po_line_id", "sku_id", "quantity", "line_cost_EGP"],
       [["SYN-PL1", "SYN-SKU-1", 500, 1000], ["SYN-PL2", "SYN-SKU-2", 700, 1400]])
    _w(raw / "marketing_campaigns.csv", ["campaign_id", "orders_attributed"], [["SYN-MC1", 30]])
    _w(raw / "sales_returns.csv", ["return_id", "refund_amount_EGP"], [["SYN-R1", 50]])
