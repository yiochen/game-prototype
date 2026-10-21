from PIL import Image,ImageDraw
import numpy as np,pathlib,json,hashlib
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-08';V=json.load(open(O/'validation.json'));H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def mip(im):
 a=np.asarray(im,dtype=float);a[:,:,:3]*=a[:,:,3:]/255;h,w=a.shape[:2];m=a.reshape(h//2,2,w//2,2,4).mean(axis=(1,3));out=m.copy();out[:,:,:3]=np.divide(out[:,:,:3]*255,out[:,:,3:],out=np.zeros_like(out[:,:,:3]),where=out[:,:,3:]>0);return Image.fromarray(np.rint(out).clip(0,255).astype('uint8')),m
def pm(im):
 a=np.asarray(im,dtype=float);a[:,:,:3]*=a[:,:,3:]/255;return a
def bg(im,color):
 c=Image.new('RGBA',im.size,(*color,255));c.alpha_composite(im);return c.convert('RGB')
rows=[]
for d in 'NESW':
 off=[(128,0),(128,128),(128,256)] if d in 'NS' else [(0,128),(128,128),(256,128)];rois=[[160,248,128,21],[160,376,128,21]] if d in 'NS' else [[158,248,4,180],[286,248,4,180]]
 pixhash=[]
 for i in range(25):
  raw=Image.open(O/'frames'/f'running-{d}-{i:02d}.png').convert('RGBA');pixhash.append(hashlib.sha256(raw.tobytes()).hexdigest());small,_=mip(raw);ass=Image.new('RGBA',(448,608))
  for pos in off:ass.alpha_composite(small,pos)
  nat=Image.open(O/'native-runs'/f'native-{d}-{i:02d}.png').convert('RGBA');nativeSmall,nativePM=mip(nat);delta=abs(nativePM-pm(ass));row={'direction':d,'index':i,'fullAlphaMax':float(delta[:,:,3].max()),'fullPremultipliedRGBMax':float(delta[:,:,:3].max()),'joins':[]}
  for x,y,w,h in rois:
   e=delta[y:y+h,x:x+w];row['joins'].append({'rect':[x,y,w,h],'alphaMax':float(e[:,:,3].max()),'premultipliedRGBMax':float(e[:,:,:3].max()),'alphaOver8Pixels':int(np.count_nonzero(e[:,:,3]>8))})
  rows.append(row);ap=O/'filtered-game-scale'/f'individual-exact-mip1-first-{d}-{i:02d}.png';ass.save(ap);nativeSmall.save(O/'filtered-game-scale'/f'native-exact-mip1-{d}-{i:02d}.png')
  if d in 'NE' and i in [0,1,6,12,18,23,24]:
   sheet=Image.new('RGB',(448*3,632*2),(243,243,238));draw=ImageDraw.Draw(sheet)
   for col,(label,color) in enumerate([('light',(230,233,228)),('gray',(120,125,128)),('dark',(24,30,36))]):
    for r,(name,im) in enumerate([('Native3 mip1',nativeSmall),('Individual sprite mip1 then RGBA3',ass)]):
     sheet.paste(bg(im,color),(448*col,632*r+24));draw.text((448*col+8,632*r+6),f'{d} / {i:02d} / {name} / {label}',fill=(24,30,36))
   sheet.save(O/'filtered-game-scale'/f'critical-mip1-{d}-{i:02d}.png')
   patches=[]
   for x,y,w,h in rois:
    for im in [nativeSmall,ass]:
     part=im.crop((x,y,x+w,y+h));patches.append(bg(part,(120,125,128)).resize((w*4,h*4),Image.Resampling.NEAREST))
   sh=Image.new('RGB',(max(x.width for x in patches),sum(x.height for x in patches)),(120,125,128));y=0
   for part in patches:sh.paste(part,(0,y));y+=part.height
   sh.save(O/'filtered-game-scale'/f'critical-mip1-joins-enlarged-{d}-{i:02d}.png')
 V['loopClosurePixels'][d].update(equal=pixhash[0]==pixhash[24],uniquePixelFrameCount=len(set(pixhash[:24])),firstPixelSHA256=pixhash[0],closurePixelSHA256=pixhash[24])
metrics={'method':'Native source pixels premultiplied by alpha, then each2x2 texel block averaged as ideal level1 mipmap. Each individual sprite mip1 converted to8-bit RGBA and composited at exact logical roots. Compare against full native3 premultiplied2x2 mip1. No wider Pillow minification kernel.0..255 units; unquantized native mean retained for stats, so≤.5 alpha error is quantization.','runtimeSource':'prototypes/sushi-loop/godot/scripts/restaurant_view.gd:42 TEXTURE_FILTER_LINEAR_WITH_MIPMAPS','frames':rows,'summaryByFacing':{d:{'joinAlphaMax':max(j['alphaMax'] for r in rows if r['direction']==d for j in r['joins']),'joinRGBMax':max(j['premultipliedRGBMax'] for r in rows if r['direction']==d for j in r['joins'])} for d in 'NESW'}}
(O/'mip1-continuity-metrics.json').write_text(json.dumps(metrics,indent=2));V['mip1ContinuityMetrics']=str(O/'mip1-continuity-metrics.json');V['mip1ContinuitySummary']=metrics['summaryByFacing'];V['knownLimitations']=[{'id':'independent-linear-mipmap-filtering','status':'unresolved','description':'At source-scale2 raw assembly, alltime join alpha is exact and RGB≤1/255. Independently filtering each sprite before compositing at logical scale reintroduces N/S outer rail silhouette opacity/color overlap. Exact2x2 mip1 confirms this is not just Pillow wide-kernel behavior. Root/camera/ports and exact source profiles were preserved, no overhang or raster correction used. Runtime composite/filter handling requires coordinator review before game integration.','evidence':str(O/'mip1-continuity-metrics.json')}];(O/'validation.json').write_text(json.dumps(V,indent=2))
known={'candidate':'round-08','status':'awaiting-independent-judge','rawJoinEvidence':V['continuitySummary'],'mip1GameScaleEvidence':metrics['summaryByFacing'],'technicalConflict':V['knownLimitations'][0],'sourceSettings':'Explicit CPU Cycles,1 deterministic TABULATED_SOBOL sample,scrambling_distance0,BOX1,denoisingOFF,dither0. CPU chosen to make actual device explicit; output is deterministic native procedural toon shading.','closure':V['loopClosurePixels']};(O/'known-issues.json').write_text(json.dumps(known,indent=2))
family=json.load(open(P/'source/family-settings.json'));family['filterCompatibility']=known['mip1GameScaleEvidence'];family['knownLimitation']=known['technicalConflict'];(P/'source/family-settings.json').write_text(json.dumps(family,indent=2))
d=json.load(open(P/'delivery.json'));d['knownIssues']=str(O/'known-issues.json');d['previews']['game-mip1-critical-N']=str(O/'filtered-game-scale/critical-mip1-N-12.png');d['previews']['game-mip1-critical-E']=str(O/'filtered-game-scale/critical-mip1-E-12.png');d['previews']['game-mip1-N-joins-enlarged']=str(O/'filtered-game-scale/critical-mip1-joins-enlarged-N-12.png');d['resources']=[str(p) for p in O.rglob('*') if p.is_file() and p.name not in ['delivery.json']]+[str(P/'source/family-settings.json'),str(P/'source/capture_round08.py'),str(P/'source/pack_round08.py'),str(P/'source/record_family_round08.py'),str(P/'source/check_filtered_mip_round08.py'),str(P/'source/source-inspection.json')];d['resources']=sorted(set(d['resources']));(P/'delivery.json').write_text(json.dumps(d,indent=2));(O/'delivery.json').write_text(json.dumps(d,indent=2))
# Complete hash manifest for root sealing. Does not claim review approval.
files=[pathlib.Path(d['project']),pathlib.Path(d['recipe']),pathlib.Path(d['validation'])]+[pathlib.Path(p) for p in d['resources']];manifest={'asset':'belt-straight-n','round':8,'status':'candidate-awaiting-independent-judge','files':[{'path':str(p),'sha256':H(p),'size':p.stat().st_size} for p in sorted(set(files))]};(O/'editor-handoff-hashes.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(metrics['summaryByFacing'],indent=2));print('FILES',len(manifest['files']),'RAW',len(d['rawFrames']),'ATLASES',len(d['atlases']),'SOURCE',d['project'])
