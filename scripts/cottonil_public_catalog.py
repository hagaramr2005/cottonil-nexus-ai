"""Bounded, robots-aware public product metadata collection. No login, bypass or images.
Products are external reference records, NEVER joined to local SKUs without mapping.
"""
import argparse,json,time,urllib.request,urllib.robotparser,urllib.parse,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--origin',default='https://cottonilegypt.com');p.add_argument('--max-pages',type=int,default=2);p.add_argument('--delay',type=float,default=2.0);a=p.parse_args()
 origin=a.origin.rstrip('/');parsed=urllib.parse.urlparse(origin)
 if parsed.scheme!='https' or parsed.hostname not in {'cottonilegypt.com','www.cottonilegypt.com'}:raise SystemExit('Only the inspected Cottonil Egypt public host is allowed')
 if not 1<=a.max_pages<=10 or a.delay<2:raise SystemExit('max-pages must be 1..10; delay must be >=2s')
 agent='CottonilNexusResearch/1.0 (public metadata research; contact site operator for bulk data)'
 robots=origin+'/robots.txt';rp=urllib.robotparser.RobotFileParser();rp.set_url(robots)
 try:rp.read()
 except Exception as e:raise SystemExit('Cannot validate robots.txt. Refusing to crawl: '+str(e))
 if not rp.can_fetch(agent,origin+'/products.json?limit=100&page=1'):raise SystemExit('robots.txt disallows or could not authorize catalog endpoint; no scraping performed')
 out=[];seen=set()
 for n in range(1,a.max_pages+1):
  url=origin+f'/products.json?limit=100&page={n}'
  if not rp.can_fetch(agent,url):raise SystemExit('Robots check failed for '+url)
  req=urllib.request.Request(url,headers={'User-Agent':agent,'Accept':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=20) as response:
    if response.status!=200 or 'json' not in response.headers.get('Content-Type',''):raise ValueError('Expected public JSON response')
    payload=json.loads(response.read(5_000_000).decode('utf-8'))
  except Exception as e:raise SystemExit(f'Stop; public collection inaccessible: {e}')
  items=payload.get('products',[])
  if not isinstance(items,list):raise SystemExit('Unexpected schema')
  for item in items:
   handle=str(item.get('handle') or '');pid=str(item.get('id') or '')
   if not handle or pid in seen:continue
   seen.add(pid)
   variants=item.get('variants') or []
   out.append({'external_id':pid,'handle':handle,'title':item.get('title'),'product_type':item.get('product_type'),'vendor':item.get('vendor'),'url':origin+'/products/'+urllib.parse.quote(handle),'image_url':(item.get('images') or [{}])[0].get('src') if item.get('images') else None,'variant_count':len(variants),'prices':[v.get('price') for v in variants if v.get('price') is not None],'source':url,'mapping_status':'unmapped_external_reference'})
  if len(items)<100:break
  time.sleep(a.delay)
 dest=ROOT/'data/external/cottonil';dest.mkdir(parents=True,exist_ok=True)
 (dest/'public_products.json').write_text(json.dumps({'origin':origin,'items':out,'warning':'Public research snapshot, not Cottonil internal SKU mapping; prices may change; check reuse/rights before publishing images.'},indent=2,ensure_ascii=False),encoding='utf-8')
 print(f'Saved {len(out)} public catalog records; original CSVs untouched')
if __name__=='__main__':main()
