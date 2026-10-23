"""Review-only native facet crops for the original judge's cited locations."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,math,hashlib
S=Path(__file__).resolve().parent;B=S.parent;C=B/'candidates/round-02'
ledger=json.loads((C/'native-validation.json').read_text());assert ledger['complete']
locations=json.loads((S/'round-02-inputs/frozen/reviews/native-facet-focus-map.json').read_text())
cells=[];sheet=Image.new('RGB',(1000,900),(112,118,128));draw=ImageDraw.Draw(sheet)
for index,location in enumerate(locations):
 rec=next(r for r in ledger['captureRecords'] if r['clip']==location['clip'] and r['direction']==location['direction'] and r['index']==location['index'])
 obj=next(o for o in rec['objects'] if o['name']==location['object']);bb=obj['projectedNativeBounds']
 box=[max(0,math.floor(bb['min'][0])-4),max(0,math.floor(bb['min'][1])-4),min(1280,math.ceil(bb['max'][0])+4),min(1792,math.ceil(bb['max'][1])+4)]
 path=B/rec['path'];image=Image.open(path).convert('RGBA').crop(box);background=Image.new('RGBA',image.size,(112,118,128,255));background.alpha_composite(image)
 x=(index%4)*250;y=(index//4)*300;sheet.paste(background.convert('RGB'),(x,y+36));draw.text((x+3,y+3),f"{location['clip']} {location['direction']} {location['index']} {location['object'].split('__')[-1]}",fill='white')
 cells.append({'clip':location['clip'],'direction':location['direction'],'index':location['index'],'object':location['object'],'source':rec['path'],'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'nativeReviewCrop':box,'sheetRect':[x,y+36,image.width,image.height]})
dest=C/'previews/native-facet-focus.png';sheet.save(dest)
(C/'previews/native-facet-focus-map.json').write_text(json.dumps({'path':str(dest.relative_to(B)),'scope':'Original judge cited locations, actual native4x usefulpixel crops only; all exports remain registered full canvases. No score orapproval.','cells':cells},indent=2)+'\n')
print('ROUND02_FOCUS_LOCATIONS',len(cells))
