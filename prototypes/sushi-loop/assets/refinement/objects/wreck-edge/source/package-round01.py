"""Identity publication, measured residuals and labeled whole-frame review sheets.
Pillow is used only for review composition and exact copies, never sprite repair.
"""
from pathlib import Path
import json,hashlib,shutil,math
from PIL import Image,ImageDraw
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;RES=HERE/'round01-resources';OUT=EXP/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n')
openim=lambda p:Image.open(p).convert('RGBA')
BG={'light':'#eeeeee','gray':'#808080','dark':'#151923'}
def composited(im,bg):
    x=Image.new('RGBA',im.size,bg);x.alpha_composite(im);return x
def label(draw,pos,text,fill='white'):draw.text(pos,text,fill=fill)
def metrics(a,b):
    aa=np.asarray(a).astype(int);bb=np.asarray(b).astype(int)
    if aa.shape!=bb.shape:return {'sameSize':False,'aSize':a.size,'bSize':b.size}
    dif=np.abs(aa-bb);mask=np.any(dif,axis=2);yy,xx=np.nonzero(mask)
    return {'sameSize':True,'decodedEqual':not bool(mask.any()),'maxRGBA':dif.max(axis=(0,1)).tolist(),'meanAbsRGBA':dif.mean(axis=(0,1)).tolist(),'differentPixels':int(mask.sum()),'alphaDifferentPixels':int((dif[:,:,3]>0).sum()),'differenceBounds':None if not len(xx) else [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]}

publication=[]
for d in 'NESW':
    n=OUT/'native/static'/d/'000.png';im=openim(n);assert im.size==(384,704)
    for p in [OUT/'frames/static'/d/'000.png',OUT/'atlases'/f'static-{d}.png']:
        p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(n,p);assert sha(p)==sha(n)
    publication.append({'direction':d,'native':str(n.relative_to(EXP)),'published':f'candidates/round-01/frames/static/{d}/000.png','atlas':f'candidates/round-01/atlases/static-{d}.png','sha256':sha(n),'nativeSize':im.size,'alphaBounds':im.getbbox(),'identityBytes':True,'atlasRect':[0,0,384,704]})
write(OUT/'publication-identity.json',{'method':'Exact PNG byte copy, no reduction/crop/fit/repair/recolor; review sheets only use uniform whole-frame display scaling','frames':publication})

# Replay the saved editable source in a separate clean process; compare decoded
# bytes and record exact hashes. No rendered pixel is replaced by replay output.
replay=Path('/tmp/wreck-edge-round01-replay');replays=[]
for d in 'NESW':
    for sub in [f'native/static/{d}/000.png',f'mixed-native/{d}.png']:
        a=OUT/sub;b=replay/sub;r=metrics(openim(a),openim(b))
        if sha(a)==sha(b):retained=str(a.relative_to(EXP))
        else:
            retained_path=OUT/'saved-source-replay'/sub;retained_path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b,retained_path);retained=str(retained_path.relative_to(EXP))
        replays.append({'submitted':str(a.relative_to(EXP)),'replayPathTemporary':str(b),'retainedReplayOrExactAlias':retained,'submittedSHA256':sha(a),'replaySHA256':sha(b),**r})
assert all(x['decodedEqual'] for x in replays if '/native/static/' in x['submitted'])
shutil.copyfile(replay/'capture-records.json',OUT/'saved-source-replay-records.json')
shutil.copyfile(replay/'native-assembly-records.json',OUT/'saved-source-replay-assembly-records.json')
write(OUT/'saved-source-replay.json',{'actualSavedSourceSHA256':sha(HERE/'round-01.blend'),'method':'Separate background process read exact saved source; private recapture path, unchanged one recipe and actual root poses. All four heroes decode exactly. Seven of eight images decode exactly; mixed E has one red channel value differing by1 at one pixel, alpha identical. This measured residual is retained as its own image. Exact hashes may alias retained submitted paths. Temporary duplicate image tree is not a dependency.','images':replays})

# All four untrimmed native singles over gray at native2x, same registration.
sheet=Image.new('RGBA',(4*384,740),'#394552');dr=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
    label(dr,(i*384+12,10),'wreck-edge '+d+' / direct native2x')
    sheet.alpha_composite(composited(openim(OUT/'frames/static'/d/'000.png'),BG['gray']),(i*384,32))
sheet.convert('RGB').save(OUT/'four-view-sheet.png')

# Logical128 and phone32 singles, complete frame and every backdrop.
for scale,name in [(.5,'logical128-singles'),(.125,'phone')]:
    w,h=round(384*scale),round(704*scale);can=Image.new('RGBA',(4*(w+12)+12,3*(h+24)+12),'#394552');dr=ImageDraw.Draw(can)
    for row,(bg,c) in enumerate(BG.items()):
        for i,d in enumerate('NESW'):
            x=12+i*(w+12);y=12+row*(h+24);label(dr,(x,y),d+' '+bg)
            im=openim(OUT/'frames/static'/d/'000.png').resize((w,h),Image.Resampling.NEAREST)
            can.alpha_composite(composited(im,c),(x,y+18))
    can.convert('RGB').save(OUT/(name+'.png'))

# Native connected scenes, all four directions, complete frames over all backgrounds.
for scale,name in [(.5,'repeated'),(.125,'phone-mixed')]:
    widths=[int(openim(OUT/'mixed-native'/f'{d}.png').width*scale) for d in 'NESW']
    heights=[int(openim(OUT/'mixed-native'/f'{d}.png').height*scale) for d in 'NESW']
    cellw=max(widths);W=3*(cellw+12)+12;H=sum(h+28 for h in heights)+12
    can=Image.new('RGBA',(W,H),'#394552');dr=ImageDraw.Draw(can);y=12
    for i,d in enumerate('NESW'):
        for col,(bg,c) in enumerate(BG.items()):
            x=12+col*(cellw+12);label(dr,(x,y),d+' native mixed / '+bg)
            im=openim(OUT/'mixed-native'/f'{d}.png').resize((widths[i],heights[i]),Image.Resampling.NEAREST)
            can.alpha_composite(composited(im,c),(x,y+18))
        y+=heights[i]+28
    can.convert('RGB').save(OUT/(name+'.png'))

# Source and native candidate use identical complete frames/scale. Target and
# style reference are labeled whole-frame style guides, uniformly display-scaled.
can=Image.new('RGBA',(1200,770),'#394552');dr=ImageDraw.Draw(can)
for x,title,p in [(10,'Original native snapshot',RES/'original.png'),(310,'Candidate native S',OUT/'frames/static/S/000.png'),(610,'Fixed target / aesthetic guide',RES/'fixed-target.png'),(910,'Warm-soft style reference',RES/'warm-soft-reference.png')]:
    label(dr,(x,10),title);im=openim(p);s=min(280/im.width,720/im.height);im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST if x<610 else Image.Resampling.LANCZOS)
    can.alpha_composite(composited(im,BG['gray']),(x,35))
can.convert('RGB').save(OUT/'source-target.png')

results=json.loads((OUT/'consumer/results.json').read_text());comparisons=[];mode_comparisons=[]
for case in results['cases']:
    prefix=case['mode']+'-'+case['id'];rows=[];H=20
    for d in 'NESW':
        a=openim(OUT/'consumer'/f'{prefix}-{d}-independent.png');b=openim(OUT/'consumer'/f'{prefix}-{d}-native-control.png')
        fixture=next(f for f in case['evidence']['fixtures'] if f['direction']==d)
        info={'mode':case['mode'],'case':case['id'],'direction':d,'raw':metrics(a,b),'interpretation':'Raw independently captured exact sprites versus true mixed native. Broad finite area light/exterior precision residuals remain unmodified and are distinct from local visible joins.'}
        aa=np.asarray(a);bb=np.asarray(b);plan=fixture['plan'];off=case['evidence']['case']['rootOffset'];r=[(off[i]-[plan['x'],plan['y']][i])*plan['scale'] for i in range(2)]
        bands=[]
        vertical=d in 'EW'
        for sign in [-1,1]:
            axis=1 if vertical else 0;c=round(r[axis]+sign*128)
            ar=(aa[max(0,c-3):c+4,:,:] if vertical else aa[:,max(0,c-3):c+4,:]);br=(bb[max(0,c-3):c+4,:,:] if vertical else bb[:,max(0,c-3):c+4,:]);delta=np.abs(ar.astype(int)-br.astype(int))
            bands.append({'axis':'y' if vertical else 'x','centerPixel':c,'halfWidth':3,'maxRGBA':delta.max(axis=(0,1)).tolist(),'alphaDifferentPixels':int((delta[:,:,3]>0).sum()),'differentPixels':int(np.any(delta,axis=2).sum())})
        info['localJoinBandsUnmodified']=bands;comparisons.append(info)
        # Full native canvas at logical128 beside actual connected control.
        # No cropping or fitting; display scale .5 only.
        a=a.resize((round(a.width*.5),round(a.height*.5)),Image.Resampling.NEAREST);b=b.resize((round(b.width*.5),round(b.height*.5)),Image.Resampling.NEAREST)
        rows.append((d,a,b));H+=max(a.height,b.height)+32
    W=max(a.width+b.width+36 for _,a,b in rows);canvas=Image.new('RGBA',(W,H),'#394552');draw=ImageDraw.Draw(canvas);y=10
    for d,a,b in rows:
        label(draw,(10,y),d+' actual 570/099 independent');label(draw,(a.width+24,y),d+' true mixed native control')
        canvas.alpha_composite(composited(a,BG['gray']),(10,y+18));canvas.alpha_composite(composited(b,BG['gray']),(a.width+24,y+18));y+=max(a.height,b.height)+32
    canvas.convert('RGB').save(OUT/'consumer'/f'{prefix}-comparison.png')

for case_id in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
    entry={'case':case_id,'native':[]}
    for d in 'NESW':
        a=OUT/'consumer'/f'full-chromium-{case_id}-{d}-independent.png';b=OUT/'consumer'/f'bundled-headless-shell-{case_id}-{d}-independent.png';entry['native'].append({'direction':d,**metrics(openim(a),openim(b))})
    a=OUT/'consumer'/f'full-chromium-{case_id}-css.png';b=OUT/'consumer'/f'bundled-headless-shell-{case_id}-css.png';entry['actualCSS']=metrics(openim(a),openim(b));mode_comparisons.append(entry)
write(OUT/'consumer-analysis.json',{'allEightRunsZeroPageErrors':all(not c['errors'] for c in results['cases']),'browserVersions':sorted(set(c['browserVersion'] for c in results['cases'])),'nativeIndependentVersusTrueNative':comparisons,'crossMode':mode_comparisons,'noPixelRepair':True,'interpretation':'Numeric values are retained raw. They do not establish visual approval or waive a local seam. Native canvas nearest display and actual CSS screenshots are separate evidence layers.'})

native=json.loads((OUT/'native-validation.json').read_text());caps=json.loads((OUT/'capture-records.json').read_text())
asset=json.loads((RES/'source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'warm-soft-native-round01','lighting':'Exact approved middle02 rig; five symmetric no-shadow area lights','noGroundShadow':True}
write(OUT/'assetRecord.json',asset)
write(OUT/'rig.json',{'asset':'wreck-edge','root':'wreck-edge__root','rootMatrix':native['rootMatrix'],'rootProperties':native['rootProperties'],'staticOwnership':native['staticOwnership'],'nativeSourceSHA256':native['sourceSHA256'],'directions':{'N':180,'E':90,'S':0,'W':-90},'sockets':{},'ports':asset['ports'],'lights':native['lights'],'world':native['world'],'render':native['render'],'meshCount':sum(o['type']=='MESH' for o in native['meshes']),'curveCount':sum(o['type']=='CURVE' for o in native['meshes'])})
write(OUT/'validation.json',{'asset':'wreck-edge','round':'round-01','nativeValidation':'candidates/round-01/native-validation.json','captureRecords':caps['captureRecords'],'measuredSourceSHA256':native['sourceSHA256'],'fullFiniteFieldEquivalence':native['fullFiniteContactProof']['actualSavedGeometryAndActiveFieldsEqual'],'finiteSupportArea':native['support']['area'],'noOutsideEnvelope':not native['evaluatedOutsideEnvelope'] and not native['rawOutsideEnvelope'],'savedSourceReplay':'candidates/round-01/saved-source-replay.json','consumerEvidence':'candidates/round-01/consumer/results.json','rawConsumerAnalysis':'candidates/round-01/consumer-analysis.json','publicationIdentity':'candidates/round-01/publication-identity.json','limitations':'Technical evidence only. The original independent judge must assess every declared visual and both local contacts in all views. No self approval.'})
print('PACKAGED',len(replays),'saved-source replays;',len(results['cases']),'browser runs; raw residuals preserved')
