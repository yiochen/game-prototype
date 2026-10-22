from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];O=P.parent.parent;C=O/'candidates/round-01';out=P/'evidence/inspection';out.mkdir(exist_ok=True);records=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
res=json.loads((C/'consumer/results.json').read_text())
for r in res['cases']:
 src=C/'consumer'/r['cssScreenshot'];im=Image.open(src);h=im.height;split=h//2
 for idx,(top,bottom)in enumerate([(0,split),(split,h)]):
  dest=out/(src.stem+'-tile'+str(idx+1)+'.png');tile=im.crop((0,top,im.width,bottom));tile.save(dest);assert tile.tobytes()==im.crop((0,top,im.width,bottom)).tobytes();records.append({'path':dest.relative_to(O).as_posix(),'source':src.relative_to(O).as_posix(),'sourceSHA256':sha(src),'exactPixelRectangle':[0,top,im.width,bottom],'tileSHA256':sha(dest),'lossless':True,'use':'Native-pixel inspection tile only; primary candidate pixels untouched. Two rectangles cover full exact CSS PNG without reduction or discard.'})
for d in 'NESW':
 ims=[Image.open(C/k/(d+'.png')).convert('RGBA')for k in ['middle-L','mixed-edge-L']];sheet=Image.new('RGB',(1280,984),(128,128,128));dr=ImageDraw.Draw(sheet)
 for i,im in enumerate(ims):
  base=Image.new('RGB',im.size,(128,128,128));base.paste(im,mask=im.getchannel('A'));sheet.paste(base,(i*640,24));dr.text((i*640+4,4),('middle-L 'if i==0 else'mixed-edge-L ')+d,fill='white')
 dest=out/('actual-native-L-pair-'+d+'.png');sheet.save(dest);records.append({'path':dest.relative_to(O).as_posix(),'sourceRecords':[{'path':(C/k/(d+'.png')).relative_to(O).as_posix(),'sha256':sha(C/k/(d+'.png')),'exactNativePlacement':[i*640,24],'size':[640,960],'alphaCompositeBackground':[128,128,128]}for i,k in enumerate(['middle-L','mixed-edge-L'])],'use':'Full native raster size, two complete alpha composites; no fit/crop/reduction.'})
(P/'inspection-mapping.json').write_text(json.dumps({'candidatePacketSHA256':sha(P/'resources/packet.json'),'pathBase':'object-root','files':records},indent=2)+'\n')
print('inspection files',len(records))
