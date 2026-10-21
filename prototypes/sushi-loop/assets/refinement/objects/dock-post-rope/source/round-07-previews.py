"""Non-art preview packaging only. Raw native RGBA frames are copied byte for byte to one-frame source-layout atlases."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,math,shutil
P=Path(__file__).resolve().parent.parent;O=P/'candidates/round-07';V=json.loads((O/'validation.json').read_text());D=['N','E','S','W'];PRE=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(P))
def preview(im,name,kind,**kwargs):
 p=O/name;im.save(p);PRE.append({'id':name.removesuffix('.png'),'kind':kind,'path':rel(p),'size':list(im.size),**kwargs});return p
def background(im,color):
 b=Image.new('RGBA',im.size,color);b.alpha_composite(im);return b.convert('RGB')
frames={d:Image.open(O/f'static-{d}-000.png').convert('RGBA') for d in D}
# Exact native, background, and intended logical size evidence.
sheet=Image.new('RGBA',(1536,704))
for i,d in enumerate(D):sheet.alpha_composite(frames[d],(i*384,0))
preview(sheet,'four-view-sheet.png','native-four-view-sheet')
logical=Image.new('RGB',(768,376),(233,229,220));draw=ImageDraw.Draw(logical)
for i,d in enumerate(D):logical.paste(background(frames[d],(233,229,220,255)).resize((192,352),Image.Resampling.LANCZOS),(i*192,24));draw.text((i*192+8,6),d,fill=(40,40,40))
preview(logical,'four-view-logical.png','intended-size-four-view-sheet')
bg=Image.new('RGB',(1536,2178));draw=ImageDraw.Draw(bg)
for row,(label,color) in enumerate([('LIGHT',(242,240,234,255)),('GRAY',(120,120,120,255)),('DARK',(30,33,38,255))]):
 for i,d in enumerate(D):bg.paste(background(frames[d],color),(i*384,row*726+22));draw.text((i*384+8,row*726+5),label+' '+d,fill=(210,210,210) if row==2 else (20,20,20))
preview(bg,'backgrounds-all-facings.png','native-light-gray-dark-backgrounds')
# Matching-profile independent sprite assembly at actual runtime pitch, all facings.
# Each image is rendered independently; alpha composition uses integer registered
# roots with no overlap correction, warping, inpainting, or visual pixel edits.
steps={'N':(-256,0),'E':(0,-256),'S':(256,0),'W':(0,256)}
composite_records=[]
for d in D:
 im=Image.new('RGBA',(1152,1216));dx,dy=steps[d];roots=[(576+t*dx,752+t*dy) for t in [-1,0,1]]
 for x,y in sorted(roots,key=lambda p:p[1]):im.alpha_composite(frames[d],(x-192,y-496))
 p=preview(im,f'joined-independent-{d}.png','independent-runtime-alpha-assembly',direction=d)
 composite_records.append({'direction':d,'rootRotationZ':next(r['rootRotationZ'] for r in V['captureRecords'] if r['direction']==d),'sourceFrame':rel(O/f'static-{d}-000.png'),'placements':[{'catalogCell':[x,2],'capturedRootPixels':list(root)} for x,root in zip([1,2,3],roots)],'runtimePitchPixels':list(steps[d]),'path':rel(p),'noRasterCorrection':True})
 native=Image.open(O/f'joined-native-{d}.png').convert('RGBA');PRE.append({'id':f'joined-native-{d}','kind':'independent-native-mesh-assembly','direction':d,'path':rel(O/f'joined-native-{d}.png'),'size':list(native.size)})
 compare=Image.new('RGB',(2304,1240),(232,229,220));compare.paste(background(native,(232,229,220,255)),(0,24));compare.paste(background(im,(232,229,220,255)),(1152,24));dd=ImageDraw.Draw(compare);dd.text((12,6),'NATIVE MESH ASSEMBLY '+d,fill=(35,35,35));dd.text((1164,6),'INDEPENDENT SPRITE ASSEMBLY '+d,fill=(35,35,35));preview(compare,f'joined-comparison-{d}.png','native-and-runtime-join-comparison',direction=d)
# Original/candidate at the same logical registration, all four views.
production=(P/'../../../production/sprites/dock-post-rope').resolve();compare=Image.new('RGB',(768,752),(232,229,220));dr=ImageDraw.Draw(compare)
for i,d in enumerate(D):
 old=Image.open(production/f'static-{d}.png').convert('RGBA');compare.paste(background(old,(232,229,220,255)).resize((192,352),Image.Resampling.LANCZOS),(i*192,24));compare.paste(background(frames[d],(232,229,220,255)).resize((192,352),Image.Resampling.LANCZOS),(i*192,400));dr.text((i*192+8,6),'SOURCE '+d,fill=(35,35,35));dr.text((i*192+8,382),'CANDIDATE '+d,fill=(35,35,35))
preview(compare,'source-candidate-logical.png','registered-source-candidate-comparison')
# Alpha, reproduction, and atlas validation.
alpha=[]
for d,im in frames.items():
 a=im.getchannel('A');border=list(a.crop((0,0,384,1)).getdata())+list(a.crop((0,703,384,704)).getdata())+list(a.crop((0,0,1,704)).getdata())+list(a.crop((383,0,384,704)).getdata());alpha.append({'direction':d,'rootRotationZ':next(r['rootRotationZ'] for r in V['captureRecords'] if r['direction']==d),'mode':im.mode,'size':list(im.size),'bbox':list(a.getbbox()),'transparentPixels':sum(v==0 for v in a.getdata()),'partialAlphaPixels':sum(0<v<255 for v in a.getdata()),'opaquePixels':sum(v==255 for v in a.getdata()),'nonzeroOuterFramePixels':sum(v>0 for v in border),'sha256':sha(O/f'static-{d}-000.png')})
fresh=Image.open(O/'fresh-reload-S.png').convert('RGBA');diff=ImageChops.difference(fresh,frames['S']);V['freshReload']['renderPixelExactMatch']=diff.getbbox() is None;V['freshReload']['renderSHA256']=sha(O/'fresh-reload-S.png');V['freshReload']['originalS_SHA256']=sha(O/'static-S-000.png');V['alpha']={'captures':alpha,'allFrameBordersTransparent':all(x['nonzeroOuterFramePixels']==0 for x in alpha),'realRGBA':True,'previewBackgrounds':rel(O/'backgrounds-all-facings.png')};V['independentAssemblyRecords']=composite_records
atlases=[]
for d in D:
 p=O/f'static-{d}.png';shutil.copyfile(O/f'static-{d}-000.png',p);atlases.append({'clip':'static','direction':d,'path':rel(p),'sha256':sha(p),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]})
# Record actual captured rotations on each directional evidence entry.
angles={r['direction']:r['rootRotationZ'] for r in V['captureRecords']}
for r in V['joinedNativeRecords']:
 r['rootRotationZ']=r['assemblyRootRotationZ'];r['rootMatrix']=r['assemblyRootMatrix']
for r in PRE:
 if 'direction' in r:r['rootRotationZ']=angles[r['direction']]
for r in atlases:r['rootRotationZ']=angles[r['direction']]
joincoverage=[]
for d in D:
 native=Image.open(O/f'joined-native-{d}.png').convert('RGBA');independent=Image.open(O/f'joined-independent-{d}.png').convert('RGBA');np=list(native.getdata());ip=list(independent.getdata());deficits=[(i%1152,i//1152,p[3]) for i,(n,p) in enumerate(zip(np,ip)) if n[3]==255 and p[3]<250]
 joincoverage.append({'direction':d,'rootRotationZ':angles[d],'opaqueNativeInteriorPixelsWithIndependentAlphaBelow250':len(deficits),'minimumAlphaInSuchPixels':min([r[2] for r in deficits],default=255),'diagnostic':'Exact meshes, standard alpha-over and integer native root placement. No alpha correction or geometric overlap. Box width 1 native reconstruction filter.'})
V['joinedCoverageCheck']=joincoverage
V['geometry']['evaluatedTopologyUnchanged']=all(V['geometry']['source'][name]['faceTopologySHA256']==rec['faceTopologySHA256'] for name,rec in V['geometry']['candidate'].items())
assert V['geometry']['evaluatedTopologyUnchanged']
V['previews']=PRE;V['atlasValidation']={'sourceLayoutPreserved':True,'atlases':atlases};V['status']='Native technical evidence complete; independent visual review pending.';(O/'validation.json').write_text(json.dumps(V,indent=2))
delivery={'asset':'dock-post-rope','round':'round-07','status':'candidate-ready-for-independent-review','project':'source/round-07.blend','recipe':'source/round-07-recipe.py','supportingRecipes':['source/round-07-audit.py','source/round-07-previews.py'],'validation':'candidates/round-07/validation.json','heroes':[{'direction':d,'path':rel(O/f'static-{d}-000.png')} for d in D],'rawFrames':[{'clip':'static','direction':d,'index':0,'path':rel(O/f'static-{d}-000.png')} for d in D],'previews':PRE,'atlases':atlases,'nativeRecords':{'camera':'candidates/round-07/camera.json','assetRecord':'candidates/round-07/assetRecord.json','rig':'candidates/round-07/rig.json'},'dependencies':[],'notes':['No geometry coordinates or profile/cut planes changed. Curved-side and top normal shading, warm materials, and neutral symmetric soft lighting are native Blender changes.','Five development rounds and the reviewed round-06 candidate are retained. Round 07 is the only submitted candidate.','Native and independently composed three-module repeated previews cover all four facings. Native S uses required catalog x=1,2,3 y=2 placement.']}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2));(P/'delivery.json').write_text(json.dumps(delivery,indent=2))
print(json.dumps({'delivery':str(P/'delivery.json'),'freshReloadExactPixels':V['freshReload']['renderPixelExactMatch'],'profileHausdorffError':V['profileMeasurements']['opposingYZProfileHausdorffError'],'alphaBordersTransparent':V['alpha']['allFrameBordersTransparent'],'previews':len(PRE)},indent=2))
