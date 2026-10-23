"""Publish full registered frames; separately compose explicitly labeled review evidence."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
S=Path(__file__).resolve().parent;B=S.parent;C=B/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def relative(p):return str(p.relative_to(B))
v=json.loads((C/'native-validation.json').read_text());assert v['complete'] and len(v['captureRecords'])==144
raw=[];native=[];atlases=[];images={};alpha=[]
for clip in ['windup','active','recovery']:
 for direction in ['N','E','S','W']:
  atlas=Image.new('RGBA',(3840,1792));rects=[]
  for index in range(12):
   src=C/'native'/clip/direction/f'{index:03d}.png';dst=C/'published'/clip/direction/f'{index:03d}.png';dst.parent.mkdir(parents=True,exist_ok=True)
   im=Image.open(src).convert('RGBA');assert im.size==(1280,1792)
   published=im.resize((640,896),Image.Resampling.LANCZOS);published.save(dst)
   bbox=published.getbbox();assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<640 and bbox[3]<896
   alpha.append({'clip':clip,'direction':direction,'index':index,'bbox':bbox,'borderClear':True})
   images[(clip,direction,index)]=published
   rect=[index%6*640,index//6*896,640,896];rects.append(rect);atlas.paste(published,rect[:2])
   raw.append({'clip':clip,'direction':direction,'index':index,'frame':index,'path':relative(dst),'dimensions':[640,896],'sha256':sha(dst)})
   native.append({'clip':clip,'direction':direction,'index':index,'frame':index,'nativeFrame':index+1,'path':relative(src),'dimensions':[1280,1792],'sha256':sha(src)})
  dest=C/'atlases'/f'{clip}-{direction}.png';dest.parent.mkdir(exist_ok=True);atlas.save(dest)
  for index,rect in enumerate(rects):assert atlas.crop((rect[0],rect[1],rect[0]+640,rect[1]+896)).tobytes()==images[(clip,direction,index)].tobytes()
  atlases.append({'clip':clip,'direction':direction,'path':relative(dest),'size':[3840,1792],'atlasSize':[3840,1792],'columns':6,'rows':2,'frameSize':[640,896],'rects':rects,'frameOrder':list(range(12)),'frames':12,'fps':12,'loop':False,'static':False,'sha256':sha(dest)})
dump(C/'published-frame-validation.json',{'rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'alpha':alpha,'allAtlasCellsEqualPublishedRGBA':True,'wholecanvasRule':'Pillow LANCZOS1280x1792 to640x896; no other sprite pixel processing','historicalRawParity':'Unavailable: historical original4x captures absent; only frozen original replay reproduces original atlas pixels after reduction.'})
P=C/'previews';P.mkdir()
def composite(im,bg=(112,118,128),size=None):
 if size:im=im.resize(size,Image.Resampling.BILINEAR)
 out=Image.new('RGBA',im.size,(*bg,255));out.alpha_composite(im);return out.convert('RGB')
def label(sheet,xy,t):ImageDraw.Draw(sheet).text(xy,t,fill='white')
mapping={};hero={d:relative(C/'published/active'/d/'011.png') for d in ['N','E','S','W']}
sheet=Image.new('RGB',(1280,468),(112,118,128))
for j,d in enumerate(['N','E','S','W']):sheet.paste(composite(images[('active',d,11)],size=(320,448)),(j*320,20));label(sheet,(j*320+3,3),'active '+d+' index11 logical')
dest=P/'four-view-sheet.png';sheet.save(dest);mapping['four-view-sheet']={'path':relative(dest),'cells':[{'direction':d,'clip':'active','index':11,'rect':[j*320,20,320,448],'source':hero[d]} for j,d in enumerate(['N','E','S','W'])]}
phone=Image.new('RGB',(640,732),(112,118,128));members=[]
for ci,clip in enumerate(['windup','active','recovery']):
 for di,d in enumerate(['N','E','S','W']):
  phone.paste(composite(images[(clip,d,5)],size=(160,224)),(di*160,ci*244+20));label(phone,(di*160+3,ci*244+3),clip+' '+d+' index5')
  members.append({'clip':clip,'direction':d,'index':5,'rect':[di*160,ci*244+20,160,224],'source':relative(C/'published'/clip/d/'005.png')})
dest=P/'phone.png';phone.save(dest);mapping['phone']={'path':relative(dest),'cells':members,'layer':'Independent wholecanvas BILINEAR preview; actual browser CSS phone evidence supplied separately.'}
# One shared full-phase sheet per clip, explicit four alias rows; crops are review-only.
for clip in ['windup','active','recovery']:
 full=[images[(clip,d,i)].resize((320,448),Image.Resampling.BILINEAR) for d in ['N','E','S','W'] for i in range(12)]
 box=(min(im.getbbox()[0] for im in full),min(im.getbbox()[1] for im in full),max(im.getbbox()[2] for im in full),max(im.getbbox()[3] for im in full))
 width=box[2]-box[0]+8;height=box[3]-box[1]+24
 sheet=Image.new('RGB',(width*12,height*4),(112,118,128));cells=[]
 for di,d in enumerate(['N','E','S','W']):
  for index in range(12):
   crop=full[di*12+index].crop(box);sheet.paste(composite(crop),(index*width+4,di*height+20));label(sheet,(index*width+3,di*height+3),f'{clip} {d} {index:02}')
   cells.append({'clip':clip,'direction':d,'index':index,'rect':[index*width+4,di*height+20,crop.width,crop.height],'source':relative(C/'published'/clip/d/f'{index:03d}.png'),'logicalCanvasReviewCrop':list(box)})
 dest=P/f'allphase-{clip}.png';sheet.save(dest)
 for d in ['N','E','S','W']:mapping[clip+'-'+d]={'path':relative(dest),'aliasFacing':d,'cells':[cell for cell in cells if cell['direction']==d],'allSheetCells':cells,'layer':'All12 phases at logical scale; shared usefulpixel crop for review only. Published/native frames remain full registered canvases.'}
# Native-resolution enlarged facets at middle and maximum spread plus terminals.
for clip in ['windup','active','recovery']:
 rows=[];cells=[];maxw=0
 for d in ['N','E','S','W']:
  row=[]
  for index in [0,5,11]:
   im=Image.open(C/'native'/clip/d/f'{index:03d}.png').convert('RGBA');box=im.getbbox();crop=im.crop(box)
   row.append((index,composite(crop),box))
  maxw=max(maxw,sum(im.width+12 for _,im,_ in row));rows.append((d,row))
 heights=[max(im.height for _,im,_ in row)+28 for _,row in rows];sheet=Image.new('RGB',(maxw,sum(heights)),(112,118,128));y=0
 for (d,row),height in zip(rows,heights):
  x=0
  for index,im,box in row:
   sheet.paste(im,(x,y+24));label(sheet,(x+3,y+3),f'native4x {clip} {d} index{index}');cells.append({'clip':clip,'direction':d,'index':index,'rect':[x,y+24,im.width,im.height],'nativeReviewCrop':list(box),'source':relative(C/'native'/clip/d/f'{index:03d}.png')});x+=im.width+12
  y+=height
 dest=P/f'native-facets-extrema-terminals-{clip}.png';sheet.save(dest);dump(P/f'native-facets-extrema-terminals-{clip}.json',{'path':relative(dest),'cells':cells,'scope':'Review crops at actual native4x size only; native images untouched.'})
mapping['motion']={'path':relative(C/'consumer/full-chromium/actual-playback-allphase-windup.png'),'purpose':'Actual timed browser video decoded all12phases plus heldterminal for allfacings; sibling active/recovery sheets and bothmode videos required resources.'}
dump(P/'preview-map.json',mapping);dump(C/'delivery-draft.json',{'project':'source/round-01.blend','recipeScript':'source/build-round-01.py','recipe':'source/round-01-recipe.json','heroes':hero,'previews':{k:v['path'] for k,v in mapping.items()},'rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'nativeRecords':{'camera':'source/round-01-records/camera.json','assetRecord':'source/round-01-records/asset.json','rig':'source/round-01-records/rig.json','nativeCamera':'source/round-01-records/camera-native.json'},'nativeValidation':'candidates/round-01/native-validation.json','validation':'candidates/round-01/validation.json'})
print('ROUND01_PUBLISHED144_ATLASES12')
