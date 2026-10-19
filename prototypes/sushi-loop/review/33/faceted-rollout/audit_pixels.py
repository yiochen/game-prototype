"""Independent native/source/atlas verification; no image files are rewritten.

Capture original flat-artwork hashes first with --snapshot-flat FILE. Later run
--raw RAW --old-raw OLD --records RECORDS --project PROJECT --output REPORT;
add --published to audit all117 runtime entries and --flat-reference FILE.
Unchanged alpha is measured, not assumed: illumination can affect native
translucent surfaces. Large alpha differences are separately listed for review.
"""
import argparse, copy, hashlib, json, sys, time
from pathlib import Path
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
PRODUCTION=REPO/'prototypes/sushi-loop/assets/production'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
def image(path):
 with Image.open(path) as opened:return opened.convert('RGBA')
def flat_snapshot():
 native=set(json.loads((PRODUCTION/'source/native-records/index.json').read_text())['assetIds']);lib=json.loads((PRODUCTION/'library.json').read_text());result={}
 for a in lib['objects']:
  if a['id'] in native:continue
  paths=sorted({d['image'] for c in a['clips'] for d in c['directions'].values()});result[a['id']]={p:sha(PRODUCTION/p) for p in paths}
 return {'objects':result,'count':len(result)}
def frames(records,aid):
 a=json.loads((records/aid/'asset.json').read_text());rig=json.loads((records/aid/'rig.json').read_text())
 for clip,c in rig['clips'].items():
  for d in a.get('directions',['N','E','S','W']):
   for f in range(c['frames']):yield a,clip,c,d,f,Path(aid)/(clip+'-'+d)/(str(f).zfill(3)+'.png')
def raw_audit(args):
 ids=args.ids or sorted(p.parent.name for p in args.records.glob('*/asset.json'));result={'projectSHA256':sha(args.project),'rawRoot':str(args.raw),'oldRawRoot':str(args.old_raw),'issues':[],'warnings':[],'assets':{},'frames':0,'alphaIdenticalFrames':0,'largeAlphaChangeFrames':0,'missingOldFrames':0}
 check=lambda ok,msg:result['issues'].append(msg) if not ok else None
 for aid in ids:
  stats={'frames':0,'alphaIdenticalFrames':0,'largeAlphaChangeFrames':0,'maxAlphaDifference':0,'maxAlphaChangedFraction':0,'oldAndNewAlphaBoundsDiffer':0,'groups':{},'representativeOpaqueClipping':{},'missing':[]};groups={}
  for a,clip,recipe,d,f,relative in frames(args.records,aid):
   path=args.raw/relative
   if not path.exists():stats['missing'].append(str(relative));continue
   rgba=image(path);arr=np.asarray(rgba);alpha=arr[:,:,3];count=recipe['frames'];expected=[v*a['scale'] for v in a['frame']];check(list(rgba.size)==expected,str(relative)+': wrong dimensions')
   receipt=path.with_suffix('.capture.json');check(receipt.exists(),str(relative)+': missing completed receipt')
   if receipt.exists():
    r=json.loads(receipt.read_text());check(r.get('state')=='complete' and r.get('sha256')==sha(path) and r.get('index')==f and r.get('assetId')==aid and r.get('direction')==d and r.get('clip')==clip,str(relative)+': receipt mismatch')
   bbox=rgba.getchannel('A').getbbox();allowed_empty=(clip=='appear' and f==0) or (clip=='fade' and f==count-1) or f in recipe.get('allowEmptyFrames',[])
   check(bool(bbox) or allowed_empty,str(relative)+': unexpected empty frame')
   if bbox and not aid.startswith('floor-'):
    # Native alpha <=2 at an outermost antialiasing pixel is recorded separately.
    opaque=Image.fromarray((alpha>2).astype('uint8')*255).getbbox()
    check(not opaque or (opaque[0]>0 and opaque[1]>0 and opaque[2]<rgba.width and opaque[3]<rgba.height),str(relative)+': alpha touches capture edge')
   g=groups.setdefault(clip+'/'+d,{'recipe':recipe,'visible':set(),'rgba':set(),'frames':0,'nativeVersions':set()});g['visible'].add(digest(rgba.convert('RGBa').tobytes()));g['rgba'].add(digest(rgba.tobytes()));g['frames']+=1
   if receipt.exists():g['nativeVersions'].add(r.get('nativeVersion'))
   if f==0:
    opaque=alpha>=250;denom=int(opaque.sum());stats['representativeOpaqueClipping'][clip+'/'+d]={'opaquePixels':denom,'RGBChannelClippedFraction':[float(((arr[:,:,channel]>=254)&opaque).sum()/denom) if denom else 0 for channel in range(3)]}
   oldpath=args.old_raw/relative
   if oldpath.exists():
    old=image(oldpath);check(old.size==rgba.size,str(relative)+': old/new size changed')
    if old.size==rgba.size:
     aa=np.asarray(old)[:,:,3].astype('int16');delta=np.abs(alpha.astype('int16')-aa);n=int((delta>0).sum());fraction=n/alpha.size;maximum=int(delta.max());stats['maxAlphaDifference']=max(stats['maxAlphaDifference'],maximum);stats['maxAlphaChangedFraction']=max(stats['maxAlphaChangedFraction'],fraction)
     if n==0:stats['alphaIdenticalFrames']+=1
     if maximum>8 and float((delta>8).sum()/alpha.size)>.01:stats['largeAlphaChangeFrames']+=1
     if old.getchannel('A').getbbox()!=bbox:stats['oldAndNewAlphaBoundsDiffer']+=1
   else:result['missingOldFrames']+=1
   stats['frames']+=1
  for key,g in groups.items():
   recipe=g.pop('recipe');g['uniqueVisibleFrames']=len(g.pop('visible'));g['uniqueRGBAFrames']=len(g.pop('rgba'));g['nativeVersions']=sorted(g['nativeVersions']);stats['groups'][key]=g
   check(g['frames']==recipe['frames'],aid+'/'+key+': incomplete frame group');check(len(g['nativeVersions'])==1,aid+'/'+key+': mixed source receipts')
   if recipe['frames']>1 and not recipe.get('static'):check(g['uniqueVisibleFrames']>=6,aid+'/'+key+': fewer than six visible frames')
   if aid.startswith('belt-'):check(g['frames']==24 and g['uniqueVisibleFrames']==24,aid+'/'+key+': incomplete/aliased24framebelt')
  check(not stats['missing'],aid+': missing '+str(len(stats['missing']))+' native PNGs');result['frames']+=stats['frames'];result['alphaIdenticalFrames']+=stats['alphaIdenticalFrames'];result['largeAlphaChangeFrames']+=stats['largeAlphaChangeFrames'];result['assets'][aid]=stats
  if stats['largeAlphaChangeFrames']:result['warnings'].append(aid+': '+str(stats['largeAlphaChangeFrames'])+' frames have >1% canvas pixels changing alpha by >8/255; review translucent materials')
  print('PIXEL_AUDIT '+aid+' '+str(stats['frames']),flush=True)

 if not args.ids:check(len(ids)==104,'Native object count differs104');check(result['frames']==9390,'Native frame count differs9390')
 check(result['missingOldFrames']==0,'Prior source PNGs missing')
 result['passed']=not result['issues'];return result

def watch_native(args):
 ids=sorted(p.parent.name for p in args.records.glob('*/asset.json'));pending=list(ids);done={};started=time.monotonic()
 while pending:
  progressed=False
  for aid in list(pending):
   planned=list(frames(args.records,aid))
   if not all((args.raw/row[-1]).exists() and (args.raw/row[-1]).with_suffix('.capture.json').exists() for row in planned):continue
   selected=copy.copy(args);selected.ids=[aid];done[aid]=raw_audit(selected);pending.remove(aid);progressed=True
   write(args.output.with_name('audit-pixels-progress.json'),{'completeAssets':len(done),'pendingAssets':pending,'issues':[issue for report in done.values() for issue in report['issues']]})
  if not pending:break
  if time.monotonic()-started>args.timeout:raise TimeoutError('Native capture audit waiting for '+','.join(pending))
  if not progressed:time.sleep(8)
 merged={'projectSHA256':sha(args.project),'rawRoot':str(args.raw),'oldRawRoot':str(args.old_raw),'issues':[],'warnings':[],'assets':{},'frames':0,'alphaIdenticalFrames':0,'largeAlphaChangeFrames':0,'missingOldFrames':0}
 for aid in ids:
  report=done[aid];merged['assets'].update(report['assets']);merged['issues'].extend(report['issues']);merged['warnings'].extend(report['warnings'])
  for key in ('frames','alphaIdenticalFrames','largeAlphaChangeFrames','missingOldFrames'):merged[key]+=report[key]
 if len(merged['assets'])!=104 or merged['frames']!=9390:merged['issues'].append('Full native object/frame totals differ104/9390')
 merged['passed']=not merged['issues'];return merged

def atlas_audit(args):
 lib=json.loads((PRODUCTION/'library.json').read_text());report={'objects':{},'issues':[],'frameFacingContexts':0,'distinctAtlasPaths':set(),'maximumAtlasDimension':0,'adaptiveColumnGroups':[],'wholeFrameUniformSampleVerified':0};cache={};native=set(json.loads((PRODUCTION/'source/native-records/index.json').read_text())['assetIds'])
 check=lambda ok,msg:report['issues'].append(msg) if not ok else None
 for a in lib['objects']:
  stats={'groups':{},'frames':0}
  for c in a['clips']:
   check(c['fps']==12,a['id']+'/'+c['id']+': FPS differs12')
   for d,values in c['directions'].items():
    path=values['image'];report['distinctAtlasPaths'].add(path)
    if path not in cache:cache[path]=image(PRODUCTION/path)
    atlas=cache[path];report['maximumAtlasDimension']=max(report['maximumAtlasDimension'],*atlas.size);check(max(atlas.size)<=8192,path+': exceeds8192texturecap');rects=values['rects'];check(list(atlas.size)==values['atlasSize'],path+': atlas size differs');check(len(rects)==c['frames'],path+': rect count differs');hashes=set()
    if values['columns']!=min(6,c['frames']):report['adaptiveColumnGroups'].append({'asset':a['id'],'clip':c['id'],'direction':d,'columns':values['columns'],'size':list(atlas.size),'frameSize':[v*a['sourceScale'] for v in a['frameSize']]})
    for index,rect in enumerate(rects):
     x,y,w,h=rect;check(x>=0 and y>=0 and x+w<=atlas.width and y+h<=atlas.height,path+': rect outside atlas');check([w,h]==[v*a['sourceScale'] for v in a['frameSize']],path+': rect registration size differs');cell=atlas.crop((x,y,x+w,y+h));hashes.add(digest(cell.convert('RGBa').tobytes()))
     if args.atlas_raw and a['id'] in native:
      raw=args.atlas_raw/a['id']/(c.get('sourceClipId',c['id'])+'-'+d)/(str(index).zfill(3)+'.png')
      check(raw.exists(),path+': missing native capture '+str(raw))
      if raw.exists():
       original=image(raw);sample=original.resize((w,h),Image.Resampling.LANCZOS) if original.size!=(w,h) else original
       check(sample.tobytes()==cell.tobytes(),path+'/'+str(index)+': runtime cell differs from uniform full-frame native sample');report['wholeFrameUniformSampleVerified']+=1
    group={'frames':len(rects),'uniqueVisibleFrames':len(hashes)};stats['groups'][c['id']+'/'+d]=group;stats['frames']+=len(rects)
    if c['frames']>1 and not c.get('static'):check(len(hashes)>=6,path+': fewer than6 distinctvisible frames')
    if a['id'].startswith('belt-'):check(c['frames']==24 and len(hashes)==24,path+': belt24frameslost')
  report['objects'][a['id']]=stats;report['frameFacingContexts']+=stats['frames'];print('ATLAS_AUDIT '+a['id'],flush=True)
  # A sheet is shared only inside one object's directional views. Drop decoded
  # image buffers here rather than retaining hundreds of large atlases.
  cache.clear()
 check(len(lib['objects'])==117,'Active catalog count differs117');check(report['frameFacingContexts']==11082,'Published frame/facing contexts differ11082');report['distinctAtlasPaths']=len(report['distinctAtlasPaths']);report['passed']=not report['issues'];return report

def main(args):
 if args.snapshot_flat:write(args.snapshot_flat,flat_snapshot());return
 report={}
 if args.raw:report['native']=watch_native(args) if args.watch else raw_audit(args)
 if args.published:report['published']=atlas_audit(args)
 if args.flat_reference:
  before=json.loads(args.flat_reference.read_text());after=flat_snapshot();report['flatArtwork']={'count':after['count'],'unchanged':before==after,'passed':before==after}
 report['passed']=all(v.get('passed',False) for v in report.values());write(args.output,report);print(json.dumps({'passed':report['passed'],'output':str(args.output),'summaries':{k:{f:v.get(f) for f in ('frames','alphaIdenticalFrames','largeAlphaChangeFrames','frameFacingContexts','distinctAtlasPaths','count','unchanged','issues','warnings') if f in v} for k,v in report.items() if isinstance(v,dict)}}),flush=True)
 if not report['passed']:sys.exit(1)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path);p.add_argument('--old-raw',type=Path);p.add_argument('--records',type=Path);p.add_argument('--project',type=Path);p.add_argument('--output',type=Path);p.add_argument('--snapshot-flat',type=Path);p.add_argument('--flat-reference',type=Path);p.add_argument('--published',action='store_true');p.add_argument('--atlas-raw',type=Path);p.add_argument('--watch',action='store_true');p.add_argument('--timeout',type=float,default=14400);p.add_argument('--ids',nargs='+');main(p.parse_args())
