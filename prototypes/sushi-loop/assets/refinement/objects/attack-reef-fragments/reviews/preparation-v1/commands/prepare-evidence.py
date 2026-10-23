import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parents[7];A=W/'prototypes/sushi-loop/assets';C=json.loads((P/'resources/consumer/current-catalog-object.json').read_text());L=json.loads((P/'native/capture-ledger.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def diff(a,b):
 aa=np.asarray(a).astype(np.int16);bb=np.asarray(b).astype(np.int16);delta=np.abs(aa-bb);return {'equalRGBA':bool(np.array_equal(aa,bb)),'maxAbsRGBA':int(delta.max()),'meanAbsRGBA':float(delta.mean()),'changedPixels':int(np.any(delta,axis=2).sum()),'visibleMeanAbsRGB':float(delta[:,:,:3][np.maximum(aa[:,:,3],bb[:,:,3])>0].mean())}
comparisons=[];frames={};native_dir=P/'consumer/replay-atlases';native_dir.mkdir(exist_ok=True);currentraw=P/'resources/native/published-original-raw';currentraw.mkdir(exist_ok=True)
for c in C['clips']:
 for d,e in c['directions'].items():
  atlas=Image.open(P/'resources/consumer'/e['image']).convert('RGBA');sheet=Image.new('RGBA',e['atlasSize']);frames[(c['id'],d)]={'current':[],'replay':[]}
  for i,rect in enumerate(e['rects']):
   src=A/'production/source/registered/attack-reef-fragments'/f"{c['id']}-{d}"/'source-captures'/f'{i:03d}.png';dest=currentraw/f"{c['id']}-{d}-{i:03d}.png"
   if src.exists():shutil.copyfile(src,dest)
   native=Image.open(P/'native/frames'/c['id']/d/f'{i:03d}.png').convert('RGBA');oldraw=Image.open(dest).convert('RGBA') if dest.exists() else None;reduced=native.resize((640,896),Image.Resampling.LANCZOS);x,y,w,h=rect;old=atlas.crop((x,y,x+w,y+h));sheet.paste(reduced,(x,y));frames[(c['id'],d)]['current'].append(old);frames[(c['id'],d)]['replay'].append(reduced)
   comparisons.append({'clip':c['id'],'direction':d,'index':i,'savedOriginalRawPath':str(dest.relative_to(P)) if dest.exists() else None,'savedOriginalRawSHA256':sha(dest) if dest.exists() else None,'nativeRawDifference':diff(native,oldraw) if oldraw else None,'historicRawParity':'unavailable: guide references absent source-captures' if oldraw is None else 'measured','publishedDifferenceAfterWholeFrameLanczos':diff(reduced,old),'replayAlphaBounds':list(reduced.getchannel('A').getbbox() or []),'publishedAlphaBounds':list(old.getchannel('A').getbbox() or [])})
  sheet.save(native_dir/f"{c['id']}-{d}.png")
# Compact all-frame sheets at phone logical half-size (the entire registered canvas).
for c in C['clips']:
 for dataset in ['current','replay']:
  sheet=Image.new('RGB',(12*160,4*244),(112,118,128));dr=ImageDraw.Draw(sheet)
  for row,d in enumerate(['N','E','S','W']):
   for i,im in enumerate(frames[(c['id'],d)][dataset]):
    thumb=im.resize((160,224),Image.Resampling.LANCZOS);sheet.paste(thumb,(i*160,row*244+20),thumb);dr.text((i*160+4,row*244+3),f"{dataset} {c['id']} {d} {i:02}",fill='white')
  sheet.save(P/'native'/f"allframes-{dataset}-{c['id']}.png")
for bgname,bg in [('light',(246,242,232)),('gray',(112,118,128)),('dark',(18,26,42))]:
 for dataset in ['current','replay']:
  sheet=Image.new('RGB',(4*320,3*468),bg);dr=ImageDraw.Draw(sheet)
  for row,c in enumerate(C['clips']):
   for col,d in enumerate(['N','E','S','W']):
    im=frames[(c['id'],d)][dataset][5].resize((320,448),Image.Resampling.LANCZOS);sheet.paste(im,(col*320,row*468+20),im);dr.text((col*320+4,row*468+3),f"{dataset} {c['id']} {d} frame05",fill='black' if bgname=='light' else 'white')
  sheet.save(P/'native'/f"logical-{dataset}-{bgname}.png")
# Animated presentation grid replays whole one-shots in sequence; no authored loop closure claimed.
for dataset in ['current','replay']:
 motion=[]
 for c in C['clips']:
  for i in range(12):
   sheet=Image.new('RGB',(640,244),(112,118,128));dr=ImageDraw.Draw(sheet)
   for col,d in enumerate(['N','E','S','W']):
    im=frames[(c['id'],d)][dataset][i].resize((160,224),Image.Resampling.LANCZOS);sheet.paste(im,(col*160,20),im);dr.text((col*160+3,3),f"{c['id']} {d} {i:02}",fill='white')
   motion.append(sheet)
 motion[0].save(P/'native'/f'playback-{dataset}.webp',save_all=True,append_images=motion[1:],duration=[83,83,84]*12,loop=0,lossless=True)
# Summaries preserve enabled raw vs evaluated data independently.
r=L['captureRecords'];summary={'count':len(r),'rawVsEvaluated':'Identical per captured frame: no modifiers/shape keys in owned meshes. Both ledgers retained.','globalRawAuthoredBounds':{'min':[min(x['rawAuthoredBounds']['min'][i] for x in r) for i in range(3)],'max':[max(x['rawAuthoredBounds']['max'][i] for x in r) for i in range(3)]},'perClip':{},'projectedOutsideNativeCanvas':[]}
for c in C['clips']:
 rr=[x for x in r if x['clip']==c['id']];summary['perClip'][c['id']]={'rawAuthoredBounds':{'min':[min(x['rawAuthoredBounds']['min'][i] for x in rr) for i in range(3)],'max':[max(x['rawAuthoredBounds']['max'][i] for x in rr) for i in range(3)]},'terminal':[{k:x[k] for k in ['direction','index','rawAuthoredBounds','projectedEvaluatedBoundsNative']} for x in rr if x['index']==11]}
for x in r:
 b=x['projectedEvaluatedBoundsNative'];outside=b['min'][0]<0 or b['min'][1]<0 or b['max'][0]>1280 or b['max'][1]>1792
 if outside:summary['projectedOutsideNativeCanvas'].append({k:x[k] for k in ['clip','direction','index','projectedEvaluatedBoundsNative']})
summary['replayResidual']={'rawIdenticalFrames':sum(bool(x['nativeRawDifference'] and x['nativeRawDifference']['equalRGBA']) for x in comparisons),'publishedIdenticalFrames':sum(x['publishedDifferenceAfterWholeFrameLanczos']['equalRGBA'] for x in comparisons),'maxRawDifference':max([x['nativeRawDifference']['maxAbsRGBA'] for x in comparisons if x['nativeRawDifference']] or [None]),'maximumRawMeanAbsRGBA':max([x['nativeRawDifference']['meanAbsRGBA'] for x in comparisons if x['nativeRawDifference']] or [None]),'maximumPublishedMeanAbsRGBA':max(x['publishedDifferenceAfterWholeFrameLanczos']['meanAbsRGBA'] for x in comparisons),'historicRawMissingFrames':sum(x['nativeRawDifference'] is None for x in comparisons),'interpretation':'Untouched-source replay uses current Blender 5.2.2 LTS and frozen actual capture runtime, samples32. Renderer/platform/color/filter residuals against historic source pixels are measured; no claim of pixel-identical replay unless equalRGBA is true.'}
dump(P/'native/replay-comparison.json',{'processing':'Exact current atlas cell extraction vs native4x full-frame capture, uniformly reduced to published2x with Pillow LANCZOS. No fit, pixel repair or recolor.','frames':comparisons});dump(P/'native/summary.json',summary)
# Narrow the locator inventory to the own object and scene technical fields; all owned raw fields retained.
p=P/'native/locators.json';loc=json.loads(p.read_text());loc['scenes']=[{'name':s['name'],'camera':s['camera'],'issue':s['properties'].get('issue'),'source':s['properties'].get('source'),'ownedCollectionPresent':'S33_CFX_attack-reef-fragments.001' in s['children']} for s in loc['scenes']];loc.pop('images',None);dump(p,loc)
print(json.dumps(summary,indent=2))
