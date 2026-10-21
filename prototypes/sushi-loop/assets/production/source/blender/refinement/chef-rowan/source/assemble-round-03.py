"""Pack untouched native frames; build clearly labeled diagnostic assemblies."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,subprocess,html,sys

HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03'
PROD=HERE/'round02-context-resources'
catalog=json.loads((OBJ/'inputs/catalog-object.json').read_text())
brief=json.loads((OBJ/'brief-v4-food-occlusion.json').read_text())
lib={o['id']:o for o in json.loads((PROD/'library.json').read_text())['objects']}
DIRECTIONS=['N','E','S','W'];CLIPS=['idle','work','hold','load']
for d in ['atlases','sheets','playbacks','contexts','context-frames']:(OUT/d).mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame(clip,direction,index):return Image.open(OUT/'frames'/f'{clip}-{direction}-{index:02}.png').convert('RGBA')
def rgb(im,color):
 bg=Image.new('RGB',im.size,color);bg.paste(im,mask=im.getchannel('A'));return bg
def video(images,path):
 images=list(images);w,h=images[0].size
 command=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r','12','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
 if '--reuse-videos' not in sys.argv or not path.exists():
  p=subprocess.Popen(command,stdin=subprocess.PIPE)
  for im in images:p.stdin.write(im.convert('RGB').tobytes())
  p.stdin.close();assert p.wait()==0
 probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,nb_frames,duration,width,height','-of','json',str(path)]))['streams'][0]
 assert probe['r_frame_rate']=='12/1' and int(probe['nb_frames'])==12
 return probe
def sheet(images,labels,columns=6,bg=(102,107,113),size=(192,320)):
 images=list(images);rows=(len(images)+columns-1)//columns
 result=Image.new('RGB',(columns*size[0],rows*(size[1]+20)),bg);d=ImageDraw.Draw(result)
 for i,(im,label) in enumerate(zip(images,labels)):
  x=i%columns*size[0];y=i//columns*(size[1]+20)
  im=im.resize(size,Image.Resampling.LANCZOS)
  result.paste(im,(x,y+20),im if im.mode=='RGBA' else None)
  d.text((x+6,y+4),label,fill='white' if sum(bg)<500 else '#242932')
 return result

records=[];atlas_records=[];timing=[]
capture_lines=(OUT/'capture.log').read_text().splitlines()
captured=[tuple(line.split()[1:]) for line in capture_lines if line.startswith('CAPTURE ')]
assert len(captured)==192 and len(set(captured))==192,'Final native capture log must contain exactly192 unique indexed capture records'
for clip in CLIPS:
 for direction in DIRECTIONS:
  images=[frame(clip,direction,i) for i in range(12)]
  atlas=Image.new('RGBA',(2304,1280))
  for i,im in enumerate(images):
   assert im.size==(384,640)
   alpha=im.getchannel('A');bbox=alpha.getbbox();assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<384 and bbox[3]<640
   path=OUT/'frames'/f'{clip}-{direction}-{i:02}.png'
   records.append(dict(index=len(records),clip=clip,direction=direction,frame=i,sourceNativeFrame=i+1,path=str(path.relative_to(OBJ)),sha256=sha(path),size=list(im.size),alphaBounds=bbox))
   atlas.paste(im,(i%6*384,i//6*640))
  path=OUT/'atlases'/f'{clip}-{direction}.png';atlas.save(path)
  for i,im in enumerate(images):assert atlas.crop((i%6*384,i//6*640,i%6*384+384,i//6*640+640)).tobytes()==im.tobytes()
  atlas_records.append(dict(clip=clip,direction=direction,path=str(path.relative_to(OBJ)),sha256=sha(path),columns=6,rows=2,size=[2304,1280],rects=[[i%6*384,i//6*640,384,640] for i in range(12)]))
  sheet(images,[f'{clip} {direction} frame{i:02}' for i in range(12)]).save(OUT/'sheets'/f'all12-{clip}-{direction}.png')
  path=OUT/'playbacks'/f'{clip}-{direction}.mp4'
  probe=video([rgb(im,(86,91,98)) for im in images],path)
  timing.append(dict(clip=clip,direction=direction,path=str(path.relative_to(OBJ)),fps=12,frames=12,loop=clip!='load',probe=probe,sha256=sha(path)))
for direction in DIRECTIONS:
 images=[frame(c,direction,i) for c in CLIPS for i in range(12)]
 labels=[f'{c} {direction} {i:02}' for c in CLIPS for i in range(12)]
 sheet(images,labels,12,size=(128,214)).save(OUT/'sheets'/f'all48-{direction}.png')

# Whole-frame consistent-registration comparisons. No silhouette fitting.
original_clips={c['id']:c for c in catalog['clips']}
def published(asset,clip,direction,index=0):
 c=next(c for c in asset['clips'] if c['id']==clip);dr=c['directions'][direction]
 im=Image.open(PROD/dr['image']).convert('RGBA');rect=dr['rects'][index%c['frames']]
 return im.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
images=[];labels=[]
for direction in DIRECTIONS:
 images.extend([published(catalog,'idle',direction),frame('idle',direction,0)]);labels.extend([f'Original {direction}',f'Round03 {direction}'])
sheet(images,labels,4).save(OUT/'sheets/comparison-registered.png')
sheet([frame('idle',d,0) for d in DIRECTIONS],DIRECTIONS,4).save(OUT/'sheets/four-view-sheet.png')
for name,color in [('light',(242,237,226)),('gray',(119,123,128)),('dark',(29,36,44))]:
 images=[frame(c,d,5 if c=='load' else 0) for c in CLIPS for d in DIRECTIONS]
 labels=[f'{c} {d}' for c in CLIPS for d in DIRECTIONS]
 sheet(images,labels,4,color).save(OUT/'sheets'/f'readability-{name}.png')
# Cropped diagnostics are explicitly separate from complete native exports.
images=[frame(c,d,5 if c=='load' else 0).crop((68,160,316,530)) for c in CLIPS for d in DIRECTIONS]
sheet(images,[f'Diagnostic crop: {c} {d}' for c in CLIPS for d in DIRECTIONS],4,size=(248,370)).save(OUT/'sheets/details-diagnostic.png')

# These are independent sprite assemblies at the game's square 128px grid,
# using complete source frames and their documented roots. No 3D join implied.
context_records=[]
def place(canvas,im,asset,x,y,offset=(0,0),direction='S'):
 scale=asset['sourceScale'];logical=im.resize((round(im.width/scale),round(im.height/scale)),Image.Resampling.LANCZOS)
 footprint=asset.get('directionFootprints',{}).get(direction,asset.get('footprint',[1,1]))
 rc=asset.get('directionRootCells',{}).get(direction,asset.get('rootCell',[footprint[0]/2,footprint[1]/2]))
 px=(x+rc[0])*128+offset[0];py=192+(y+rc[1])*128+offset[1]
 left=round(px-asset['root'][0]);top=round(py-asset['root'][1])
 canvas.paste(logical,(left,top),logical)
 return dict(asset=asset['id'],grid=[x,y],direction=direction,rootLogical=[px,py],sourceRoot=asset['root'],sourceScale=scale)
for clip in ['hold','load']:
 for direction in DIRECTIONS:
  images=[];placements=None
  for i in range(12):
   canvas=Image.new('RGB',(640,768),(226,218,199));d=ImageDraw.Draw(canvas)
   d.text((18,18),f'Native sprite assembly: Rowan {clip} {direction} / frame{i:02} / 12 fps',fill='#242932')
   d.text((18,38),'Original 128px grid, fixed roots; published native neighbor belt.',fill='#414b53')
   for x in range(6):d.line((x*128,192,x*128,704),fill=(202,195,180))
   for y in range(5):d.line((0,192+y*128,640,192+y*128),fill=(202,195,180))
   dx,dy={'S':(0,1),'N':(0,-1),'E':(1,0),'W':(-1,0)}[direction]
   objects=[(lib['chef-blackboard'],'idle','S',0,1), (lib['belt-straight-e'],'running',direction,2+dx,1+dy), (catalog,clip,direction,2,1)]
   objects.sort(key=lambda r:r[4]+r[0].get('rootCell',[.5,.5])[1])
   placements=[]
   for asset,ac,ad,x,y in objects:
    im=frame(clip,direction,i) if asset['id']=='chef-rowan' else published(asset,ac,ad,0)
    placements.append(place(canvas,im,asset,x,y,direction=ad))
   path=OUT/'context-frames'/f'{clip}-{direction}-{i:02}.png';canvas.save(path)
   images.append(canvas)
  path=OUT/'contexts'/f'neighbor-{clip}-{direction}.mp4';probe=video(images,path)
  sheet(images,[f'{clip} {direction} frame{i:02}' for i in range(12)],6,bg=(226,218,199),size=(320,384)).save(OUT/'contexts'/f'all12-neighbor-{clip}-{direction}.png')
  images[5 if clip=='load' else 0].save(OUT/'contexts'/f'neighbor-{clip}-{direction}.png')
  context_records.append(dict(clip=clip,direction=direction,representation='Independent whole-frame native sprite assembly; not a single 3D scene',path=str(path.relative_to(OBJ)),fps=12,loop=clip!='load',probe=probe,placements=placements))

# Source-specified customer/stool scale context uses original catalog placements.
canvas=Image.new('RGB',(640,704),(226,218,199));d=ImageDraw.Draw(canvas)
d.text((18,18),'Native sprite assembly: completed dish and customer scale',fill='#242932')
place(canvas,frame('hold','S',0),catalog,0,1)
place(canvas,published(lib['stool-wood'],'static','S'),lib['stool-wood'],2,1)
place(canvas,published(lib['customer-rosa'],'seated-wait','S'),lib['customer-rosa'],2,1)
canvas.save(OUT/'contexts/customer-scale.png')
repeated=Image.new('RGB',(640,640),(226,218,199));d=ImageDraw.Draw(repeated);d.text((18,18),'Native repeated registration at one-cell 128px pitch',fill='#242932')
for i,di in enumerate(DIRECTIONS):place(repeated,frame('idle',di,0),catalog,i,1,direction=di)
repeated.save(OUT/'sheets/repeated.png')

# Material and source-version audit receipts are hash-bound, copied opaquely.
resources=[]
for path in sorted((HERE/'resources').glob('*')):
 if path.is_file():resources.append(dict(path=str(path.relative_to(OBJ)),sha256=sha(path)))
if not (OUT/'browser-playback-qa.json').exists():
 print('Presentation assets prepared; browser QA receipt required before final manifest.');sys.exit(0)
audit=json.loads((OUT/'native-audit.json').read_text())
supplement=json.loads((OUT/'native-supplement.json').read_text())
food_audit=json.loads((OUT/'food-native-audit.json').read_text())
visible_audit=json.loads((OUT/'visible-projection-audit.json').read_text());assert visible_audit['allChecksPassed']
depth_audit=json.loads((OUT/'occlusion-native-audit.json').read_text());closure=json.loads((HERE/'portability-proof-round03/receipt.json').read_text())
assert audit['allChecksPassed'] and supplement['allChecksPassed'] and food_audit['allChecksPassed'] and depth_audit['allChecksPassed'] and closure['all20DecodedRGBAEqual']
assert audit['sourceProjectSHA256']==sha(HERE/'round-03.blend')==supplement['nativeSourceSHA256']
validation=dict(asset='chef-rowan',activeBrief='brief-v4-food-occlusion.json',round='round-03',nativeAudit='native-audit.json',
                nativeAuditSHA256=sha(OUT/'native-audit.json'),nativeSupplement='native-supplement.json',nativeSupplementSHA256=sha(OUT/'native-supplement.json'),foodNativeAudit='food-native-audit.json',foodNativeAuditSHA256=sha(OUT/'food-native-audit.json'),allTechnicalChecksPassed=audit['allChecksPassed'] and supplement['allChecksPassed'] and food_audit['allChecksPassed'],
                activeBriefSHA256=sha(OBJ/'brief-v4-food-occlusion.json'),criteriaSHA256=sha(OBJ/'reviews/criteria-v4-food-occlusion.json'),
                sourceProject='source/round-03.blend',sourceProjectSHA256=sha(HERE/'round-03.blend'),
                frameCount=len(records),atlasCount=len(atlas_records),allFramesRGBA384x640=True,alphaClipping=False,
                actualPlaybackFPS=12,playbackCount=len(timing),nonloopingLoad=True,
                browserPlaybackQA='browser-playback-qa.json',browserPlaybackQASHA256=sha(OUT/'browser-playback-qa.json'),
                capturePolicy='Untouched whole native frames; all packing/comparison logical-size scaling uniform only; no pixel warps or silhouette fitting',
                foodRepresentation='Exact approved canonical packed2D fullUV; not modeled3D sushi',
                dependencyReceipts=resources,frameRecords=records,atlases=atlas_records,playbacks=timing,contexts=context_records,
                depthOnlyAudit='candidates/round-03/occlusion-native-audit.json',depthOnlyAuditSHA256=sha(OUT/'occlusion-native-audit.json'),foodOcclusionPolicy=brief['foodOcclusionPolicy'],visibleProjectionAudit='candidates/round-03/visible-projection-audit.json',visibleProjectionAuditSHA256=sha(OUT/'visible-projection-audit.json'),hiddenFoodPixelAudit='candidates/round-03/hidden-food-pixel-audit.json',hiddenFoodPixelAuditSHA256=sha(OUT/'hidden-food-pixel-audit.json'),pixelEqualityNote=json.loads((OUT/'hidden-food-pixel-audit.json').read_text())['explanation'],closedPackageReceipt='source/portability-proof-round03/receipt.json',closedPackageReceiptSHA256=sha(HERE/'portability-proof-round03/receipt.json'),appearance='Pending independent judge review; technical pass is not aesthetic approval.')
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
(OUT/'frame-index.json').write_text(json.dumps(records,indent=2)+'\n')
(OUT/'playbacks/timing.json').write_text(json.dumps(timing,indent=2)+'\n')
(OUT/'contexts/assembly.json').write_text(json.dumps(context_records,indent=2)+'\n')
cards=[]
for t in timing:
 p=Path(t['path']).relative_to('candidates/round-03')
 cards.append(f'<figure><video controls muted playsinline preload="metadata" {"loop" if t["loop"] else ""} src="{html.escape(str(p))}"></video><figcaption>{t["clip"]} {t["direction"]} · 12 fps · {"loop" if t["loop"] else "nonlooping out-and-back"}</figcaption></figure>')
page='<!doctype html><meta charset="utf-8"><title>Rowan native round03</title><style>body{margin:24px;background:#343b44;color:#eee;font:16px system-ui}main{display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:12px}figure{margin:0}video{width:100%;max-height:480px;background:#565b62}img{max-width:100%}a{color:#6ee3e7}</style><h1>Rowan native round03</h1><p>Active brief v4-food-occlusion. Continuous native camera-ray law d(f)=.60-.15*max(0,-f)^2. Exact canonical salmon remains packed 2D. Appearance awaits independent review.</p><main>'+''.join(cards)+'</main><p><a href="sheets/comparison-registered.png">Registered comparison</a> · <a href="sheets/readability-light.png">Light</a> · <a href="sheets/readability-gray.png">Gray</a> · <a href="sheets/readability-dark.png">Dark</a> · <a href="native-audit.json">Native audit</a></p>'
(OUT/'preview.html').write_text(page)
delivery=dict(asset='chef-rowan',round='round-03',activeBrief='brief-v4-food-occlusion.json',approval='pending independent judge',
              nativeSource='source/round-03.blend',nativeSourceSHA256=sha(HERE/'round-03.blend'),
              recipe='source/round-03-recipe.py',recipeSettings='source/round-03-recipe.json',
              validation='candidates/round-03/validation.json',nativeAudit='candidates/round-03/native-audit.json',
              nativeSupplement='candidates/round-03/native-supplement.json',foodNativeAudit='candidates/round-03/food-native-audit.json',browserPlaybackQA='candidates/round-03/browser-playback-qa.json',
              frameIndex='candidates/round-03/frame-index.json',preview='candidates/round-03/preview.html',
              frameCount=192,atlasCount=16,fps=12,clips=[dict(id=c,frames=12,loop=c!='load') for c in CLIPS],
              atlases=atlas_records,foodDependency=brief['foodDependency'],resources=resources,
              notes='Source .blend saved/reopened and all frames rendered natively. Contexts are labeled independent native sprite assemblies. No production edits or self approval.')
(OBJ/'delivery-round03-draft.json').write_text(json.dumps(delivery,indent=2)+'\n')
packet_inputs=dict(activeBrief='brief-v4-food-occlusion.json',project='source/round-03.blend',validation='candidates/round-03/validation.json',
                   renders=[str(p.relative_to(OBJ)) for folder in ['frames','atlases','sheets','contexts'] for p in sorted((OUT/folder).glob('*.png'))],
                   resources=[str(p.relative_to(OBJ)) for folder in ['playbacks','contexts'] for p in sorted((OUT/folder).glob('*.mp4'))]+[r['path'] for r in resources]+['candidates/round-03/native-audit.json','candidates/round-03/native-supplement.json','candidates/round-03/frame-index.json','candidates/round-03/playbacks/timing.json','candidates/round-03/contexts/assembly.json','candidates/round-03/capture.log','candidates/round-03/preview.html','source/round-03-recipe.py','source/round-03-recipe.json','source/capture-round-03.py','source/assemble-round-03.py','source/supplement-round03-audit.py'])
(OUT/'packet-inputs.json').write_text(json.dumps(packet_inputs,indent=2)+'\n')
packet_inputs['resources'].extend(['candidates/round-03/food-native-audit.json','candidates/round-03/browser-playback-qa.json','source/food-round03-tech-check.py'])
(OUT/'packet-inputs.json').write_text(json.dumps(packet_inputs,indent=2)+'\n')
print('Packed',len(records),'native frames,',len(atlas_records),'atlases,',len(timing),'12fps playbacks and',len(context_records),'held/load neighbor contexts.')
