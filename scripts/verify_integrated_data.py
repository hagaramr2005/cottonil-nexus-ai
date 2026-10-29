"""Read-only integrity check for the bundled source-derived analytics."""
from pathlib import Path
import sqlite3,json,sys
root=Path(__file__).resolve().parents[1]
db=root/'data'/'nexus.sqlite'
if not db.exists():raise SystemExit('Missing data/nexus.sqlite')
with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as c:
    integrity=c.execute('PRAGMA integrity_check').fetchone()[0]
    get=lambda q:c.execute(q).fetchone()[0]
    totals={'source_csv_files':get('SELECT COUNT(*) FROM datasets'),'sales_orders':get("SELECT value FROM metrics WHERE key='sales_orders'"),'sales_line_revenue_egp':get("SELECT value FROM metrics WHERE key='net_sales'"),'sales_mart_revenue_egp':get('SELECT SUM(net) FROM sales_mart'),'sales_mart_cells':get('SELECT COUNT(*) FROM sales_mart'),'sku_profiles':get('SELECT COUNT(*) FROM sku_profile'),'covered_months':get('SELECT COUNT(DISTINCT month) FROM sales_mart')}
    matched=abs(totals['sales_line_revenue_egp']-totals['sales_mart_revenue_egp'])<.02
    result={'database_integrity':integrity,'sales_reconciled':matched,'data':totals,'raw_csv_files_present':sum(1 for _ in (root/'data'/'raw').glob('*.csv'))}
    print(json.dumps(result,indent=2))
    if integrity!='ok' or not matched:sys.exit(1)
