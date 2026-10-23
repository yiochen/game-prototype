from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,hashlib,shutil,numpy as np
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-04';font='/System/Library/Fonts/Supplemental/Arial.ttf'
def f(sz):
 try:return ImageFont.truetype(font,sz)
 except:return ImageFont.load_default()
def label(img,text,name):
 c=Image.new('RGBA',(img.width,img.height+64),'#f1e9db');c.alpha_composite(img,(0,64));d=ImageDraw.Draw(c);d.text((24,16),text,font=f(27),fill='#362d26');c.save(R/name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw=R/'static-S-000.png';hero=Image.open(raw).convert('RGBA');wall=Image.open(R/'wall-context-S.png').convert('RGBA');native=Image.open(R/'native-joined-raw.png').convert('RGBA');reopened=Image.open(R/'reopened-S.png').convert('RGBA')
shutil.copyfile(raw,R/'static-S.png')
# Pixel-exact registered export assembly; no image fit, warp, recolor or painted seam treatment.
a=Image.new('RGBA',(4416,1344))
placements=[]
for tile in [0,1,2,7,8,9,10]:a.alpha_composite(wall,(tile*384,0));placements.append({'asset':'matching-wall-context-only','tileX':tile,'paste':[tile*384,0],'root':[96+(tile+.5)*384,1248]})
a.alpha_composite(hero,(3*384,0));placements.append({'asset':'backdrop-entrance','tileX':3,'paste':[1152,0],'root':[2016,1248]});a.save(R/'independent-assembled-raw.png')
label(a,'S native sprite assembly: entrance + matching wall context (wall requires its own fresh-pair approval)','independent-assembled.png')
label(native,'S native connected facade: entrance + matching wall context (context only, pending separate wall approval)','native-joined.png')
# The historical four-view-sheet slot is explicitly a one-facing sheet for this fixed facade.
small=hero.resize((576,448),Image.Resampling.LANCZOS);sheet=Image.new('RGBA',(1728,496),'#e7e0d2');d=ImageDraw.Draw(sheet)
for i,(bg,lab) in enumerate([('#f6f2e9','S on light'),('#888888','S on gray'),('#192331','S on dark')]):
 panel=Image.new('RGBA',(576,448),bg);panel.alpha_composite(small);sheet.alpha_composite(panel,(i*576,48));d.text((i*576+16,13),lab+' · 576×448',font=f(20),fill='#302820')
sheet.save(R/'four-view-sheet.png');sheet.save(R/'background-sheet.png')
preview=Image.new('RGBA',(1472,488),'#e7e0d2');t=Image.new('RGBA',a.size,'#24303d');t.alpha_composite(a);preview.alpha_composite(t.resize((1472,448),Image.Resampling.LANCZOS),(0,40));ImageDraw.Draw(preview).text((16,11),'S: 3 walls + 4-tile entrance + 4 walls · matching wall context only',font=f(20),fill='#302820');preview.save(R/'repeated.png')
# Join strips retain native pixel scale. They are diagnostics only.
strips=Image.new('RGBA',(768,1408),'#f1e9db');d=ImageDraw.Draw(strips)
for i,(x,lab) in enumerate([(1248,'Left entrance join'),(2784,'Right entrance join')]):
 crop=a.crop((x-192,0,x+192,1344));strips.alpha_composite(crop,(i*384,64));d.text((i*384+10,19),lab,font=f(22),fill='#362d26')
strips.save(R/'entrance-join-strips.png')
val=json.loads((R/'validation.json').read_text());ar=np.asarray(hero);al=ar[:,:,3];ys,xs=np.where(al>0)
val['rasterAudit']={'mode':hero.mode,'nativeSize':list(hero.size),'alphaBoundsExclusive':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'transparentGutters':bool(not al[0].any() and not al[-1].any() and not al[:,0].any() and not al[:,-1].any()),'rgbaSha256':sha(raw),'reopenedRenderSha256':sha(R/'reopened-S.png'),'reopenedPixelMaxDifference':int(np.abs(ar.astype(int)-np.asarray(reopened).astype(int)).max()),'reopenedPixelMeanDifference':float(np.abs(ar.astype(int)-np.asarray(reopened).astype(int)).mean()),'atlasEqualsRaw':sha(R/'static-S.png')==sha(raw)}
aa=np.asarray(a);na=np.asarray(native);mask=(aa[:,:,3]>250)&(na[:,:,3]>250)
val['independentAssembly']={'path':'candidates/round-04/independent-assembled-raw.png','tilePitchNative':384,'tilePitchLogical':128,'frame':[4416,1344],'placements':placements,'wallStatus':'matching context only, not wall production approval','nativeConnectedComparison':{'meanAbsoluteRGBAOnOpaque':float(np.abs(aa.astype(int)-na.astype(int))[mask].mean()),'note':'Connected ray tracing can differ at geometry contacts from independent alpha-compositing; actual previews are supplied for visual join review.'},'seamAlphaSamples':{str(x):{'wallBodyRow900':aa[900,x-1:x+2,3].tolist(),'baseboardRow1200':aa[1200,x-1:x+2,3].tolist(),'roofRow350':aa[350,x-1:x+2,3].tolist()} for x in [480,864,1248,2784,3168,3552,3936]}}
val['wallFieldPixelSamples']={'contextRow900':{str(x):list(wall.getpixel((x,900))) for x in [100,192,288,384,475]},'entranceRow900':{str(x):list(hero.getpixel((x,900))) for x in [100,160,1568,1625]},'note':'Flat horizontal wall samples quantify absence of a global module-width light ramp; lantern and jamb contact regions are not sampled.'}
(R/'validation.json').write_text(json.dumps(val,indent=2))
project=P/'source/round-04.blend'
shutil.copyfile(project,P/'source/round-04-family-context.blend')
family=json.loads((P/'source/family-context.json').read_text());family['nativeLibrary']='round-04-family-context.blend';family['recipe']='round-04-recipe.json';family['protectedJoinShading']='Shared profile material variants suppress bevel shading at module end planes. Append identical material variants for wall context continuity.';family['wallCapture']={'nativeFrame':[576,1344],'logicalFrame':[192,448],'logicalRoot':[96,416],'sourceScale':3,'orthoScale':1.5,'shiftY':val['wallContextCapture']['camera']['shift'][1],'worldMatrix':val['wallContextCapture']['camera']['worldMatrix']};(P/'source/round-04-family-context.json').write_text(json.dumps(family,indent=2))
delivery={'schemaVersion':1,'asset':'backdrop-entrance','round':'round-04','project':'source/round-04.blend','recipe':'source/round-04-recipe.json','recipeScript':'source/build_round04.py','validation':'candidates/round-04/validation.json','heroes':{'S':'candidates/round-04/static-S-000.png'},'rawFrames':[{'clip':'static','direction':'S','index':0,'path':'candidates/round-04/static-S-000.png'}],'previews':{'four-view-sheet':'candidates/round-04/four-view-sheet.png','repeated':'candidates/round-04/repeated.png','background-sheet':'candidates/round-04/background-sheet.png','native-joined':'candidates/round-04/native-joined.png','independent-assembled':'candidates/round-04/independent-assembled.png','entrance-join-strips':'candidates/round-04/entrance-join-strips.png'},'atlases':[{'clip':'static','direction':'S','path':'candidates/round-04/static-S.png','sha256':sha(R/'static-S.png'),'columns':1,'rows':1,'size':[1728,1344],'rects':[[0,0,1728,1344]]}],'nativeRecords':{'camera':'candidates/round-04/native-records/camera.json','assetRecord':'candidates/round-04/native-records/asset-record.json','rig':'candidates/round-04/native-records/rig.json'},'resources':['source/build_round04.py','source/round-04-recipe.json','source/capture_validate_round04.py','source/render_wall_context_round04.py','source/audit_reopened_round04.py','source/assemble_delivery_round04.py','source/native-baseline.json','source/round-04-family-context.blend','source/round-04-family-context.json','source/round-04-join-context.blend','candidates/round-04/native-joined-raw.png','candidates/round-04/independent-assembled-raw.png','candidates/round-04/wall-context-S.png','candidates/round-04/reopened-S.png'],'notes':['Static S only. The four-view-sheet name is a legacy preview slot holding S on three backgrounds, without invented directions.','Original S0 phase, 35-degree camera, square pixels, sourceScale3 and contact anchor are preserved. Native root origin is explicitly distinguished from front-contact registration.','Matching wall native context is supplied only for join QA and a reusable technical family contract. Wall production requires its own fresh editor and judge.','Unchanged protected source geometry and matrices; no added floor geometry, walls decoration, or ground object.']}
(P/'delivery.json').write_text(json.dumps(delivery,indent=2))
print(json.dumps({'delivery':str(P/'delivery.json'),'checks':val['checks'],'protected':val['protectedJoinPlanes'],'raster':val['rasterAudit'],'samples':val['wallFieldPixelSamples'],'seams':val['independentAssembly']['seamAlphaSamples']},indent=2))
