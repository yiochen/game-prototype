"""Preview composition and measurements only. Never edits published pixels."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,math,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-01'
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
def composite(im,bg='#f2f0e8'):return Image.alpha_composite(Image.new('RGBA',im.size,bg),im.convert('RGBA')).convert('RGB')
def label(draw,xy,s):draw.text(xy,s,font=font,fill='#263544')
directions=['N','E','S','W'];angles={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
sheet=Image.new('RGB',(304*4,414),'#f2f0e8');d=ImageDraw.Draw(sheet)
for i,di in enumerate(directions):
    im=Image.open(OUT/f'frames/static/{di}/000.png');sheet.paste(composite(im).crop((40,260,344,640)),(i*304,30));label(d,(i*304+12,6),di+' — native2x')
sheet.save(OUT/'four-view-sheet.png')
ledger=read(OUT/'consumer/capture-ledger.json')
assembly=Image.new('RGB',(448*2,510*4),'#f2f0e8');ad=ImageDraw.Draw(assembly)
native_independent=[];local=[];maskdir=OUT/'local-masks';maskdir.mkdir(exist_ok=True)
profile=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)]
def project(p,a):
    x,y,z=p;xx=x*math.cos(a)-y*math.sin(a);yy=x*math.sin(a)+y*math.cos(a);return (448+256*xx,752-256*yy-179.2*z)
def masks(di,native):
    allm={};a=angles[di]
    opaque=Image.fromarray((np.asarray(native)[:,:,3]==255).astype('uint8')*255).filter(ImageFilter.MinFilter(9))
    for port in ['W','N']:
        m=Image.new('L',native.size);dr=ImageDraw.Draw(m)
        for j in range(1,8):
            yz=[profile[j],profile[(j+1)%8]]
            if port=='W':points=[(x,w,z) for x,w,z in [(-.53,*yz[0]),(-.53,*yz[1]),(-.47,*yz[1]),(-.47,*yz[0])]]
            else:points=[(-w,y,z) for w,y,z in [(yz[0][0],.47,yz[0][1]),(yz[1][0],.47,yz[1][1]),(yz[1][0],.53,yz[1][1]),(yz[0][0],.53,yz[0][1])]]
            dr.polygon([project(p,a) for p in points],fill=255)
        m=ImageChops.darker(m,opaque);m.save(maskdir/f'{di}-{port}-native-interior.png');allm[port]=m
    return allm
all_masks={}
for row,di in enumerate(directions):
    native=Image.open(OUT/f'native/two-port-{di}.png').convert('RGBA')
    rec=next(r for r in ledger['modes'][0]['captures'] if r['direction']==di and r['size']==128 and r['phase']==0 and r['background']=='#f2f0e8')
    raw=Image.open(OUT/rec['raw']['path']).convert('RGBA');plan=rec['plan'];x=round((96-plan['x'])*plan['scale']);y=round((-56-plan['y'])*plan['scale']);ind=raw.crop((x,y,x+896,y+1216));ind.save(OUT/f'independent-two-port-{di}.png')
    for col,im in enumerate([native,ind]):
        assembly.paste(composite(im).crop((0,240,896,1152)).resize((448,456),Image.Resampling.LANCZOS),(col*448,row*510+34));label(ad,(col*448+12,row*510+7),f'{di} — '+('native combined' if col==0 else 'independent actual consumer raster'))
    n=np.asarray(native).astype(int);r=np.asarray(ind).astype(int);all_masks[di]=masks(di,native)
    for port,m in all_masks[di].items():
        pick=np.asarray(m)>0;diff=np.abs(n[:,:,:3]-r[:,:,:3])[pick]
        local.append({'direction':di,'port':port,'mask':f'local-masks/{di}-{port}-native-interior.png','samplePixels':int(pick.sum()),'independentAlphaMin':int(r[:,:,3][pick].min()),'independentInteriorAlphaLossPixels':int(((r[:,:,3]<255)&pick).sum()),'nativeIndependentRGBMax':int(diff.max()),'nativeIndependentRGBMean':float(diff.mean()),'note':'Raw comparison; finite-light placement and raster differences retained. No local defect waiver.'})
assembly.save(OUT/'native-independent-assembly.png')
# Each browser/background preview contains every all4/phase screenshot at logical
# size and the exact phone screenshot alongside. One fixed crop for all views.
previews={}
for mode in ledger['modes']:
    for bgindex,bg in enumerate(['#f2f0e8','#777b82','#17202b']):
        sh=Image.new('RGB',(4*588,4*488),'#e9e5dd');sd=ImageDraw.Draw(sh)
        for diindex,di in enumerate(directions):
            for phase in range(4):
                x=diindex*588;y=phase*488;label(sd,(x+8,y+5),f'{di} phase{phase} — 128 / 32')
                for size,dx in [(128,0),(32,460)]:
                    rec=next(r for r in mode['captures'] if r['direction']==di and r['size']==size and r['phase']==phase and r['background']==bg)
                    im=Image.open(OUT/rec['screenshot']['path']);crop=(0,120,448,568) if size==128 else (0,30,112,142);sh.paste(im.crop(crop),(x+dx,y+32))
        name=f'consumer-{mode["name"]}-bg{bgindex}.png';sh.save(OUT/name);previews[f'consumer-{mode["name"]}-bg{bgindex}']='candidates/round-01/'+name
# Actual CSS coverage: compare the same native interior neighborhoods between
# light and dark screenshots. An opaque interior is background-independent.
css=[]
for mode in ledger['modes']:
    for di in directions:
        for size in [128,32]:
            for phase in range(4):
                rs=[next(r for r in mode['captures'] if r['direction']==di and r['size']==size and r['phase']==phase and r['background']==bg) for bg in ['#f2f0e8','#777b82','#17202b']]
                imgs=[np.asarray(Image.open(OUT/r['screenshot']['path']).convert('RGB')).astype(int) for r in rs];s=size/128;shift=rs[0]['root']+rs[0]['pan']
                for port,mask in all_masks[di].items():
                    # Forward shift native mask in native pixels, then BOX reduce;
                    # retain only full-coverage pixels after CSS filtering.
                    shifted=mask.transform(mask.size,Image.Transform.AFFINE,(1,0,-shift*2,0,1,-shift*2),resample=Image.Resampling.BILINEAR)
                    reduced=shifted.resize((round(448*s),round(608*s)),Image.Resampling.BOX);pick=np.asarray(reduced)==255
                    diff=np.max(np.abs(imgs[0]-imgs[2]),axis=2);m=maskdir/f'{mode["name"]}-{di}-{port}-cell{size}-phase{phase}.png';reduced.save(m)
                    css.append({'mode':mode['name'],'direction':di,'port':port,'cell':size,'phase':phase,'root':rs[0]['root'],'pan':rs[0]['pan'],'mask':str(m.relative_to(OUT)),'pixels':int(pick.sum()),'backgroundDependentPixels':int(((diff>0)&pick).sum()),'maxLightDarkDifference':int(diff[pick].max()) if pick.any() else None,'actualCSS':rs[0]['css'],'screenshots':[r['screenshot'] for r in rs]})
write(OUT/'local-join-measurements.json',{'method':'Finite projected original eight-point section surface bands ±.03 units around both ports, intersected with eroded actual native alpha255 interior. Both ports and all4 facings. CSS masks retain only full BOX coverage after phase transform; three actual backgrounds retained.','nativeVsIndependent':local,'actualCSSBackgroundComparisons':css,'excluded':'Outer silhouette and alpha-antialiased native boundary; no full-cell or AABB opacity mask.','note':'RGB finite-light/raw-raster residuals are recorded separately from observed local alpha coverage. No actual source extent adjustment or pixel repair was performed.'})
replay=[]
for name in [*[f'native/static/{d}/000.png' for d in directions],*[f'native/two-port-{d}.png' for d in directions],*[f'canonical/static-{d}.png' for d in directions]]:
    p=OUT/name;q=OUT/'saved-source-replay'/name;aa=np.asarray(Image.open(p)).astype(int);bb=np.asarray(Image.open(q)).astype(int);delta=np.abs(aa-bb)
    replay.append({'path':name,'sourceReplay':'saved-source-replay/'+name,'sha256':sha(p),'replaySHA256':sha(q),'byteEqual':p.read_bytes()==q.read_bytes(),'decodedDifferentPixels':int(np.any(delta>0,axis=2).sum()),'maxDecodedChannelDifference':int(delta.max())})
write(OUT/'saved-source-replay-comparison.json',{'sourceSHA256':sha(BASE/'round-01.blend'),'comparisons':replay,'sourceReplayCommand':'blender -b --python source/reproduce-round-01.py -- --replay --out candidates/round-01/saved-source-replay'})
geometry=read(OUT/'geometry-audit.json');field=read(OUT/'native-field-proof.json');topology=read(OUT/'native-topology.json');captures=read(OUT/'capture-measurements.json')
asset=read(OBJ/'inputs/source-assetRecord.json');asset.update(scale=2,sourceScale=2,rootObject='reef-corner__root',sourceSHA256=sha(BASE/'round-01.blend'),artStyle={'revision':'warm-soft-reef-corner-round01','nativeEditable':True,'lighting':'Exact approved canonical reef-middle broad centered overhead and four equal fills','roughness':'canonical blue .64 / cyan .62; distinct coral native materials','specularIORLevel':.22})
write(OUT/'assetRecord.json',asset)
write(OUT/'rig.json',{'assetId':'reef-corner','fps':12,'static':True,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'actions':[]}},'armatures':[],'footprint':[1,1],'projection':'top-down-oblique-square-grid','groundRootObject':'reef-corner__root','sockets':{},'actionCount':0,'status':'native-static-round01-awaiting-independent-review','sourceSHA256':sha(BASE/'round-01.blend'),'sourceFiles':{'reproduce-round-01.py':sha(BASE/'reproduce-round-01.py')},'lighting':geometry['lighting']})
validation={'asset':'reef-corner','round':'round-01','status':'native evidence measured; independent visual verdict pending','sourceSHA256':sha(BASE/'round-01.blend'),'nativeValidation':'candidates/round-01/capture-measurements.json','views':captures['captureRecords'],'registeredCapture':read(OUT/'published-camera.json'),'geometry':'candidates/round-01/geometry-audit.json','topology':'candidates/round-01/native-topology.json','fieldProof':'candidates/round-01/native-field-proof.json','consumer':'candidates/round-01/consumer/capture-ledger.json','localJoinMeasurements':'candidates/round-01/local-join-measurements.json','replay':'candidates/round-01/saved-source-replay-comparison.json','lighting':'Canonical actual saved rig retained; same rig/color in every facing and assembly','measurements':{'fullCanonicalTriangles':len(field['triangleRecords']),'barycentricSamples':field['sampleCount'],'maxFieldNormalError':field['maxNormalizedNormalError'],'maxFieldAlbedoError':field['maxAlbedoError'],'actualMaterialResponseEqual':field['actualMaterialResponseEqual'],'actualRigEqual':field['actualRigEqual'],'coreNonTwoFaceEdges':len(topology['nonTwoFaceEdges']),'actualBottomArea':topology['actualBottomAreaSum'],'actualBounds':geometry['bounds'],'nativeReplayChangedPixels':sum(r['decodedDifferentPixels'] for r in replay),'actualBrowserModes':[{'name':m['name'],'version':m['version'],'captures':len(m['captures']),'errors':m['pageErrors']} for m in ledger['modes']],'nativeIndependentInteriorAlphaLossPixels':sum(r['independentInteriorAlphaLossPixels'] for r in local),'cssBackgroundDependentInteriorPixels':sum(r['backgroundDependentPixels'] for r in css)},'limits':['Canonical collars are copied whole; normalized field residual is ordinary native float representation (maximum recorded, no early custom-normal normalization).','The middle is the only approved family companion; no derivative/family/production approval is inferred.','Native finite-light RGB differences against independently rendered sprites remain raw and are measured by local neighborhood. Visual quality and seam assessment remain for the original independent judge.']}
write(OUT/'validation.json',validation)
delivery={'asset':'reef-corner','round':'round-01','project':'source/round-01.blend','recipeScript':'source/reproduce-round-01.py','validation':'candidates/round-01/validation.json','nativeRecords':{k:'candidates/round-01/'+v for k,v in {'camera':'published-camera.json','assetRecord':'assetRecord.json','rig':'rig.json'}.items()},'heroes':{d:f'candidates/round-01/frames/static/{d}/000.png' for d in directions},'previews':{'four-view-sheet':'candidates/round-01/four-view-sheet.png','repeated':'candidates/round-01/native-independent-assembly.png',**previews},'rawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-01/frames/static/{d}/000.png'} for d in directions],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-01/native/static/{d}/000.png'} for d in directions],'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-01/atlases/static-{d}.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]],'sha256':sha(OUT/f'atlases/static-{d}.png')} for d in directions],'resources':[],'resourcePathBase':'object folder','approval':'Pending root sealing and original independent judge; editor does not approve.'}
# Source closure excludes historical preflight files, which are outside source.
for p in sorted(BASE.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:delivery['resources'].append({'path':str(p.relative_to(OBJ)),'sha256':sha(p)})
write(OBJ/'delivery-round01-editor.json',delivery)
print(json.dumps(validation['measurements'],indent=2))
