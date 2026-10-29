import csv, hashlib, json, os, sqlite3, threading
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2]
DB=Path(os.getenv('NEXUS_DB',str(ROOT/'data'/'nexus.sqlite')))
RAW=Path(os.getenv('NEXUS_RAW',str(ROOT/'data'/'raw')))
DB.parent.mkdir(parents=True,exist_ok=True)
lock=threading.RLock()
SCHEMA='''
CREATE TABLE IF NOT EXISTS datasets(name TEXT PRIMARY KEY, rows INTEGER, columns_json TEXT, nulls_json TEXT, duplicates INTEGER, sha256 TEXT, ingested_at TEXT);
CREATE TABLE IF NOT EXISTS metrics(key TEXT PRIMARY KEY, value REAL, unit TEXT, definition TEXT, source TEXT, trust TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY,title TEXT,severity TEXT,status TEXT,observations_json TEXT,hypotheses_json TEXT,evidence_json TEXT,created_at TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT,kind TEXT,detail TEXT,actor TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT,action TEXT,status TEXT,owner TEXT,reason TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS daily_sales(date TEXT PRIMARY KEY, revenue REAL, orders INTEGER, units REAL, gross_margin REAL);
CREATE TABLE IF NOT EXISTS sku_sales(sku_id TEXT PRIMARY KEY,units REAL,revenue REAL,margin REAL,lines INTEGER);
CREATE TABLE IF NOT EXISTS branch_sales(branch_id TEXT PRIMARY KEY,orders INTEGER,revenue REAL);
CREATE TABLE IF NOT EXISTS sku_purchases(sku_id TEXT PRIMARY KEY,units REAL,line_cost REAL);
CREATE TABLE IF NOT EXISTS source_samples(table_name TEXT,record_id TEXT,payload TEXT,PRIMARY KEY(table_name,record_id));
CREATE TABLE IF NOT EXISTS case_detection(case_id TEXT PRIMARY KEY, evaluated_at TEXT NOT NULL, supported INTEGER NOT NULL, required_sources TEXT NOT NULL, observed_json TEXT NOT NULL, source_hashes TEXT NOT NULL, threshold_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS auth_sessions(sid_hash TEXT PRIMARY KEY,username TEXT NOT NULL,role TEXT NOT NULL,expires_at INTEGER NOT NULL,revoked_at TEXT,csrf_hash TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, method TEXT NOT NULL, path TEXT NOT NULL, status INTEGER NOT NULL, branch_scope TEXT, details TEXT NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(occurred_at);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor, occurred_at);
CREATE TABLE IF NOT EXISTS auth_attempts(username TEXT,source_hash TEXT,attempted_at INTEGER NOT NULL,successful INTEGER NOT NULL); 
CREATE INDEX IF NOT EXISTS idx_auth_attempts ON auth_attempts(username,source_hash,attempted_at);
'''
def db():
 c=sqlite3.connect(DB,timeout=30,check_same_thread=False)
 c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');c.executescript(SCHEMA);return c
def now():return datetime.now(timezone.utc).isoformat()
def amount(v):
 try:return float(v or 0)
 except (ValueError,TypeError):return 0.0
def inventory():
 return sorted(p for p in RAW.rglob('*.csv') if p.is_file())
def ingest():
 files=inventory()
 if not files:raise FileNotFoundError(f'No CSV files under {RAW}')
 conn=db();daily=defaultdict(lambda:[0.,set(),0.,0.]); sku=defaultdict(lambda:[0.,0.,0.,0]); branch=defaultdict(lambda:[set(),0.]); purchases=defaultdict(lambda:[0.,0.]); overall=defaultdict(float)
 branch_open={}; sales_order_dates={}; sample_limit=10
 for p in files:
  name=p.name; sha=hashlib.sha256();rows=0;nulls=defaultdict(int);dupes=None;header=[]
  with p.open('rb') as binary:
   for block in iter(lambda:binary.read(1024*1024),b''):sha.update(block)
  conn.execute('DELETE FROM source_samples WHERE table_name=?',(name,))
  with p.open(encoding='utf-8-sig',newline='',errors='replace') as f:
   reader=csv.DictReader(f);header=reader.fieldnames or []
   for row in reader:
    rows+=1
    for k,v in row.items():
     if not (v or '').strip():nulls[k]+=1
    if name=='branches.csv':branch_open[row['branch_id']]=row['opening_date']
    elif name=='sales_orders.csv':
     overall['sales_orders']+=1;overall['sales_paid']+=amount(row['paid_total_EGP'])
     d=row['order_date'];sales_order_dates[row['sales_order_id']]=(d,row['branch_id'])
     daily[d][1].add(row['sales_order_id']);branch[row['branch_id']][0].add(row['sales_order_id'])
    elif name=='sales_order_items.csv':
     qty=amount(row['quantity']);net=amount(row['net_line_EGP']);margin=amount(row['margin_EGP']);sku_id=row['sku_id'];d=row['order_date']
     overall['sold_units']+=qty;overall['net_sales']+=net;overall['margin']+=margin
     daily[d][0]+=net;daily[d][2]+=qty;daily[d][3]+=margin
     s=sku[sku_id];s[0]+=qty;s[1]+=net;s[2]+=margin;s[3]+=1
     branch[row['branch_id']][1]+=net
    elif name=='purchase_order_items.csv':
     q=amount(row['quantity']);cost=amount(row['line_cost_EGP']);overall['purchased_units']+=q;overall['purchase_line_cost']+=cost
     s=purchases[row['sku_id']];s[0]+=q;s[1]+=cost
    elif name=='marketing_campaigns.csv':overall['marketing_attributed_orders']+=amount(row['orders_attributed'])
    elif name=='sales_returns.csv':overall['returns']+=1;overall['refunds']+=amount(row['refund_amount_EGP'])
    if rows<=sample_limit:
     pk=next((row.get(x) for x in ('sales_order_id','sales_line_id','po_line_id','return_id','sku_id','branch_id','campaign_id','product_id') if row.get(x)),str(rows))
     conn.execute('INSERT OR REPLACE INTO source_samples VALUES (?,?,?)',(name,pk,json.dumps(row,ensure_ascii=False)))
  conn.execute('INSERT OR REPLACE INTO datasets VALUES (?,?,?,?,?,?,?)',(name,rows,json.dumps(header),json.dumps(nulls),dupes,sha.hexdigest(),now()))
  conn.commit()
  print(f'Loaded {name}: {rows:,} rows',flush=True)
 # On successful source enumeration, remove obsolete aggregates and source receipts.
 # The full ingest is not transactionally atomic across files; use isolated staging DBs.
 available_files={p.name for p in files}
 if available_files:
  for previous in conn.execute('SELECT name FROM datasets').fetchall():
   if previous['name'] not in available_files:
    conn.execute('DELETE FROM datasets WHERE name=?',(previous['name'],))
    conn.execute('DELETE FROM source_samples WHERE table_name=?',(previous['name'],))
 for tablename in ('daily_sales','sku_sales','branch_sales','sku_purchases'):
  conn.execute('DELETE FROM '+tablename)
 for d,(revenue,orders,units,margin) in daily.items():conn.execute('INSERT OR REPLACE INTO daily_sales VALUES (?,?,?,?,?)',(d,revenue,len(orders),units,margin))
 for k,v in sku.items():conn.execute('INSERT OR REPLACE INTO sku_sales VALUES (?,?,?,?,?)',(k,*v))
 for k,v in branch.items():conn.execute('INSERT OR REPLACE INTO branch_sales VALUES (?,?,?)',(k,len(v[0]),v[1]))
 for k,v in purchases.items():conn.execute('INSERT OR REPLACE INTO sku_purchases VALUES (?,?,?)',(k,*v))
 # Branch date check parsed with actual source formats; no credit is given to unverified comparisons.
 from datetime import datetime
 opened={k:datetime.strptime(v,'%m/%d/%Y').date() for k,v in branch_open.items() if v}
 before=sum(1 for d,b in sales_order_dates.values() if b in opened and datetime.strptime(d,'%Y-%m-%d').date()<opened[b])
 overall['orders_before_branch_open']=before
 overall['sku_count_both']=len(set(sku)&set(purchases))
 overall['purchase_sales_ratio']=overall['purchased_units']/overall['sold_units'] if overall['sold_units'] else 0
 metric_specs={'net_sales':('EGP','Sum of sales line net_line_EGP','sales_order_items.csv','warning'),'sold_units':('units','Sum of sales line quantity','sales_order_items.csv','warning'),'sales_orders':('orders','Count of sales_orders records','sales_orders.csv','verified'),'margin':('EGP','Sum of sales line margin_EGP, subject to cost validity','sales_order_items.csv','warning'),'purchased_units':('source units','Sum of purchase item quantity, unit equivalence not validated','purchase_order_items.csv','unverified'),'purchase_line_cost':('EGP','Sum of purchase line_cost_EGP, not a realized loss','purchase_order_items.csv','unverified'),'purchase_sales_ratio':('ratio','Purchased source quantity divided by sold source quantity; units unreconciled','purchase_order_items.csv; sales_order_items.csv','blocked'),'marketing_attributed_orders':('attributions','Sum of campaign orders_attributed, attribution unit unverified','marketing_campaigns.csv','unverified'),'orders_before_branch_open':('orders','Sales orders dated prior to joined branch opening date','sales_orders.csv; branches.csv','warning'),'sku_count_both':('SKUs','SKU intersection between purchase lines and sales lines','purchase_order_items.csv; sales_order_items.csv','verified'),'returns':('records','Count of return records','sales_returns.csv','verified'),'refunds':('EGP','Sum of refund_amount_EGP','sales_returns.csv','warning')}
 requirements_by_metric={
  'net_sales':('sales_order_items.csv',), 'sold_units':('sales_order_items.csv',),
  'sales_orders':('sales_orders.csv',), 'margin':('sales_order_items.csv',),
  'purchased_units':('purchase_order_items.csv',), 'purchase_line_cost':('purchase_order_items.csv',),
  'purchase_sales_ratio':('purchase_order_items.csv','sales_order_items.csv'),
  'marketing_attributed_orders':('marketing_campaigns.csv',),
  'orders_before_branch_open':('sales_orders.csv','branches.csv'),
  'sku_count_both':('purchase_order_items.csv','sales_order_items.csv'),
  'returns':('sales_returns.csv',), 'refunds':('sales_returns.csv',)
 }
 available={p.name for p in files}
 for key,(unit,definition,source,trust) in metric_specs.items():
  if set(requirements_by_metric[key]).issubset(available):
   conn.execute('INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?,?)',(key,overall[key],unit,definition,source,trust,now()))
  else:
   conn.execute('DELETE FROM metrics WHERE key=?',(key,))
 
 # A case is created ONLY when the required source files and the measured predicate both hold.
 try: ratio_threshold=float(os.getenv('NEXUS_RECONCILIATION_RATIO_THRESHOLD','10'))
 except ValueError:raise ValueError('NEXUS_RECONCILIATION_RATIO_THRESHOLD must be numeric')
 if ratio_threshold<=1:raise ValueError('Reconciliation threshold must exceed 1')
 rules={
  'NEX-001': ({'purchase_order_items.csv','sales_order_items.csv'}, overall['sold_units']>0 and overall['purchase_sales_ratio']>=ratio_threshold),
  'NEX-002': ({'marketing_campaigns.csv','sales_orders.csv'}, overall['sales_orders']>0 and overall['marketing_attributed_orders']>overall['sales_orders']),
  'NEX-003': ({'sales_orders.csv','branches.csv'}, overall['orders_before_branch_open']>0),
 }
 cases=[('NEX-001','Procurement versus sales unit reconciliation','critical', ['Purchase-to-sales quantities have materially different magnitudes; physical unit equivalence is not validated.'],['UOM mismatch','Period or inventory movement mismatch','Source generator assumptions'],['purchased_units','sold_units','purchase_sales_ratio']),('NEX-002','Marketing attribution exceeds recorded orders','high',['Marketing-attributed order total requires reconciliation to actual sales orders.'],['Attribution duplicated across campaigns','Different event definitions or date coverage'],['marketing_attributed_orders','sales_orders']),('NEX-003','Orders predate branch opening dates','high',['Joined sales orders have earlier dates than associated branch opening dates.'],['Backfilled branch metadata','Incorrect source dates','Reassignment of historical sales'],['orders_before_branch_open'])]
 created=0
 for cid,title,severity,observations,hypotheses,evidence in cases:
  requirements,condition=rules[cid]
  supported=requirements.issubset(available) and bool(condition)
  source_hashes={r['name']:r['sha256'] for r in conn.execute('SELECT name,sha256 FROM datasets') if r['name'] in requirements}
  observed={'NEX-001':{'purchased_units':overall['purchased_units'],'sold_units':overall['sold_units'],'ratio':overall['purchase_sales_ratio']},
            'NEX-002':{'marketing_attributed_orders':overall['marketing_attributed_orders'],'sales_orders':overall['sales_orders']},
            'NEX-003':{'orders_before_branch_open':overall['orders_before_branch_open']}}[cid]
  threshold={'NEX-001':{'ratio_gte':ratio_threshold},'NEX-002':{'attribution_gt_orders':True},'NEX-003':{'orders_before_open_gt':0}}[cid]
  conn.execute('INSERT OR REPLACE INTO case_detection VALUES (?,?,?,?,?,?,?)',
    (cid,now(),int(supported),json.dumps(sorted(requirements)),json.dumps(observed),json.dumps(source_hashes),json.dumps(threshold)))
  if supported:
   cur=conn.execute('INSERT OR IGNORE INTO cases VALUES (?,?,?,?,?,?,?,?,?)',(cid,title,severity,'open',json.dumps(observations),json.dumps(hypotheses),json.dumps(evidence),now(),now()))
   created+=cur.rowcount
  else:
   # Remove ONLY pristine auto-seeded cases, never decisions or human work.
   conn.execute('DELETE FROM cases WHERE id=? AND title=? AND status=\'open\' AND NOT EXISTS(SELECT 1 FROM decisions WHERE case_id=?) AND NOT EXISTS(SELECT 1 FROM events WHERE case_id=?)',(cid,title,cid,cid))
 conn.commit();conn.close()
 return {'datasets':len(files),'metrics':dict(overall),'cases_created':created,'case_evidence':{cid:{'required_sources':sorted(req),'sources_present':sorted(req & available),'predicate_met':bool(condition),'supported':req.issubset(available) and bool(condition)} for cid,(req,condition) in rules.items()}}
