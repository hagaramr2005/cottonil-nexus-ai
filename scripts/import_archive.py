import sys,zipfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];dest=root/'data'/'raw';dest.mkdir(exist_ok=True,parents=True)
z=zipfile.ZipFile(sys.argv[1]);count=0
for info in z.infolist():
 if not info.filename.lower().endswith('.csv'):continue
 file=Path(info.filename).name
 if (dest/file).exists():continue
 with z.open(info) as src,(dest/file).open('wb') as target:shutil.copyfileobj(src,target)
 count+=1
print(f'Extracted {count} files to {dest}')
