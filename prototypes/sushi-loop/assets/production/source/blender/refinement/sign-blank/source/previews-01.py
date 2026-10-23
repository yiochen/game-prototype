from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib,shutil
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(im,name):im.save(O/name)
def panel(im,bg,size=None):
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 out=Image.new('RGBA',im.size,bg);out.alpha_composite(im);return out.convert('RGB')
def label(draw,xy,txt):draw.text(xy,txt,fill='#454244')
im=Image.open(O/'static-S.png').convert('RGBA');original=Image.open(P/'inputs/original.png').convert('RGBA')
# Exact atlas/raw bytes. No image transformation is used for runtime captures.
raw=O/'frames/static-S/000.png';raw.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/'static-S.png',raw)
# One S-facing view in the historically named four-view-sheet.
sheet=Image.new('RGB',(408,748),'#ddd9d3');d=ImageDraw.Draw(sheet);label(d,(14,12),'S | single player-facing native view | 384 x 704');sheet.paste(panel(im,'#dfddd7'),(12,32));d.line((198,544,210,544),fill='#458985');d.line((204,538,204,550),fill='#458985');label(d,(215,540),'root');save(sheet,'four-view-sheet.png')
# Background edges at logical size and native pixels; preview-only compositing.
backgrounds=[('#f5f1e8','Light'),('#868481','Gray'),('#292e35','Dark')]
comparison=Image.new('RGB',(1184,820),'#e4e0da');d=ImageDraw.Draw(comparison);label(d,(16,10),'Registered native S on backgrounds | 192 x 352 logical use size above; native-pixel detail below')
box=(60,380,324,630)
for col,(bg,title) in enumerate(backgrounds):
 x=16+col*392;label(d,(x,34),title+' / logical size')
 comparison.paste(panel(im,bg,(192,352)),(x+88,54))
 label(d,(x,422),'Same native frame / enlarged detail')
 comparison.paste(panel(im.crop(box),bg).resize((370,350),Image.Resampling.NEAREST),(x,446))
save(comparison,'backgrounds.png')
# Side-by-side original and candidate, identically cropped only in preview.
comp=Image.new('RGB',(1080,558),'#dfd9d0');d=ImageDraw.Draw(comp)
for i,(img,txt) in enumerate([(original,'Original'),(im,'Round 01 native')]):
 label(d,(i*540+16,12),txt+' | same registration crop')
 comp.paste(panel(img.crop(box),'#dfd9d0').resize((528,500),Image.Resampling.NEAREST),(i*540+6,42))
save(comp,'comparison.png')
# Registered runtime assembly: fixed cell pitch128, sourceScale2, common tile root.
dep=O/'preview-dependencies';dep.mkdir(exist_ok=True)
for name,rel in [('floor','../../../production/sprites/floor-cream/static-S.png'),('plant','../../../production/sprites/plant-angular/static-S.png')]:shutil.copyfile(P/rel,dep/(name+'.png'))
floor=Image.open(dep/'floor.png').convert('RGBA').resize((128,128),Image.Resampling.LANCZOS)
plant=Image.open(dep/'plant.png').convert('RGBA').resize((192,384),Image.Resampling.LANCZOS)
sign=im.resize((192,352),Image.Resampling.LANCZOS)
rep=Image.new('RGBA',(768,760),'#cfc6b7')
def at(img,root,anchor):rep.alpha_composite(img,(round(root[0]-anchor[0]),round(root[1]-anchor[1])))
roots={(x,y):(256+x*128,280+y*128) for y in range(3) for x in range(3)}
for root in roots.values():at(floor,root,(64,64))
# Same plant tile on left, then same object repeated at two registered foreground placements.
for cell in [(0,1),(1,1),(2,1)]:at(plant,roots[cell],(96,288))
for cell in [(0,1),(1,1),(2,1)]:at(sign,roots[cell],(96,256))
d=ImageDraw.Draw(rep);label(d,(18,16),'Registered 3 x 3 patch | 128 px logical cell pitch')
label(d,(18,36),'Plant and S sign share each highlighted tile; sign uses foreground pass')
label(d,(18,716),'All frames composed at declared roots/sourceScale. No sprite fitting or directional ground shadow.')
save(rep.convert('RGB'),'repeated.png')
# One transparent native frame audit.
a=im.getchannel('A');bb=a.getbbox();pix=list(a.getdata());alpha={'size':list(im.size),'alphaBoundingBox':list(bb),'fullyTransparentPixels':sum(v==0 for v in pix),'partialAlphaPixels':sum(0<v<255 for v in pix),'opaquePixels':sum(v==255 for v in pix),'allOuterBordersTransparent':all(a.getpixel((x,y))==0 for x in range(im.width) for y in [0,im.height-1]) and all(a.getpixel((x,y))==0 for y in range(im.height) for x in [0,im.width-1]),'boundsMarginPixels':[bb[0],bb[1],im.width-bb[2],im.height-bb[3]],'nativeFrameSha256':sha(O/'static-S.png'),'rawFrameSha256':sha(raw)}
(O/'alpha-validation.json').write_text(json.dumps(alpha,indent=2))
v=json.loads((O/'validation.json').read_text());reopen=json.loads((O/'reopened-validation.json').read_text());v['alpha']=alpha;v['reopenedSource']=reopen
other=Image.open(O/'reopened-S.png').convert('RGBA');deltas=[abs(a-b) for p1,p2 in zip(im.getdata(),other.getdata()) for a,b in zip(p1,p2)]
reopen['pixelComparison']={'maximumChannelDifference8bit':max(deltas),'meanAbsoluteChannelDifference8bit':sum(deltas)/len(deltas),'changedChannelValues':sum(d>0 for d in deltas),'alphaIdentical':im.getchannel('A').tobytes()==other.getchannel('A').tobytes(),'note':'PNG file hashes differ because timestamp/render-time metadata changes on reopening; native RGBA comparison is measured separately. GPU render quantization can differ by one 8-bit value.'}
v['checks'].pop('reopenedRenderBytesIdentical',None)
v['checks'].update(reopenedSourceUnchanged=reopen['projectUnchanged'],reopenedRGBWithinOneQuantizationStep=max(deltas)<=1,reopenedAlphaIdentical=reopen['pixelComparison']['alphaIdentical'],reopenedDatablocksLocal=reopen['allDatablocksLocal'],outerBordersTransparent=alpha['allOuterBordersTransparent'])
(O/'reopened-validation.json').write_text(json.dumps(reopen,indent=2))
v['previewEvidence']={'sheetPolicy':'historically named four-view-sheet contains only the one required player-facing S view','compositionMethod':'Pillow alpha compositing of exact native files for inspection only; scaled uniformly by registered sourceScale 2 to logical use size','runtimeCellPitch':128,'plantRoot':[96,288],'signRoot':[96,256],'floorRoot':[64,64],'sharedTileDrawOrder':['floor','plant-angular','sign-blank foreground'],'dependencies':[{'path':str(p.relative_to(P)),'sha256':sha(p)} for p in sorted(dep.glob('*.png'))],'files':[{'name':n,'path':str((O/n).relative_to(P)),'sha256':sha(O/n)} for n in ['four-view-sheet.png','backgrounds.png','comparison.png','repeated.png']]}
(O/'validation.json').write_text(json.dumps(v,indent=2))
delivery={'asset':'sign-blank','round':'round-01','pipeline':'native-3d','project':'source/round-01.blend','recipe':'source/round-01.py','validation':'candidates/round-01/validation.json','heroes':{'S':'candidates/round-01/static-S.png'},'rawFrames':[{'clip':'static','direction':'S','index':0,'path':'candidates/round-01/frames/static-S/000.png'}],'previews':{'four-view-sheet':'candidates/round-01/four-view-sheet.png','repeated':'candidates/round-01/repeated.png','backgrounds':'candidates/round-01/backgrounds.png','comparison':'candidates/round-01/comparison.png'},'atlases':[{'clip':'static','direction':'S','path':'candidates/round-01/static-S.png','sha256':sha(O/'static-S.png'),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]}],'nativeRecords':{'camera':'candidates/round-01/camera.json','assetRecord':'candidates/round-01/asset.json','rig':'candidates/round-01/rig.json'},'resources':{'originalSource':'source/original-library.blend','reopenRecipe':'source/reopen-01.py','previewRecipe':'source/previews-01.py','reopenedValidation':'candidates/round-01/reopened-validation.json','alphaValidation':'candidates/round-01/alpha-validation.json','floorPreviewDependency':'candidates/round-01/preview-dependencies/floor.png','plantPreviewDependency':'candidates/round-01/preview-dependencies/plant.png'}}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2));(P/'delivery.json').write_text(json.dumps(delivery,indent=2))
print('checks',v['checks']);print('alpha',alpha)
