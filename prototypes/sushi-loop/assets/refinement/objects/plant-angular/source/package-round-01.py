"""Pack native plant round 01 without altering a capture pixel.
Use the bundled Python runtime with Pillow and numpy.
"""
from pathlib import Path
import copy, hashlib, json, shutil, statistics
from PIL import Image, ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parents[5]
OUT=ROOT/'candidates/round-01'
NATIVE=json.loads((OUT/'native-validation.json').read_text())
CATALOG=json.loads((ROOT/'inputs/catalog-object.json').read_text())
assert NATIVE['nativeContractPassed']
assert len(NATIVE['renders'])==52
assert not (OUT/'delivery.json').exists(), 'Immutable package already exists'
DIRECTIONS=['S','E','N','W']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 Path(path).write_text(json.dumps(value,indent=2)+'\n')
def objrel(path):return str(Path(path).relative_to(ROOT))
def workrel(path):return str(Path(path).relative_to(WORKSPACE))
def matte(im,bg):
 out=Image.new('RGBA',im.size,bg+(255,));out.alpha_composite(im);return out.convert('RGB')

validation={'asset':'plant-angular','round':1,'nativeValidation':objrel(OUT/'native-validation.json'),
            'nativeValidationSHA256':sha(OUT/'native-validation.json'),
            'rawFrames':[],'atlases':[],'motion':{},'previews':[],
            'frame':[384,768],'logicalFrame':[192,384],'root':[192,576],'fps':12,
            'sourceScale':2,'footprint':[1,1],'allRawRGBA':True,'allClearBorder':True}
replacement=[]
def replacement_record(src,dest):
 replacement.append({'source':workrel(src),'destination':dest,'sha256':sha(src)})
registered=OUT/'registered'
for clip in CATALOG['clips']:
 cid=clip['id'];count=clip['frames']
 for direction in DIRECTIONS:
  layout=clip['directions'][direction]
  atlas=Image.new('RGBA',tuple(layout['atlasSize']),(0,0,0,0))
  raw=[];pixel_hashes=[]
  for index,rect in enumerate(layout['rects']):
   path=OUT/'raw'/('%s-%s'%(cid,direction))/('%03d.png'%index)
   im=Image.open(path);im.load()
   assert im.mode=='RGBA' and im.size==(384,768)
   pix=np.array(im);alpha=im.getchannel('A');bbox=alpha.getbbox()
   clear=bbox[0]>0 and bbox[1]>0 and bbox[2]<384 and bbox[3]<768
   assert clear
   info={'clip':cid,'direction':direction,'index':index,'path':objrel(path),'sha256':sha(path),
         'pixelSHA256':hashlib.sha256(im.tobytes()).hexdigest(),'size':list(im.size),'mode':im.mode,
         'alphaBBox':list(bbox),'clearBorder':clear,'nontransparentPixels':int(np.count_nonzero(pix[:,:,3])),
         'partiallyTransparentPixels':int(np.count_nonzero((pix[:,:,3]>0)&(pix[:,:,3]<255)))}
   validation['rawFrames'].append(info);pixel_hashes.append(info['pixelSHA256'])
   x,y,w,h=rect;assert (w,h)==im.size
   atlas.paste(im,(x,y))
   regpath=registered/('%s-%s'%(cid,direction))/'source-captures'/('%03d.png'%index)
   regpath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,regpath)
   raw.append({'path':'source-captures/'+regpath.name,'sha256':sha(regpath)})
   replacement_record(regpath,'prototypes/sushi-loop/assets/production/source/registered/plant-angular/%s-%s/source-captures/%03d.png'%(cid,direction,index))
  apath=OUT/'atlases'/('%s-%s.png'%(cid,direction));apath.parent.mkdir(parents=True,exist_ok=True)
  atlas.save(apath)
  reloaded=Image.open(apath)
  for index,(x,y,w,h) in enumerate(layout['rects']):
   frame=Image.open(OUT/'raw'/('%s-%s'%(cid,direction))/('%03d.png'%index))
   assert reloaded.crop((x,y,x+w,y+h)).tobytes()==frame.tobytes()
  atlasrec={'clip':cid,'direction':direction,'path':objrel(apath),'sha256':sha(apath),
            'size':list(atlas.size),'columns':layout['columns'],'rows':layout['rows'],'rects':layout['rects'],
            'frameCount':count,'uniquePixelFrames':len(set(pixel_hashes)),'losslessFramePacking':True}
  assert len(set(pixel_hashes))==count
  validation['atlases'].append(atlasrec)
  replacement_record(apath,'prototypes/sushi-loop/assets/production/'+layout['image'])
  camera=json.loads((ROOT/'inputs/source-camera.json').read_text())
  guide={'version':1,'kind':'rendered-3d-sheet','assetKind':'animation' if cid=='idle' else 'sprite',
         'size':list(atlas.size),'frame':[192,384],'anchor':[96,288],'cellSize':128,'captureScale':2,
         'gutter':0,'columns':layout['columns'],'rows':layout['rows'],
         'cells':[{'index':i,'rect':[x,y,x+w,y+h],'durationMs':1000/12} for i,(x,y,w,h) in enumerate(layout['rects'])],
         'groundAnchorAlignment':'center','projection':'top-down-oblique-square-grid','camera':camera['camera'],
         'occupiedCells':[[0,0]],'elevationPx':0,'sourceCaptures':raw,'sourceCaptureScale':2,
         'processing':'Direct native384x768 RGBA capture; lossless whole-frame atlas packing only',
         'clip':cid,'direction':direction,'fps':12,'loop':cid=='idle','static':cid=='static',
         'nativeSource':'source/blender/refinement/plant-angular/round-01.blend'}
  gp=registered/('%s-%s'%(cid,direction))/'guide.json';write(gp,guide)
  replacement_record(gp,'prototypes/sushi-loop/assets/production/source/registered/plant-angular/%s-%s/guide.json'%(cid,direction))

# Hero files are exact copies of the neutral native static captures.
for direction in DIRECTIONS:
 p=OUT/(direction+'.png');shutil.copyfile(OUT/'raw'/('static-'+direction)/'000.png',p)
 validation['previews'].append({'name':'hero-'+direction,'path':objrel(p),'sha256':sha(p),'nativePixels':True})

# Real twelve-frame playback, one consistent palette per facing and a neutral matte.
for direction in DIRECTIONS:
 images=[Image.open(OUT/'raw'/('idle-'+direction)/('%03d.png'%i)).convert('RGBA') for i in range(12)]
 rgb=[matte(im,(55,60,68)) for im in images]
 palette_sheet=Image.new('RGB',(384*4,768*3))
 for i,im in enumerate(rgb):palette_sheet.paste(im,((i%4)*384,(i//4)*768))
 palette=palette_sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 frames=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in rgb]
 gif=OUT/('idle-'+direction+'.gif')
 frames[0].save(gif,save_all=True,append_images=frames[1:],duration=[80,80,90]*4,loop=0,
                optimize=False,disposal=2)
 check=Image.open(gif);dur=[];gifhash=[]
 for i in range(check.n_frames):
  check.seek(i);dur.append(check.info['duration']);gifhash.append(hashlib.sha256(check.convert('RGB').tobytes()).hexdigest())
 assert check.n_frames==12 and len(set(gifhash))==12 and sum(dur)==1000
 validation['previews'].append({'name':'idle-'+direction,'path':objrel(gif),'sha256':sha(gif),
                               'frames':12,'uniqueFrames':12,'durationMs':sum(dur),'frameDurationMs':dur,
                               'averageFps':12,'background':'#373c44','sharedPalette':True})
 arrays=[np.asarray(im,dtype=np.float32)/255 for im in rgb]
 steps=[float(np.sqrt(np.mean((arrays[i]-arrays[(i+1)%12])**2))) for i in range(12)]
 validation['motion'][direction]={'uniqueNativePixelFrames':12,'adjacentPixelRMS':steps,
                                  'loopBoundaryRMS':steps[-1],'maximumAdjacentRMS':max(steps),
                                  'loopBoundaryToMaximumRatio':steps[-1]/max(steps)}

# Every idle frame is shown at exact logical192x384 size, fixed canvas registration.
CW,CH=196,404
sheet=Image.new('RGB',(12*CW,4*CH),(55,60,68));draw=ImageDraw.Draw(sheet)
for row,direction in enumerate(DIRECTIONS):
 for i in range(12):
  im=Image.open(OUT/'raw'/('idle-'+direction)/('%03d.png'%i)).convert('RGBA').resize((192,384),Image.Resampling.LANCZOS)
  sheet.paste(matte(im,(55,60,68)),(i*CW+2,row*CH+18))
  draw.text((i*CW+5,row*CH+4),'%s  %02d'%(direction,i),fill=(229,230,235))
sheetpath=OUT/'motion-sheet.png';sheet.save(sheetpath)
validation['previews'].append({'name':'motion-sheet','path':objrel(sheetpath),'sha256':sha(sheetpath),
                               'framesShown':48,'logicalFrameDisplay':[192,384]})

backgrounds=[(236,233,226),(126,126,126),(30,32,37)]
sheet=Image.new('RGB',(4*200,3*410),(126,126,126));draw=ImageDraw.Draw(sheet)
for row,bg in enumerate(backgrounds):
 for col,direction in enumerate(DIRECTIONS):
  im=Image.open(OUT/(direction+'.png')).convert('RGBA').resize((192,384),Image.Resampling.LANCZOS)
  sheet.paste(matte(im,bg),(col*200+4,row*410+20))
  draw.text((col*200+8,row*410+5),direction,fill=(255,255,255) if row else (40,40,40))
readpath=OUT/'readability-sheet.png';sheet.save(readpath)
validation['previews'].append({'name':'readability-sheet','path':objrel(readpath),'sha256':sha(readpath),
                               'backgrounds':['#ece9e2','#7e7e7e','#1e2025'],'logicalFrameDisplay':[192,384]})

# A complete per-object source record, ready for the coordinator's catalog promotion.
cat=copy.deepcopy(CATALOG)
cat['productionStage']='Native Blender · warm soft refinement · round01 awaiting review'
cat['source']['blend']='source/blender/refinement/plant-angular/round-01.blend'
cat['source']['modelScript']='source/blender/refinement/plant-angular/editor-round-01.py'
cat['source']['camera']='source/records/plant-angular/camera.json'
cat['source']['assetRecord']='source/records/plant-angular/asset.json'
cat['source']['rig']='source/records/plant-angular/rig.json'
cat['source']['rawFrames']=[{'image':'source/registered/plant-angular/%s-%s/source-captures/%03d.png'%(r['clip'],r['direction'],r['index']),
                            'sha256':r['sha256'],'clip':r['clip'],'direction':r['direction'],'index':r['index']} for r in validation['rawFrames']]
cat['source']['captureScale']=2
cat['source']['editableRefinement']={'blendSHA256':NATIVE['nativeSource']['sha256'],
                                    'recipeSHA256':NATIVE['nativeSource']['recipeSHA256'],
                                    'validation':'source/records/plant-angular/warm-refinement-validation.json'}
cat['artStyle']={'style':'Warm softly lit cartoon','revision':'plant-angular-warm-round01',
                 'lighting':'Axially symmetric world with vertical broad sun; no ground shadow',
                 'renderer':'Cycles','roughness':'native material-specific'}
cat['captureFingerprint']=hashlib.sha256(''.join(r['sha256'] for r in validation['rawFrames']).encode()).hexdigest()
catpath=OUT/'records/catalog-object.json';write(catpath,cat)
for name in ['camera','asset','rig']:
 replacement_record(OUT/'records'/(name+'.json'),'prototypes/sushi-loop/assets/production/source/records/plant-angular/'+name+'.json')
replacement_record(ROOT/'source/round-01.blend','prototypes/sushi-loop/assets/production/source/blender/refinement/plant-angular/round-01.blend')
replacement_record(ROOT/'source/editor-round-01.py','prototypes/sushi-loop/assets/production/source/blender/refinement/plant-angular/editor-round-01.py')
validation['captureCount']=len(validation['rawFrames'])
validation['atlasCount']=len(validation['atlases'])
validation['allRawHashesMatchNative']=all(r['sha256']==next(n['sha256'] for n in NATIVE['renders'] if n['path']==r['path']) for r in validation['rawFrames'])
validation['nativeMotion']=NATIVE['motion']
validation['nativeSource']=NATIVE['nativeSource']
validation['nativeCapture']=NATIVE['capture']
validation['geometryEnvelope']=NATIVE['geometryEnvelope']
validation['lighting']=NATIVE['lighting']
validation['packagingRecipe']={'path':objrel(__file__),'sha256':sha(__file__)}
validation['renderEfficiency']={'engine':'Cycles','samples':72,'frameCount':52,
                               'totalSeconds':sum(r['seconds'] for r in NATIVE['renders']),
                               'medianSecondsPerFrame':statistics.median(r['seconds'] for r in NATIVE['renders']),
                               'projectBytes':(ROOT/'source/round-01.blend').stat().st_size}
validation['contractPassed']=True
vp=OUT/'validation.json';write(vp,validation)
replacement_record(vp,'prototypes/sushi-loop/assets/production/source/records/plant-angular/warm-refinement-validation.json')
delivery={'assetId':'plant-angular','round':1,'status':'candidate-awaiting-independent-review',
          'editableSource':{'path':workrel(ROOT/'source/round-01.blend'),'sha256':sha(ROOT/'source/round-01.blend'),
                            'scene':NATIVE['nativeSource']['scene'],'rootObject':'plant-angular__root',
                            'recipe':workrel(ROOT/'source/editor-round-01.py'),
                            'rigGuide':workrel(OUT/'records/rig.json'),
                            'clips':'Assign the per-leaf Key actions matching static or idle in rig.json; frames1-12 idle,13 closure.'},
          'frame':[384,768],'logicalFrame':[192,384],'logicalRoot':[96,288],'exportRoot':[192,576],
          'sourceScale':2,'captureCount':52,'atlasCount':8,'validation':workrel(vp),'validationSHA256':sha(vp),
          'nativeValidation':workrel(OUT/'native-validation.json'),'nativeValidationSHA256':sha(OUT/'native-validation.json'),
          'catalogObjectReplacement':workrel(catpath),'catalogObjectSHA256':sha(catpath),
          'replacements':replacement,
          'reviewRenders':validation['previews'],
          'scope':'Only plant-angular; coordinator promotes catalog and later Godot after exact-byte approval.'}
write(OUT/'delivery.json',delivery)
print(json.dumps({'candidate':str(OUT),'frames':52,'atlases':8,'validationPassed':True,
                  'delivery':str(OUT/'delivery.json'),'renderEfficiency':validation['renderEfficiency']},indent=2))
