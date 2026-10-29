
"""Build source-derived sales analytics marts; source CSVs are read-only."""
import csv, json, sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import os, sys
ROOT=Path(__file__).resolve().parents[1]
RAW=Path(os.environ.get("NEXUS_RAW", ROOT/"data/raw"))
DB=Path(os.environ.get("NEXUS_DB",ROOT/"data/nexus.sqlite"))
def parse(name):
    with (RAW/name).open(encoding="utf-8-sig",newline="") as f:
        yield from csv.DictReader(f)
def num(row,key):
    try: return float(row.get(key) or 0)
    except (ValueError,TypeError): return 0.
def build():
    if not (RAW/"sales_order_items.csv").exists(): raise FileNotFoundError("Missing sales_order_items.csv")
    DB.parent.mkdir(parents=True,exist_ok=True)
    orders={}
    for r in parse("sales_orders.csv"):
        orders[r["sales_order_id"]]=(r.get("sales_channel") or "Unknown",r.get("customer_id") or "")
    product_names={}
    product_category={}
    if (RAW/"products_catalog.csv").exists():
        for r in parse("products_catalog.csv"):
            product_names[r.get("product_id")]=r
    groups=defaultdict(lambda:[0.,0.,0.,0.,0,set()])
    sku=defaultdict(lambda:[0.,0.,0.,0.,set(),set()])
    for i,r in enumerate(parse("sales_order_items.csv"),1):
        month=r["order_date"][:7]
        channel,cust=orders.get(r["sales_order_id"],("Unknown",""))
        key=(month,r["branch_id"],r["product_id"],channel)
        a=groups[key]
        a[0]+=num(r,"net_line_EGP");a[1]+=num(r,"gross_line_EGP")
        a[2]+=num(r,"discount_line_EGP");a[3]+=num(r,"quantity")
        a[4]+=num(r,"margin_EGP");a[5].add(r["sales_order_id"])
        s=sku[r["sku_id"]];s[0]+=num(r,"net_line_EGP")
        s[1]+=num(r,"quantity");s[2]+=num(r,"margin_EGP");s[3]+=1
        s[4].add(r["branch_id"]);s[5].add(month)
    with sqlite3.connect(DB) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS sales_mart(
          month TEXT NOT NULL,branch_id TEXT NOT NULL,product_id TEXT NOT NULL,
          channel TEXT NOT NULL,net REAL,gross REAL,discount REAL,units REAL,
          line_margin REAL,orders INTEGER,
          PRIMARY KEY(month,branch_id,product_id,channel));
        CREATE TABLE IF NOT EXISTS sku_profile(
          sku_id TEXT PRIMARY KEY,net REAL,units REAL,line_margin REAL,lines INTEGER,
          branches INTEGER,active_months INTEGER);
        CREATE INDEX IF NOT EXISTS idx_sales_mart_month ON sales_mart(month);
        CREATE INDEX IF NOT EXISTS idx_sales_mart_branch ON sales_mart(branch_id);
        CREATE INDEX IF NOT EXISTS idx_sales_mart_product ON sales_mart(product_id);
        """)
        c.execute("DELETE FROM sales_mart");c.execute("DELETE FROM sku_profile")
        c.executemany("INSERT INTO sales_mart VALUES (?,?,?,?,?,?,?,?,?,?)",
          ((*key,*val[:5],len(val[5])) for key,val in groups.items()))
        c.executemany("INSERT INTO sku_profile VALUES (?,?,?,?,?,?,?)",
          ((key,*val[:4],len(val[4]),len(val[5])) for key,val in sku.items()))
        c.commit()
    return {"processed_lines":i,"mart_rows":len(groups),"sku_profiles":len(sku),"months":len({x[0] for x in groups}),"database":str(DB)}
if __name__=="__main__":print(json.dumps(build(),indent=2))
