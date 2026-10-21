"""Build inspection previews/technical image evidence without editing native render pixels."""
from pathlib import Path
import argparse,json,hashlib,shutil
from PIL import Image,ImageDraw
parser=argparse.ArgumentParser();parser.add_argument('round');args=parser.parse_args()
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'candidates'/args.round
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
images={d:Image.open(OUT/(d+'.png')).convert('RGBA') for d in 'NESW'}
checks={}
for d,im in images.items():
 alpha=im.getchannel('A');box=alpha.getbbox()
 opaque=[px[:3] for px in im.getdata() if px[3]>=250]
 checks[d]={'size':list(im.size),'mode':'RGBA','alphaBounds':list(box),'transparentPixelCount':sum(a==0 for a in alpha.getdata()),'fullyOpaquePixelCount':len(opaque),'edgeAlphaMaximum':max(list(alpha.crop((0,0,384,1)).getdata())+list(alpha.crop((0,703,384,704)).getdata())+list(alpha.crop((0,0,1,704)).getdata())+list(alpha.crop((383,0,384,704)).getdata())),'pixelsWithAnyClippedRGBChannel':sum(max(p)==255 for p in opaque),'whiteClippedPixels':sum(min(p)==255 for p in opaque),'sha256':sha(OUT/(d+'.png'))}
 assert im.size==(384,704) and box and checks[d]['edgeAlphaMaximum']==0
 # Original layout is a single unchanged full-frame static atlas.
 atlas=OUT/'atlases'/('static-'+d+'.png');atlas.parent.mkdir(exist_ok=True)
 shutil.copyfile(OUT/(d+'.png'),atlas)
 assert sha(atlas)==checks[d]['sha256']

# Every complete native frame, followed by all four at logical runtime scale.
bg=(42,39,34,255)
sheet=Image.new('RGBA',(1536,746),bg);draw=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
 sheet.alpha_composite(images[d],(i*384,42));draw.text((i*384+188,15),d,fill=(240,222,192))
sheet.save(OUT/'four-view-sheet.png')
runtime=Image.new('RGBA',(768,380),bg);draw=ImageDraw.Draw(runtime)
logical={d:im.resize((192,352),Image.Resampling.LANCZOS) for d,im in images.items()}
for i,d in enumerate('NESW'):
 runtime.alpha_composite(logical[d],(i*192,28));draw.text((i*192+92,9),d,fill=(240,222,192))
runtime.save(OUT/'four-view-logical.png')

# Independently composited sprites at the registered 128px cell pitch.
repeat=Image.new('RGBA',(640,600),(67,73,62,255));draw=ImageDraw.Draw(repeat)
for y in range(4):
 for x in range(4):
  draw.rectangle((64+x*128,120+y*128,64+(x+1)*128,120+(y+1)*128),fill=((76,82,69,255) if (x+y)%2 else (72,78,66,255)))
for y in range(3):
 for x in range(4):
  d='NESW'[(x+y)%4];anchor=(128+x*128,185+y*128)
  repeat.alpha_composite(logical[d],(anchor[0]-96,anchor[1]-248))
draw.text((16,15),'Crate wood | logical runtime scale | 128px cell pitch',fill=(240,222,192))
repeat.save(OUT/'repeated.png')

validation=json.loads((OUT/'validation-native.json').read_text())
validation['imageEvidence']=checks
validation['checks'].update({'allPNGsRequiredSize':all(r['size']==[384,704] for r in checks.values()),'allSpritesClearOfFrameEdges':all(r['edgeAlphaMaximum']==0 for r in checks.values()),'allAtlasesExactNativeBytes':all(sha(OUT/'atlases'/('static-'+d+'.png'))==checks[d]['sha256'] for d in 'NESW')})
validation['previews']={f:{'sha256':sha(OUT/f),'size':list(Image.open(OUT/f).size),'purpose':('Unmodified full native frames' if f=='four-view-sheet.png' else 'Inspection-only alpha compositing/resizing; native exports unchanged')} for f in ('four-view-sheet.png','four-view-logical.png','repeated.png')}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
manifest={'asset':'crate-wood','status':'candidate-awaiting-independent-judge','candidate':args.round,'pipeline':'native-3d','source':{'blend':'source/'+args.round+'.blend','sha256':sha(BASE/'source'/(args.round+'.blend')),'reproductionScript':'source/'+args.round+'.py','reproductionScriptSha256':sha(BASE/'source'/(args.round+'.py'))},'validation':'candidates/'+args.round+'/validation.json','validationSha256':sha(OUT/'validation.json'),'previews':['candidates/'+args.round+'/'+f for f in ('four-view-sheet.png','four-view-logical.png','repeated.png')],'sprites':{},'proposedReplacementMetadata':{'id':'crate-wood','frameSize':[192,352],'root':[96,248],'sourceScale':2,'footprint':[1,1],'height':.925,'projection':'top-down-oblique-square-grid','clips':[{'id':'static','sourceClipId':'idle','frames':1,'fps':12,'static':True,'loop':False,'frameOrder':[0]}]},'approval':None,'finalPromotion':'Root coordinator copies exact approved bytes only after packet-bound independent approval.'}
for d in 'NESW':
 manifest['sprites'][d]={'path':'candidates/'+args.round+'/atlases/static-'+d+'.png','sha256':checks[d]['sha256'],'proposedProductionPath':'sprites/crate-wood/static-'+d+'.png','atlasSize':[384,704],'columns':1,'rows':1,'rects':[[0,0,384,704]]}
(OUT/'delivery.json').write_text(json.dumps(manifest,indent=2)+'\n')
(BASE/'delivery.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'round':args.round,'checks':validation['checks'],'imageEvidence':checks,'delivery':str(BASE/'delivery.json')},indent=2))
