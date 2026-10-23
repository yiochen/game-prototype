from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib,math
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets');OBJ=BASE/'refinement/objects/garbage-shelving';OUT=OBJ/'reviews/source-audit';a=json.loads((OUT/'native-audit.json').read_text());r=json.loads((OUT/'published-raster-audit.json').read_text())
ps=a['phases']; phases={(p['clip'],p['direction'],p['frame0']):p for p in ps}
summary={'originalScene':a['scene'],'originalCollection':a['collection'],'blendSHA256':a['blendSHA256'],'savedUnrelatedCamera':{k:v for k,v in a['savedStateBeforeCapture'].items() if k!='sceneProperties'},'geometryCountsDescriptiveOnly':{'objects':len(a['objects']),'meshObjects':sum(o['type']=='MESH' for o in a['objects']),'vertices':sum(o['meshVertices'] or 0 for o in a['objects']),'faces':sum(o['meshFaces'] or 0 for o in a['objects']),'materials':len(a['materials'])},'clips':{},'shaderActions':[],'actionPaths':{},'resources':a['resources'],'libraries':a['libraries'],'comparisons':[]}
for clip in ['idle','highlighted','clearance']:
 x=[p for p in ps if p['clip']==clip and not p['closureDiagnostic']];s=[p for p in x if p['direction']=='S'];mn=[min(p['boundsMin'][i] for p in s) for i in range(3)];mx=[max(p['boundsMax'][i] for p in s) for i in range(3)]
 paths=sorted(set(c['dataPath'] for ac in a['actions'] if ac['clip']==clip for c in ac['curves']));summary['actionPaths'][clip]=paths
 closure=phases.get((clip,'S',12));idle=phases['idle','S',0]
 ratio=[]
 for p in s:
  by={o['name']:o for o in idle['objects']};changes=[]
  for o in p['objects']:
   b=by[o['name']]
   changes.append({'name':o['name'],'locationDelta':[o['location'][i]-b['location'][i] for i in range(3)],'zRotationDelta':o['rotationEuler'][2]-b['rotationEuler'][2],'scaleRatio':[o['scale'][i]/b['scale'][i] for i in range(3)],'hideRender':o['hideRender']})
  ratio.append({'frame0':p['frame0'],'objects':changes})
 summary['clips'][clip]={'frameCount':len(s),'rootLocalEnvelopeS':{'min':mn,'max':mx},'perFacingEnvelope':{d:{'min':[min(p['boundsMin'][i] for p in x if p['direction']==d) for i in range(3)],'max':[max(p['boundsMax'][i] for p in x if p['direction']==d) for i in range(3)],'projectedNativeUnion':[min(p['projectedNativeBounds'][i] for p in x if p['direction']==d) if i<2 else max(p['projectedNativeBounds'][i] for p in x if p['direction']==d) for i in range(4)]} for d in ['N','E','S','W']},'allMeshLocalCoordinatesUnchanged':all(o.get('meshLocalSHA256')==next(b.get('meshLocalSHA256') for b in idle['objects'] if b['name']==o['name']) for p in s for o in p['objects']),'anyHidden':any(o['hideRender'] or o['hideViewport'] for p in s for o in p['objects']),'perFrameTransformsRelativeIdle':ratio}
 if closure:summary['clips'][clip]['closureFrame13EqualsFrame1']=all(o['matrixWorld']==next(b['matrixWorld'] for b in phases[clip,'S',0]['objects'] if b['name']==o['name']) for o in closure['objects'])
for clip in ['idle','highlighted','clearance']:
 for d in ['N','E','S','W']:
  ims=[];pub=next(rr for rr in r['atlasFrames'] if rr['clip']==clip and rr['direction']==d);at=Image.open(pub['path']).convert('RGBA');n=1 if clip=='idle' else 12
  atlas=Image.new('RGBA',at.size)
  rows=[]
  for i in range(n):
   p=OUT/'native-original'/f'{clip}-{d}'/f'{i:03d}.png';im=Image.open(p).convert('RGBA');ims.append(im);box=((i%6)*896,(i//6)*1344);atlas.paste(im,box)
   x,y,w,h=(0,0,896,1344) if n==1 else ((i%6)*896,(i//6)*1344,896,1344);fr=at.crop((x,y,x+w,y+h));diff=ImageChops.difference(fr,im);alpha_diff=ImageChops.difference(fr.getchannel('A'),im.getchannel('A'))
   rows.append({'frame0':i,'nativeFile':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'nativeAlphaBBox':im.getchannel('A').getbbox(),'publishedAlphaBBox':fr.getchannel('A').getbbox(),'meanAbsDiffRGBA':ImageStat.Stat(diff).mean,'maxAlphaDiff':alpha_diff.getextrema()[1]})
  op=OUT/'native-original-atlases'/f'{clip}-{d}.png';op.parent.mkdir(exist_ok=True);atlas.save(op)
  summary['comparisons'].append({'clip':clip,'direction':d,'frames':rows,'nativeAtlas':str(op)})
  if n>1:
   bboxes=[im.getchannel('A').getbbox() for im in ims];box=(min(b[0] for b in bboxes)-12,min(b[1] for b in bboxes)-12,max(b[2] for b in bboxes)+12,max(b[3] for b in bboxes)+12);sh=Image.new('RGB',(1200,660),(118,118,118));dr=ImageDraw.Draw(sh)
   for i,im in enumerate(ims):
    cr=im.crop(box);cr.thumbnail((196,300));tile=Image.new('RGBA',(200,330),(118,118,118,255));tile.alpha_composite(cr,((200-cr.width)//2,20+(300-cr.height)//2));sh.paste(tile.convert('RGB'),((i%6)*200,(i//6)*330));dr.text(((i%6)*200+5,(i//6)*330+3),f'native {clip} {d} {i:02}',fill='white')
   sh.save(OUT/f'native-{clip}-{d}-all12.png')
# registered original native4view on neutral, and playback html with actual 12fps frame pacing.
sh=Image.new('RGBA',(896*4,1344),(118,118,118,255));dr=ImageDraw.Draw(sh)
for j,d in enumerate(['N','E','S','W']):
 im=Image.open(OUT/'native-original'/f'idle-{d}'/'000.png').convert('RGBA');sh.alpha_composite(im,(j*896,0));dr.text((j*896+10,10),f'Native idle {d}, no subject fit',fill='white')
sh.save(OUT/'native-idle-four-facing.png')
html='''<!doctype html><meta charset="utf-8"><title>Garbage shelving original native playback</title><style>body{background:#777;color:white;font:16px sans-serif}section{display:flex}figure{margin:8px}img{width:224px;height:336px;background:#777}h2{font-size:18px}</style><p>Source b1765262bfa897ad. Full registered frames scaled uniformly to phone224x336. 12fps. Highlighted loops; clearance stops on frame11; Restart replays clearance. No fade or object removal is added.</p><button onclick="start=performance.now()">Restart</button>'''
for clip in ['highlighted','clearance']:
 html+=f'<h2>{clip}</h2><section>'+''.join(f'<figure><figcaption>{d}</figcaption><img id="{clip}-{d}" src="native-original/{clip}-{d}/000.png"></figure>' for d in ['N','E','S','W'])+'</section>'
html+='''<script>let start=performance.now();function step(){let k=Math.floor((performance.now()-start)*12/1000);for(let c of ['highlighted','clearance'])for(let d of ['N','E','S','W'])document.getElementById(c+'-'+d).src='native-original/'+c+'-'+d+'/'+String(c==='highlighted'?k%12:Math.min(11,k)).padStart(3,'0')+'.png';requestAnimationFrame(step)}step()</script>'''
(OUT/'original-native-playback.html').write_text(html)
(OUT/'native-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'counts':summary['geometryCountsDescriptiveOnly'],'actionPaths':summary['actionPaths'],'clips':{c:{k:v for k,v in x.items() if k!='perFrameTransformsRelativeIdle'} for c,x in summary['clips'].items()},'maxMeanRGBAdifference':max(max(f['meanAbsDiffRGBA']) for rr in summary['comparisons'] for f in rr['frames'])},indent=2))
