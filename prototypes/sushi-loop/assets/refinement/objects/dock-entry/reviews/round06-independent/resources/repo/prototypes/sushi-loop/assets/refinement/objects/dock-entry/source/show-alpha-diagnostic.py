from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';C=B/'source/resources/paired-consumer/floor-packet/candidates/round-03';v=json.loads((O/'consumer-contact-metrics.json').read_text());out=O/'previews/alpha-contact-diagnostic.png';sheet=Image.new('RGB',(1200,4*340),'white');draw=ImageDraw.Draw(sheet);new=[]
for row,r in enumerate(v['records']):
 d=r['direction'];x,y=r['seamCenterNative'];box=(int(x-48),int(y-48),int(x+48),int(y+48));n=Image.open(B/r['nativePath']).convert('RGBA').crop(box);p=Image.open(B/r['independentPath']).convert('RGBA').crop(box)
 for col,(bg,name) in enumerate([('#f2f0e6','light'),('#a7a7a7','gray'),('#20242a','dark')]):
  for j,(im,label) in enumerate([(n,'native'),(p,'independent')]):
   panel=Image.new('RGBA',(96,96),bg);panel.alpha_composite(im);panel=panel.resize((192,192),Image.Resampling.NEAREST);sheet.paste(panel.convert('RGB'),(col*400+j*195,row*340+30));draw.text((col*400+j*195,row*340+10),f'{d} {label} {name}',fill='black')
 # Exact central row/column alpha profile around the edge.
 nn=np.array(Image.open(B/r['nativePath']).convert('RGBA'));pp=np.array(Image.open(B/r['independentPath']).convert('RGBA'));cx,cy=round(x),round(y)
 if d in 'EW':native=nn[cy,cx-4:cx+5,3].tolist();ind=pp[cy,cx-4:cx+5,3].tolist()
 else:native=nn[cy-4:cy+5,cx,3].tolist();ind=pp[cy-4:cy+5,cx,3].tolist()
 draw.text((8,row*340+236),'Center alpha native:'+str(native)+' independent:'+str(ind),fill='black')
 new.append({'direction':d,'sampleNativePixel':[cx,cy],'nativeNormalAlphaProfile':native,'independentNormalAlphaProfile':ind})
sheet.save(out);(O/'consumer-alpha-profiles.json').write_text(json.dumps({'profiles':new,'preview':str(out.relative_to(B)),'interpretation':'Enlargement exposes raw subpixel source-over trough; actual logical and phone sampling remain separate final browser evidence. No pixels repaired.'},indent=2));print(new)
