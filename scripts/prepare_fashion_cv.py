"""Make leakage-safe reproducible Fashion Product Images Small splits. Requires only stdlib."""
import argparse,csv,random,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(source,seed=42,min_class=100):
 source=Path(source);matches=list(source.rglob('styles.csv'))
 if len(matches)!=1:raise SystemExit(f'Expected exactly one styles.csv; found {len(matches)}')
 styles=matches[0];images={p.stem:p for p in source.rglob('*.jpg')};images.update({p.stem:p for p in source.rglob('*.png')})
 records=[]
 with styles.open(encoding='utf-8-sig',newline='',errors='replace') as f:
  for row in csv.DictReader(f):
   pid=str(row.get('id','')).strip();kind=(row.get('subCategory') or '').strip();color=(row.get('baseColour') or '').strip()
   if pid in images and kind and color:records.append({'id':pid,'image':str(images[pid].resolve()),'type':kind,'color':color,'title':row.get('productDisplayName','')})
 if not records:raise SystemExit('No matching labeled images: verify Kaggle download')
 counts=collections.Counter(r['type'] for r in records);classes=[c for c,n in counts.most_common() if n>=min_class][:5]
 if len(classes)<2:raise SystemExit(f'Insufficient classes: {counts.most_common(10)}')
 filtered=[r for r in records if r['type'] in classes];groups=collections.defaultdict(list)
 for r in filtered:groups[r['type']].append(r)
 rng=random.Random(seed);out=[]
 for group in groups.values():
  rng.shuffle(group)
  for i,r in enumerate(group):out.append({**r,'split':'test' if i<len(group)*.15 else 'val' if i<len(group)*.30 else 'train'})
 dest=ROOT/'data/cv/fashion_prepared';dest.mkdir(parents=True,exist_ok=True)
 with (dest/'manifest.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['id','image','type','color','title','split']);w.writeheader();w.writerows(out)
 summary={'dataset':'paramaggarwal/fashion-product-images-small','seed':seed,'classes':classes,'total':len(out),'split_counts':dict(collections.Counter(r['split'] for r in out)),'label_counts':dict(collections.Counter(r['type'] for r in out)),'disclaimer':'Kaggle IDs have no verified relation to Cottonil SKUs'}
 (dest/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',default=str(ROOT/'data/cv/fashion'));p.add_argument('--seed',type=int,default=42);a=p.parse_args();run(a.source,a.seed)
