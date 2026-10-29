"""Train real MobileNetV3 Small transfer learner; never invent accuracy or weights.
Optional: pip install torch torchvision (select correct CUDA wheel from PyTorch docs).
"""
import argparse,csv,json,random,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--epochs',type=int,default=3);p.add_argument('--batch-size',type=int,default=32);p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto');p.add_argument('--pretrained',action='store_true',help='Use official ImageNet pretrained weights; needs internet/cache');a=p.parse_args()
 try:
  import torch
  from torch import nn
  from torchvision import models,transforms
  from PIL import Image
 except ImportError as e:raise SystemExit('Install torch torchvision pillow in this venv. '+str(e))
 manifest=ROOT/'data/cv/fashion_prepared/manifest.csv'
 if not manifest.exists():raise SystemExit('Run prepare_fashion_cv.py first')
 with manifest.open(encoding='utf-8',newline='') as f:records=list(csv.DictReader(f))
 classes=sorted({r['type'] for r in records});label={c:i for i,c in enumerate(classes)}
 torch.manual_seed(42);random.seed(42)
 if torch.cuda.is_available() and a.device!='cpu':device='cuda'
 else:device='cpu'
 if a.device=='cuda' and device!='cuda':raise SystemExit('CUDA requested but unavailable')
 tfm=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
 class Dataset(torch.utils.data.Dataset):
  def __init__(self,split):self.rows=[r for r in records if r['split']==split]
  def __len__(self):return len(self.rows)
  def __getitem__(self,i):
   r=self.rows[i]
   with Image.open(r['image']) as im:image=tfm(im.convert('RGB'))
   return image,label[r['type']]
 training=Dataset('train');val=Dataset('val');test=Dataset('test')
 if not min(len(training),len(val),len(test)):raise SystemExit('Empty train/val/test split')
 weights=models.MobileNet_V3_Small_Weights.DEFAULT if a.pretrained else None
 net=models.mobilenet_v3_small(weights=weights)
 for param in net.features.parameters():param.requires_grad=False
 net.classifier[-1]=nn.Linear(net.classifier[-1].in_features,len(classes));net.to(device)
 opt=torch.optim.AdamW(net.classifier.parameters(),lr=0.0005);criterion=nn.CrossEntropyLoss()
 def loader(ds,shuffle=False):return torch.utils.data.DataLoader(ds,batch_size=a.batch_size,shuffle=shuffle,num_workers=0)
 best=-1;out=ROOT/'models/fashion';out.mkdir(parents=True,exist_ok=True);history=[]
 def score(ds):
  net.eval();correct=0;total=0;tp=collections.Counter();fp=collections.Counter();fn=collections.Counter()
  with torch.no_grad():
   for x,y in loader(ds):
    pred=net(x.to(device)).argmax(1).cpu()
    correct+=(pred==y).sum().item();total+=len(y)
    for a,b in zip(y.tolist(),pred.tolist()):
     if a==b:tp[a]+=1
     else:fp[b]+=1;fn[a]+=1
  f1=[2*tp[i]/max(1,2*tp[i]+fp[i]+fn[i]) for i in range(len(classes))]
  return {'accuracy':correct/max(1,total),'macro_f1':sum(f1)/len(f1),'samples':total,'per_class_f1':dict(zip(classes,f1))}
 for epoch in range(a.epochs):
  net.train();loss_total=0
  for x,y in loader(training,True):
   opt.zero_grad();loss=criterion(net(x.to(device)),y.to(device));loss.backward();opt.step();loss_total+=float(loss.item())
  metrics=score(val);metrics.update(epoch=epoch+1,loss_sum=loss_total);history.append(metrics);print(json.dumps(metrics))
  if metrics['macro_f1']>best:
   best=metrics['macro_f1'];torch.save({'state_dict':net.cpu().state_dict(),'classes':classes,'architecture':'mobilenet_v3_small','pretrained':a.pretrained},out/'best.pt');net.to(device)
 checkpoint=torch.load(out/'best.pt',map_location=device,weights_only=True);net.load_state_dict(checkpoint['state_dict']);net.to(device)
 report={'train':len(training),'val':len(val),'test':len(test),'best_validation_macro_f1':best,'test':score(test),'epochs':a.epochs,'device':device,'pretrained':a.pretrained,'history':history,'warning':'Accuracy reflects Kaggle holdout only, NOT Cottonil product catalog validation'}
 (out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
