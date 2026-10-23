from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,hashlib,math
P=Path(__file__).resolve().parent;O=P.parents[1];C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def compare(a,b):
 diff=ImageChops.difference(a,b);return {'decodedRGBAExact':not any(any(px) for px in diff.get_flattened_data()),'changedPixelsRGBA':sum(any(px) for px in diff.get_flattened_data()),'maxPerChannel':[v[1] for v in diff.getextrema()],'meanAbsRGBA':ImageStat.Stat(diff).mean}
packet=json.loads((C/'packet.json').read_text());bound=[]
for kind in ['files','candidateRenders','previews']:
 for alias,r in packet[kind].items():
  p=(C/r['path']).resolve();actual=sha(p);assert actual==r['sha256'],(alias,str(p));bound.append({'kind':kind,'alias':alias,'path':str(p.relative_to(O)) if p.is_relative_to(O) else str(p),'sha256':actual})
(P/'exact-packet-binding.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'candidateSourceSHA256':sha(O/'source/round-01.blend'),'records':bound},indent=2)+'\n')
replay=json.loads((P/'native-replay.json').read_text());native=[];physics={};canvas=[];crossmode=[];coverage=[]
(P/'evidence').mkdir(exist_ok=True)
for d in ['N','E','S','W']:
 rs=replay['frames'][d];first=rs[0];physics[d]={
 'rawUnion':[[min(r['rawCanonicalBounds'][0][j] for r in rs) for j in range(3)],[max(r['rawCanonicalBounds'][1][j] for r in rs) for j in range(3)]],
 'evaluatedUnion':[[min(r['evaluatedCanonicalBounds'][0][j] for r in rs) for j in range(3)],[max(r['evaluatedCanonicalBounds'][1][j] for r in rs) for j in range(3)]],
 'allBudgetPass':all(r[key][0][j]>=[-.73,-.30,-.06][j]-1e-5 and r[key][1][j]<=[.73,.30,1.48][j]+1e-5 for r in rs for key in ['rawCanonicalBounds','evaluatedCanonicalBounds'] for j in range(3)),
 'allOpenEntryCenters':all(not r['entryOpening']['normalSegmentHits'] and r['entryOpening']['nearestSurfaceDistance']>.4 for r in rs),
 'allGroundContactsFinite':all(v['evaluated']['area']>1e-8 for r in rs for v in r['finiteGroundContacts'].values()),
 'supportsStable':all(r['objects'][n]['matrixWorld']==first['objects'][n]['matrixWorld'] for r in rs for n in ['portal_rim__support_left','portal_rim__support_right']),
 'allConnectionsIntersectOrHaveIndependentInteriorWitness':all(c['intersectsOrInteriorWitness'] for r in rs for c in r['connections']),
 'source13Equals1Geometry':all(rs[12]['objects'][n].get('evaluatedGeometrySHA256')==first['objects'][n].get('evaluatedGeometrySHA256') for n in first['objects']),
 'source13Equals1Matrices':all(rs[12]['objects'][n]['matrixWorld']==first['objects'][n]['matrixWorld'] for n in first['objects']),
 'cameraStableAllPhases':all(r['camera']==first['camera'] for r in rs)}
 for mode in ['full-chromium','headless-shell']:
  sheet=Image.new('RGB',(6*194,2*412),(128,128,128));draw=ImageDraw.Draw(sheet)
  for i in range(12):
   actual=Image.open(C/f'evidence/canvases-{mode}'/d/f'{i:03d}.png').convert('RGBA');im=actual.resize((193,385),Image.Resampling.LANCZOS);x=(i%6)*194;y=(i//6)*412;sheet.paste(im,(x,y),im);draw.text((x+3,y+387),f'{d} {i:02d} · {mode}',fill='white');coverage.append({'sheet':f'evidence/browser-allphases-{mode}-{d}.png','cell':[i%6,i//6],'boundPath':f'candidates/round-01/evidence/canvases-{mode}/{d}/{i:03d}.png','sha256':sha(C/f'evidence/canvases-{mode}'/d/f'{i:03d}.png'),'wholeCanvas':True,'displaySize':[193,385]})
  sheet.save(P/'evidence'/f'browser-allphases-{mode}-{d}.png')
 atlas=Image.open(C/'published'/f'idle-{d}.png').convert('RGBA')
 for i in range(12):
  raw=Image.open(P/'raw/idle'/d/f'{i:03d}.png').convert('RGBA');submitted=Image.open(C/'raw/idle'/d/f'{i:03d}.png').convert('RGBA');pub=Image.open(C/'published/idle'/d/f'{i:03d}.png').convert('RGBA');reduced=raw.resize((384,768),Image.Resampling.LANCZOS);rect=[(i%6)*384,(i//6)*768,384,768];cell=atlas.crop((rect[0],rect[1],rect[0]+384,rect[1]+768));a=pub.getchannel('A');native.append({'direction':d,'frameIndex':i,'replayVsSubmittedNative':compare(raw,submitted),'independentWholeFrameReductionVsPublished':compare(reduced,pub),'publishedVsOriginalAtlasCell':compare(pub,cell),'publishedFrameSize':list(pub.size),'nativeFrameSize':list(raw.size),'alphaBounds':a.getbbox(),'maxBorderAlpha':max(max(a.crop(b).getextrema()) for b in [(0,0,384,1),(0,767,384,768),(0,0,1,768),(383,0,384,768)])})
  expected=Image.new('RGBA',(386,770));expected.paste(pub,(1,1));modes=[]
  for mode in ['full-chromium','headless-shell']:
   actual=Image.open(C/f'evidence/canvases-{mode}'/d/f'{i:03d}.png').convert('RGBA');cmp=compare(expected,actual);cmp['alphaExact']=not ImageChops.difference(expected.getchannel('A'),actual.getchannel('A')).getbbox();cmp['opaquePixelsRGBExact']=all(p[:3]==q[:3] for p,q in zip(expected.get_flattened_data(),actual.get_flattened_data()) if p[3]==255);canvas.append({'direction':d,'frameIndex':i,'mode':mode,'planSize':[386,770],'nativePlacement':[1,1,384,768],'comparison':cmp});modes.append(actual)
  crossmode.append({'direction':d,'frameIndex':i,**compare(*modes)})
(P/'pixel-and-native-metrics.json').write_text(json.dumps({'native':native,'physics':physics,'sourceSHA256Unchanged':replay['sourceSHA256']==replay['sourceSHA256After'],'nativeVsBoundBrowserCanvas':canvas,'boundBrowserModesCrossComparison':crossmode,'interpretation':'No repair. Transparent common native canvas places full publishedframe at1,1; browser premultiplied-alpha rounding and CSS display residuals remain distinct evidence layers.'},indent=2)+'\n')
(P/'browser-useful-pixel-coverage.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'files':coverage,'policy':'All96 actual browser native canvases, wholecanvas uniform intended-size sheet display; no APNG default or sparse-frame substitution.'},indent=2)+'\n')
print(json.dumps({'packetMembersVerified':len(bound),'all48NativeDecodedExact':all(r['replayVsSubmittedNative']['decodedRGBAExact'] for r in native),'maxNativeReplayChannels':[max(r['replayVsSubmittedNative']['maxPerChannel'][j] for r in native) for j in range(4)],'all48ReductionExact':all(r['independentWholeFrameReductionVsPublished']['decodedRGBAExact'] for r in native),'allAtlasCellsExact':all(r['publishedVsOriginalAtlasCell']['decodedRGBAExact'] for r in native),'maxBorderAlpha':max(r['maxBorderAlpha'] for r in native),'physics':physics,'all48BrowserModesDecodedExact':all(r['decodedRGBAExact'] for r in crossmode),'alphaExactAll96':all(r['comparison']['alphaExact'] for r in canvas),'opaqueRGBExactAll96':all(r['comparison']['opaquePixelsRGBExact'] for r in canvas)},indent=2))
