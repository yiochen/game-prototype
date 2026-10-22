"""Assemble exact native bytes into original-layout static atlases and labeled evidence.
Sprite bytes are never recolored, warped or repaired. Resizing occurs in preview sheets only.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,shutil,math
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-02';SRC=BASE/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return str(p.relative_to(BASE))
DIRS='NESW';size=(384,704)
for kind in ['frames','atlases','previews']: (OUT/kind).mkdir(exist_ok=True)
for d in DIRS:
 raw=OUT/'raw'/f'static-{d}'/'000.png'
 for kind in ['frames','atlases']:shutil.copyfile(raw,OUT/kind/f'static-{d}.png')
imgs={d:Image.open(OUT/'frames'/f'static-{d}.png').convert('RGBA') for d in DIRS}
def sheet(scale,bg):
 w,h=[round(x*scale) for x in size];im=Image.new('RGB',(w*4,h+30),bg);dr=ImageDraw.Draw(im)
 for i,d in enumerate(DIRS):im.paste(imgs[d].resize((w,h),Image.Resampling.LANCZOS),(w*i,30),imgs[d].resize((w,h),Image.Resampling.LANCZOS));dr.text((w*i+10,9),d,fill=(240,244,250) if sum(bg)<420 else (20,25,30))
 return im
sheet(1,(34,40,50)).save(OUT/'previews/four-view-sheet.png');sheet(.5,(34,40,50)).save(OUT/'previews/logical-four-view-sheet.png')
w,h=192,352;im=Image.new('RGB',(w*4,h*3+90));dr=ImageDraw.Draw(im)
for j,(name,c) in enumerate([('Light',(239,239,233)),('Gray',(116,122,130)),('Dark',(15,24,37))]):
 dr.rectangle((0,j*(h+30),w*4,(j+1)*(h+30)),fill=c)
 for i,d in enumerate(DIRS):
  im.paste(imgs[d].resize((w,h),Image.Resampling.LANCZOS),(i*w,j*(h+30)+30),imgs[d].resize((w,h),Image.Resampling.LANCZOS));dr.text((i*w+8,j*(h+30)+8),name+' / '+d,fill=(245,245,245) if name!='Light' else (25,25,25))
im.save(OUT/'previews/backgrounds-logical.png')
# Original/candidate comparison uses complete locked logical canvases, target on separate labeled canvas.
im=Image.new('RGB',(192*3,382),(34,40,50));dr=ImageDraw.Draw(im)
for i,(label,p) in enumerate([('Original S',BASE/'inputs/original.png'),('Native candidate S',OUT/'frames/static-S.png'),('Fixed target (reference)',BASE/'inputs/target.png')]):
 x=Image.open(p).convert('RGBA')
 if i==2:x.thumbnail((192,352),Image.Resampling.LANCZOS)
 else:x=x.resize((192,352),Image.Resampling.LANCZOS)
 im.paste(x,(i*192+(192-x.width)//2,30),x);dr.text((i*192+5,8),label,fill='white')
im.save(OUT/'previews/comparison-logical.png')
im=Image.new('RGB',(192*4,352*2+60),(34,40,50));dr=ImageDraw.Draw(im)
for j,(label,folder) in enumerate([('Sealed round01','round-01'),('Current round02','round-02')]):
 for i,d in enumerate(DIRS):
  x=Image.open(BASE/'candidates'/folder/'frames'/f'static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);im.paste(x,(i*192,j*382+30),x);dr.text((i*192+8,j*382+8),label+' / '+d,fill='white')
im.save(OUT/'previews/prior-round-comparison.png')
alpha={};equal={}
for d,x in imgs.items():
 a=x.getchannel('A');bb=a.getbbox();bd=Image.new('L',x.size);bd.paste(a.crop((0,0,384,1)),(0,0));border=max(max(a.crop((0,0,384,1)).getdata()),max(a.crop((0,703,384,704)).getdata()),max(a.crop((0,0,1,704)).getdata()),max(a.crop((383,0,384,704)).getdata()))
 alpha[d]={'size':list(x.size),'bounds':list(bb),'borderTransparent':border==0,'rawSHA256':sha(OUT/'raw'/f'static-{d}'/'000.png'),'atlasSHA256':sha(OUT/'atlases'/f'static-{d}.png'),'exactRawAtlasBytes':sha(OUT/'raw'/f'static-{d}'/'000.png')==sha(OUT/'atlases'/f'static-{d}.png')}
 replay=Image.open(OUT/'reopened/raw'/f'static-{d}'/'000.png').convert('RGBA');diff=ImageChops.difference(x,replay);equal[d]={'decodedRGBAEqual':x.tobytes()==replay.tobytes(),'maximumChannelDifference':[v[1] for v in diff.getextrema()],'originalSHA256':sha(OUT/'raw'/f'static-{d}'/'000.png'),'replaySHA256':sha(OUT/'reopened/raw'/f'static-{d}'/'000.png')}
audit=json.loads((OUT/'reopened/native-audit.json').read_text());b=audit['evaluatedRootLocalBounds'];cam=audit['camera'];c=cam['calibration'];expected={'root':[192,512],'unitX':[256,0],'unitDepth':[0,256],'unitHeight':[0,-179.2]};cal=all(abs(c[k][i]-e)<.001 for k,v in expected.items() for i,e in enumerate(v));exp='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
checks={'frozenBriefUnchanged':sha(BASE/'brief.json')=='dc28411f7d85a9c577001b4fcd096ea9ed2174606175617c834587d6b4b90a3d','rootCalibration':cal,'identityCanonicalRoot':audit['canonicalRootMatrix']==[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],'heightWithinMeasured1_075':b['max'][2]<=1.0750000476837158+1e-5,'XYWithinOneCell':all(b['min'][i]>=-.50001 and b['max'][i]<=.50001 for i in (0,1)),'groundZ0':abs(b['min'][2])<1e-6,'allMeshesClosedManifold':all(m['nonManifoldEdges']==0 for m in audit['meshes']),'allMeshesGrounded':all(abs(m['evaluatedBounds']['min'][2])<1e-5 for m in audit['meshes']),'actualFacingPhases':all(abs(audit['facings'][d]['degrees']-deg)<1e-8 for d,deg in {'N':180,'E':90,'S':0,'W':-90}.items()),'noExternalImagesOrLibraries':not audit['externalImages'] and not audit['externalLibraries'],'staticNoActionsArmaturesShapeKeys':not audit['actions'] and not audit['armatures'] and not audit['shapeKeys'],'noGroundReceiver':audit['noGroundReceiver'],'noCompositing':not audit['render']['compositing'],'allFrames384x704':all(v['size']==[384,704] for v in alpha.values()),'noFrameClipping':all(v['borderTransparent'] for v in alpha.values()),'exactRawAtlasBytes':all(v['exactRawAtlasBytes'] for v in alpha.values()),'savedSourceReplayRGBAEqual':all(v['decodedRGBAEqual'] for v in equal.values()),'originalBackupUnchanged':sha(SRC/'original-library.blend')==exp,'originalSourceUnchanged':sha(BASE/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend')==exp}
write(OUT/'replay-verification.json',{'equality':'exact decoded RGBA, native PNG metadata may differ by file path/time','facings':equal,'allDecodedRGBAEqual':checks['savedSourceReplayRGBAEqual']})
write(OUT/'validation.json',{'asset':'decor-foreground-rock','round':2,'checks':checks,'allTechnicalChecksPass':all(checks.values()),'frozenBriefSHA256':sha(BASE/'brief.json'),'sourceBackupSHA256':sha(SRC/'original-library.blend'),'camera':cam,'evaluatedBounds':b,'alpha':alpha,'nativeValidation':'candidates/round-02/reopened/native-audit.json','portableReplay':'candidates/round-02/replay-verification.json','resources':{'selfContainedNative':True,'externalImageDependencies':[],'externalLibraries':[]},'visualApproval':'Independent judge pending'})
print(json.dumps({'checks':checks,'allTechnicalChecksPass':all(checks.values())},indent=2))
