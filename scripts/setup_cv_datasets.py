"""Conservative official-source setup. Never marks unsupported downloads as successful."""
import argparse,subprocess,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data'/'cv'
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['fashion','dme','all'],default='all');a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 manifest={}
 if a.dataset in ('fashion','all'):
  target=OUT/'fashion';target.mkdir(exist_ok=True)
  try:
   subprocess.run([sys.executable,'-m','kaggle','datasets','download','-d','paramaggarwal/fashion-product-images-small','-p',str(target),'--unzip'],check=True)
   files=list(target.rglob('*.jpg'))+list(target.rglob('*.png'))
   meta=list(target.rglob('styles.csv'))
   if not files or not meta:raise RuntimeError('Downloaded content lacks verified images or styles.csv')
   manifest['fashion']={'status':'downloaded','images':len(files),'metadata':str(meta[0].relative_to(OUT))}
  except Exception as e:manifest['fashion']={'status':'blocked','error':str(e),'setup':'Install kaggle; configure secure ~/.kaggle/kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY; rerun.'}
 if a.dataset in ('dme','all'):
  manifest['dme']={'status':'manual_verification_required','official_source':'https://data.mendeley.com/datasets/4fcvnr77sb/1','reason':'Mendeley file-download API and license not verified in this environment. No guessed endpoint.'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
