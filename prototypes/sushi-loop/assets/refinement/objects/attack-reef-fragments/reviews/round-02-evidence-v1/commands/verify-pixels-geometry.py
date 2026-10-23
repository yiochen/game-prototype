import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import numpy as np
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-02';prep=O/'reviews/preparation-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def diff(a,b):
 d=np.abs(np.asarray(a).astype(np.int16)-np.asarray(b).astype(np.int16));return {'equalRGBA':not bool(d.any()),'maxAbs':int(d.max()),'meanAbs':float(d.mean())}
# Verify all frozen baseline and candidate input identities before interpreting art.
base=json.loads((prep/'hash-manifest.json').read_text());assert all(sha(O/f['path'])==f['sha256'] for f in base['files'])
packet=json.loads((C/'packet.json').read_text());verified=[]
for group in ['files','candidateRenders','previews']:
 for name,r in packet[group].items():
  q=(C/r['path']).resolve();assert sha(q)==r['sha256'],(group,name);verified.append({'group':group,'name':name,'path':str(q),'sha256':r['sha256']})
manifest=json.loads((C/'resource-manifest.json').read_text());assert all(sha(O/f['path'])==f['sha256'] for f in manifest['resources'])
assert sha(C/'packet.json')=='2ef3cf680436f44b117165afeb02dfed4e6a0989b0a42e71dc9e0917789fdf22'
records=json.loads((P/'native/replay-validation.json').read_text())['captureRecords'];provided=json.loads((C/'native-validation.json').read_text())['captureRecords'];bykey={(r['clip'],r['direction'],r['index']):r for r in provided}
orig=json.loads((O/'inputs/catalog-object.json').read_text());clips={c['id']:c for c in orig['clips']};atlas_cache={};pixel=[];geom=[]
for r in records:
 key=(r['clip'],r['direction'],r['index']);rr=bykey[key];actual=Image.open(P/r['path']).convert('RGBA');offered=Image.open(O/rr['path']).convert('RGBA');pub=Image.open(C/'published'/key[0]/key[1]/f'{key[2]:03d}.png').convert('RGBA');reduced=actual.resize((640,896),Image.Resampling.LANCZOS)
 akey=key[:2]
 if akey not in atlas_cache:atlas_cache[akey]=Image.open(C/'atlases'/f'{key[0]}-{key[1]}.png').convert('RGBA')
 rect=clips[key[0]]['directions'][key[1]]['rects'][key[2]];x,y,w,h=rect;cell=atlas_cache[akey].crop((x,y,x+w,y+h));alpha=np.asarray(actual)[:,:,3]
 pixel.append({'clip':key[0],'direction':key[1],'index':key[2],'independentReplayVsSubmittedNative':diff(actual,offered),'independentWholeFrameLanczosVsPublished':diff(reduced,pub),'atlasVsPublished':diff(cell,pub),'transparentNativeOuterBorder':bool(not alpha[0].any()and not alpha[-1].any()and not alpha[:,0].any()and not alpha[:,-1].any()),'publishedAlphaBounds':pub.getchannel('A').getbbox()})
 errors={}
 for f in ['rawAuthoredBounds','evaluatedBounds','canonicalSBounds']:
  errors[f]=max(abs(r[f][a][i]-rr[f][a][i]) for a in ['min','max'] for i in range(3))
 geom.append({'clip':key[0],'direction':key[1],'index':key[2],'offeredMeasurementMaxAbsDeltas':errors,'pass':r['clearancePass']and r['containmentPass']and r['rootStationary']and r['positiveScales']})
assert len(pixel)==144 and all(x['pass'] for x in geom)
# Explicit preview alias/path/cell/content mapping, without inventing pixel coverage.
mp=json.loads((C/'previews/preview-map.json').read_text());aliases=[]
for name,r in packet['previews'].items():
 m=mp[name];assert (O/m['path']).resolve()==(C/r['path']).resolve();entry={'alias':name,'packetPath':r['path'],'sha256':r['sha256'],'cells':[]}
 if name!='motion':
  sheet=Image.open(C/r['path']).convert('RGB')
  for cell in m['cells']:
   source=Image.open(O/cell['source']).convert('RGBA');size=(160,224)if name=='phone'else(320,448);logical=source.resize(size,Image.Resampling.BILINEAR);crop=cell.get('logicalCanvasReviewCrop');bbox=logical.getchannel('A').getbbox();covered=True if not crop else crop[0]<=bbox[0]and crop[1]<=bbox[1]and crop[2]>=bbox[2]and crop[3]>=bbox[3]
   if crop:logical=logical.crop(crop)
   expected=Image.new('RGBA',logical.size,(112,118,128,255));expected.alpha_composite(logical);x,y,w,h=cell['rect'];off=sheet.crop((x,y,x+w,y+h));equal=not ImageChops.difference(expected.convert('RGB'),off).getbbox();assert equal and covered,(name,cell)
   entry['cells'].append({'clip':cell['clip'],'direction':cell['direction'],'index':cell['index'],'source':cell['source'],'sheetRect':cell['rect'],'cropContainsAllAlpha':covered,'cellPixelsVerified':equal})
 aliases.append(entry)
# Native enlargement of relevant upper caps, lower planes and turning silhouette.
focus=[]
for clip,d,i,names in [('active','E',11,[0,1,2,5]),('active','S',11,[0,3,8]),('windup','W',5,[1,2,7])]:
 rr=bykey[(clip,d,i)];source=Image.open(O/rr['path']).convert('RGBA')
 for index in names:
  name=f'attack-reef-fragments__fragment_{index}.001';ob=next(x for x in rr['objects']if x['name']==name);b=ob['projectedNativeBounds'];box=(max(0,int(b['min'][0])-5),max(0,int(b['min'][1])-5),min(1280,int(b['max'][0])+6),min(1792,int(b['max'][1])+6));im=source.crop(box);focus.append({'clip':clip,'direction':d,'index':i,'object':name,'source':rr['path'],'nativeReviewCrop':box,'image':im})
sheet=Image.new('RGB',(1000,3*300),(112,118,128));dr=ImageDraw.Draw(sheet)
for j,f in enumerate(focus):
 im=f.pop('image');x=j%4*250;y=j//4*300;back=Image.new('RGBA',im.size,(112,118,128,255));back.alpha_composite(im);sheet.paste(back.convert('RGB'),(x,y+36));dr.text((x+2,y+2),f"{f['clip']} {f['direction']} {f['index']} part{f['object'].split('fragment_')[1]}",fill='white');f['sheetRect']=[x,y+36,im.width,im.height]
sheet.save(P/'inspection/native-facet-focus.png')
dump(P/'inspection/native-facet-focus-map.json',focus)
summary={'baseline294Verified':len(base['files']),'packetBoundResourcesVerified':len(verified),'editorResourceManifestVerified':len(manifest['resources']),'captureCount':len(pixel),'rawReplayExact':sum(x['independentReplayVsSubmittedNative']['equalRGBA'] for x in pixel),'normalizedPublishedExact':sum(x['independentWholeFrameLanczosVsPublished']['equalRGBA']for x in pixel),'atlasPublishedExact':sum(x['atlasVsPublished']['equalRGBA']for x in pixel),'allTransparentOuterBorder':all(x['transparentNativeOuterBorder']for x in pixel),'actualGeometryWithinRootBudgetAndFrame':all(x['pass']for x in geom),'maxOfferedGeometryDifference':max(v for x in geom for v in x['offeredMeasurementMaxAbsDeltas'].values()),'historicalOriginal4xRawParity':'unavailable as retained in original preparation; not inferred from normalized original atlas parity'}
dump(P/'native/pixel-geometry-verification.json',{'summary':summary,'pixels':pixel,'geometry':geom});dump(P/'inspection/verified-preview-alias-cell-map.json',{'candidatePacketSHA256':sha(C/'packet.json'),'aliases':aliases,'deduplication':'Windup fouraliases share one exactpath/hash but all4rows independently inspected; same for active/recovery. No unseen uniquepreview listed as covered.'});dump(P/'resources/verified-packet-inputs.json',{'files':verified});print(json.dumps(summary,indent=2))
