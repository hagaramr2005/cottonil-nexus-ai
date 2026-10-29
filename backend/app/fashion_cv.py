"""Optional real trained-fashion inference. Model must exist from local training."""
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'models/fashion/best.pt'
EVAL=ROOT/'models/fashion/evaluation.json'
def status():
 return {'available':MODEL.exists() and EVAL.exists(),'checkpoint_exists':MODEL.exists(),'evaluation_exists':EVAL.exists(),'model':'MobileNetV3-Small type classifier (Kaggle labels)','warning':'No verified mapping from Kaggle product IDs to Cottonil SKUs; not defect detector'}
@lru_cache(maxsize=1)
def load():
 import torch
 from torchvision import models,transforms
 checkpoint=torch.load(MODEL,map_location='cpu',weights_only=True)
 classes=checkpoint['classes'];net=models.mobilenet_v3_small(weights=None);net.classifier[-1]=torch.nn.Linear(net.classifier[-1].in_features,len(classes));net.load_state_dict(checkpoint['state_dict']);net.eval()
 return net,classes,transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
def predict(content):
 import io,json,torch
 from PIL import Image,ImageOps
 model,classes,tfm=load()
 with Image.open(io.BytesIO(content)) as im:
  x=tfm(ImageOps.exif_transpose(im).convert('RGB')).unsqueeze(0)
 with torch.no_grad():p=torch.softmax(model(x),dim=1).flatten()
 top=torch.topk(p,min(3,len(classes)))
 return {'model':'mobilenet_v3_small','predictions':[{'type':classes[int(i)],'score':round(float(s),4)} for s,i in zip(top.values,top.indices)],'evaluation':json.loads(EVAL.read_text(encoding='utf-8'))['test'],'limitations':['Evaluated on held-out Kaggle fashion images only','Raw probabilities are not calibrated confidence','Cottonil SKUs remain unmapped','Human review required']}
