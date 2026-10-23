from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,hashlib,subprocess
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');B=O/'candidates/round-04';OUT=O/'reviews/round-04-independent';P=json.loads((B/'packet.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cache={};items=[]
for section in ['files','candidateRenders','previews']:
 for k,v in P[section].items():
  p=(B/v['path']).resolve()
  if p not in cache:cache[p]=sha(p) if p.is_file() else None
  items.append({'section':section,'key':k,'path':str(p),'expected':v['sha256'],'actual':cache[p],'pass':cache[p]==v['sha256']})
records=json.loads((B/'atlas-records.json').read_text());frames=[];atlases=[]
for r in records:
 a=Image.open(O/r['path']);rr={'clip':r['clip'],'direction':r['direction'],'size':list(a.size),'mode':a.mode,'expectedSize':r['size'],'cells':[]}
 for i,rect in enumerate(r['rects']):
  p=B/'frames'/f"{r['clip']}-{r['direction']}"/f'{i:03d}.png';im=Image.open(p);x,y,w,h=rect;cell=a.crop((x,y,x+w,y+h));bb=im.getchannel('A').getbbox();row={'path':str(p),'sha256':sha(p),'clip':r['clip'],'direction':r['direction'],'frame0':i,'size':list(im.size),'mode':im.mode,'alphaBBox':bb,'border':min(bb[0],bb[1],896-bb[2],1344-bb[3]),'atlasCellExact':cell.tobytes()==im.tobytes()};frames.append(row);rr['cells'].append(row)
 atlases.append(rr)
closures=[]
for d in ['N','E','S','W']:
 f=B/'frames'/f'highlighted-{d}'/'000.png';p=B/'closure'/f'highlighted-{d}-013.png';a=Image.open(f);b=Image.open(p);closures.append({'direction':d,'exactRGBA':a.tobytes()==b.tobytes(),'phase0SHA256':sha(f),'closureSHA256':sha(p)})
# Exact current/public floor comparison and source resources closed under native link.
D=json.loads((B/'delivery.snapshot.json').read_text());streams=[]
for p in sorted((B/'previews').rglob('*.mp4')):
 r=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','quiet','-print_format','json','-show_streams','-show_format',str(p)]));v=next(x for x in r['streams'] if x['codec_type']=='video');streams.append({'path':str(p),'sha256':sha(p),'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'averageFPS':v['avg_frame_rate'],'frames':v.get('nb_frames'),'duration':v.get('duration')})
# New judge-only fixed crop source/candidate proof sheets, supplemental to whole registered sheets.
for clip,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for d in ['S','E','N','W']:
  ims=[Image.open(B/'frames'/f'{clip}-{d}'/f'{i:03d}.png').convert('RGBA') for i in range(n)];bbs=[im.getchannel('A').getbbox() for im in ims];box=(min(b[0] for b in bbs)-10,min(b[1] for b in bbs)-10,max(b[2] for b in bbs)+10,max(b[3] for b in bbs)+10)
  if clip=='idle':continue
  sh=Image.new('RGB',(1200,1110),(118,118,118));dr=ImageDraw.Draw(sh)
  for i,im in enumerate(ims):
   cr=im.crop(box);cr.thumbnail((296,338));tile=Image.new('RGBA',(300,370),(118,118,118,255));tile.alpha_composite(cr,((300-cr.width)//2,24+(338-cr.height)//2));sh.paste(tile.convert('RGB'),((i%4)*300,(i//4)*370));dr.text(((i%4)*300+5,(i//4)*370+3),f'{clip} {d} frame{i:02} fixed crop',fill='white')
  sh.save(OUT/f'candidate-{clip}-{d}-all12-fixedcrop.png')
# Context verification using original full frames at literal roots. No changes to candidate.
M=json.loads((B/'context-manifest.json').read_text());res=O/'source/round-04/resources/context';floor=Image.open(res/'floor-cream.png').convert('RGBA');chef=Image.open(res/'chef-lena-idle-S.png').convert('RGBA').crop((0,0,384,640));contextChecks=[]
def floorcanvas(w,h):
 im=Image.new('RGBA',(w*256+720,h*256+850),(27,34,41,255))
 for y in range(h):
  for x in range(w):im.alpha_composite(floor,(360+x*256,600+y*256))
 return im
for d in ['S','E','N','W']:
 im=Image.open(B/'frames'/f'idle-{d}'/'000.png').convert('RGBA');r=floorcanvas(5,3);r.alpha_composite(im,(616-448,856-896));r.alpha_composite(chef,(1256-192,728-496));p=B/'previews'/f'human-context-{d}.png';contextChecks.append({'type':'human','direction':d,'exactCompositing':r.convert('RGB').tobytes()==Image.open(p).tobytes(),'source':str(p)})
 r=floorcanvas(6,7)
 for x,y in [(0,0),(2,0),(0,2),(2,2),(0,5),(3,5)]:r.alpha_composite(im,(360+(x+1)*256-448,600+(y+1)*256-896))
 p=B/'previews'/f'repeated-{d}.png';contextChecks.append({'type':'repeatedAndGap','direction':d,'exactCompositing':r.convert('RGB').tobytes()==Image.open(p).tobytes(),'source':str(p)})
 r=floorcanvas(4,4);p=B/'previews/floor-reveal'/d/'after-consumer-removal.png';contextChecks.append({'type':'afterRemovalFloor','direction':d,'exactCompositing':r.convert('RGB').tobytes()==Image.open(p).tobytes(),'source':str(p)})
 for i in range(12):
  c=r.copy();c.alpha_composite(Image.open(B/'frames'/f'clearance-{d}'/f'{i:03d}.png').convert('RGBA'),(872-448,1112-896));p=B/'previews/floor-reveal'/d/f'clearance-{i:03d}.png';contextChecks.append({'type':'floorRevealPhase','direction':d,'frame0':i,'exactCompositing':c.convert('RGB').tobytes()==Image.open(p).tobytes(),'source':str(p)})
report={'packetSHA256':sha(B/'packet.json'),'briefSHA256':sha(O/'brief.json'),'projectSHA256':sha(O/'source/round-04/round-04.blend'),'deliverySnapshotSHA256':sha(B/'delivery.snapshot.json'),'uniqueHashFiles':len(cache),'hashEntries':len(items),'hashFailures':[x for x in items if not x['pass']],'hashChecks':items,'atlases':atlases,'frames':frames,'closures':closures,'minimumBorder':min(x['border'] for x in frames),'streams':streams,'contextChecks':contextChecks,'contextFailures':[x for x in contextChecks if not x['exactCompositing']],'resourceLinkedSource':{'path':str(O/'source/round-04/resources/original-library.blend'),'sha256':sha(O/'source/round-04/resources/original-library.blend')}}
(OUT/'packet-raster-context-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k in ['packetSHA256','briefSHA256','projectSHA256','deliverySnapshotSHA256','uniqueHashFiles','hashEntries','hashFailures','minimumBorder','contextFailures','resourceLinkedSource']},indent=2))
