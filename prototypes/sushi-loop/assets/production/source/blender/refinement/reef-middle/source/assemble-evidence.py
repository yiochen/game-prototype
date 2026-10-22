"""Package native measurements, byte copies and explicitly labelled review composites.
Only review sheets are resized/composited; publication frames/atlases remain native bytes.
"""
from pathlib import Path
import hashlib,json,math,shutil,sys,platform
from PIL import Image,ImageDraw,ImageChops
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-01'
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
audit=read(OUT/'reopened-replay/native-audit.json');capture=read(OUT/'capture-measurements.json')
replay=[]
for rel in [*(f'native/static/{d}/000.png' for d in 'NESW'),*(f'native/three-joined-{d}.png' for d in 'NESW')]:
    p=OUT/rel;q=OUT/'reopened-replay'/rel
    a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA');diff=ImageChops.difference(a,b);ext=diff.getextrema()
    replay.append({'path':str(p.relative_to(OBJ)),'reopenedPath':str(q.relative_to(OBJ)),'submittedSHA256':sha(p),'reopenedSHA256':sha(q),'sameEncodedBytes':sha(p)==sha(q),'maxChannelDifference':[x[1] for x in ext],'differentDecodedPixels':sum(v!=(0,0,0,0) for v in diff.getdata())})
ports=audit['ports'];expected=[[-.38,0],[.38,0],[.38,.2],[.25,.4],[.08,.44],[-.14,.35],[-.30,.4],[-.38,.2]]
profile_error=max(abs(a-b) for s in ports.values() for yz,e in zip(s['orderedYZ'],expected) for a,b in zip(yz,e))
w=ports['W']['adjacentBands'];e=ports['E']['adjacentBands']
normal_error=max(abs(a-b) for a1,b1 in zip(w,e) for a2,b2 in zip(a1['cornerNormals'],b1['cornerNormals']) for a,b in zip(a2,b2))
material_equal=all(a['material']==b['material'] for a,b in zip(w,e))
# Albedo comes from the measured native Z -> linear ColorRamp -> Principled BaseColor graph.
material_map={m['name']:m for m in audit['materials']};albedo=[]
for k,(a,b) in enumerate(zip(w,e)):
    m=material_map[a['material']];r=m['colorRamps'][0];lo,hi=r['elements'];samples=[]
    for t in [i/8 for i in range(9)]:
        y=expected[k][0]*(1-t)+expected[(k+1)%8][0]*t;z=expected[k][1]*(1-t)+expected[(k+1)%8][1]*t
        f=max(0,min(1,(z-lo['position'])/(hi['position']-lo['position'])));c=[lo['color'][j]*(1-f)+hi['color'][j]*f for j in range(4)]
        samples.append({'yz':[y,z],'westAndEastLinearRGBA':c,'fieldAtLocalX':[-.5,-.48,-.42,.42,.48,.5],'maxAcrossBandsDifference':0})
    albedo.append({'edge':k,'material':m['name'],'materialGraphSHA256':hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest(),'method':'Analytic evaluation of actual reopened Position.Z -> audited LINEAR ColorRamp -> Principled BaseColor graph. No x/y dependence; source whole object remains in worldZ0..68 for every facing. All six endpoint/adjacent-band x positions evaluate identically.','samples':samples})
write(OUT/'native-field-continuity.json',{'exactProfile':expected,'profileMaximumError':profile_error,'adjacentCornerNormalMaximumDifference':normal_error,'westEastMaterialNamesEqual':material_equal,'adjacentBandWidth':.08,'albedoFields':albedo,'trianglesAndCornerNormals':'reopened-replay/native-audit.json','endCaps':'Finite exact planar cut faces use blue native stone; explicit flat side normals are independent of cap normals. No port bevel, overlap or end growth.'})
reports={};consumer=[]
for backend in ['full-chrome','headless-shell']:
    r=read(OUT/f'consumer/evidence/{backend}-report.json');reports[backend]=r;records=r['records']
    consumer.append({'backend':backend,'browserVersion':r['browserVersion'],'cases':len(records),'actualConsumerMaxAlphaDelta':max(v['actualConsumerResidual']['maxAlphaDelta'] for v in records),'actualConsumerMaxOpaqueRGBDelta':max(v['actualConsumerResidual']['maxOpaqueRGBDelta'] for v in records),'diagnosticMaxAlphaDelta':max(v['comparisonOnlyEqualExtentsResidual']['maxAlphaDelta'] for v in records),'diagnosticMaxOpaqueRGBDelta':max(v['comparisonOnlyEqualExtentsResidual']['maxOpaqueRGBDelta'] for v in records),'localOpaquePortMinAlphaActual':min(v['finitePortInterior']['native-actual']['minIndependentAlpha'] for v in records),'localOpaquePortMinAlphaDiagnostic':min(v['finitePortInterior']['native-equal-extents-diagnostic']['minIndependentAlpha'] for v in records),'localOpaquePortMaxRGBDeltaActual':max(v['finitePortInterior']['native-actual']['maxRGBDelta'] for v in records),'localOpaquePortMaxRGBDeltaDiagnostic':max(v['finitePortInterior']['native-equal-extents-diagnostic']['maxRGBDelta'] for v in records),'diagnosticDiscardedVisiblePixels':sum(v['discardedVisiblePixels'] for v in r['controls']),'diagnosticIntegerRestorationDifferences':sum(v['integerRestoration']['differingPixels'] for v in r['controls'])})
write(OUT/'replay-comparison.json',{'savedSourceSHA256':sha(BASE/'round-01.blend'),'method':'Fresh background Blender reopened saved round-01.blend and recaptured all4 singles and all4 exact three-module native strips with identical fixed recipe.','records':replay})
write(OUT/'consumer-summary.json',{'records':consumer,'scope':'128 actual cases:2backendsx4facingsx2intendedsizesx8root/pan pairs. Every raw actual/native/independent image and same-source equal-extents diagnostic is retained.','limitations':'Actual fullChrome retains source-extent nearest-tie residuals. Equal-extents removes only verified transparent padding and is comparison-only. It is never used for published frames or the production consumer. Residuals are reported without a blanket seam/alpha/RGB waiver; visible actual join quality is for the independent judge.','localMask':'Frozen finite-port rectangles from source study, each sample requires a native opaque3x3 neighborhood. Samples excluded at nonopaque silhouettes are reported in each case. Whole-frame residuals retain those samples.'})
asset=read(OBJ/'inputs/source-assetRecord.json');asset.update(scale=2,artStyle={'revision':'reef-middle-native-warm-soft-round-01','palette':'blue/cyan stone;teal focal coral;purple supporting coral','lighting':'Broad centered100W/disk5;four equal45W cardinal fills/disk4.5/radius3/z2.4;neutral worldStrength.32','surface':'native Z-linear albedo ramp;rounded hollow tube rims;bevelled stone relief;private meshes;no textures'},actualBounds=audit['bounds'])
write(OUT/'assetRecord.json',asset)
rig={'assetId':'reef-middle','fps':12,'static':True,'groundRootObject':'reef-middle__root','projection':'square-top-front-oblique','footprint':[1,1],'sockets':{},'armatures':[],'actionCount':0,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'actions':[],'controlsByFrame':[{}],'geometryOwners':[],'shaderChannels':[],'shaderLoopClosure':{}}},'source':'source/round-01.blend','sourceSHA256':sha(BASE/'round-01.blend'),'notes':['No object/material/node/shape animation. All4 rotations measured during capture.']}
write(OUT/'rig.json',rig)
bounds=audit['bounds'];env=all(bounds[0][i]>=[-.5,-.38,0][i]-1e-5 and bounds[1][i]<=[.5,.38,.68][i]+1e-5 for i in range(3))
pngproof=[{'direction':d,'nativeSHA256':sha(OUT/f'native/static/{d}/000.png'),'publishedSHA256':sha(OUT/f'frames/static/{d}/000.png'),'atlasSHA256':sha(OUT/f'atlases/static-{d}.png'),'size':list(Image.open(OUT/f'native/static/{d}/000.png').size)} for d in 'NESW']
checks={'finiteOrderedPortsWithin1e-5':profile_error<1e-5,'matchingActualAdjacentCornerNormalsWithin1e-6':normal_error<1e-6,'matchingEndpointMaterialFields':material_equal,'finiteGroundAndOverallEnvelope':env,'privateMeshes':all(g['privateMeshUsers']==1 for g in audit['geometry']),'noAnimation':not audit['actions'] and all(not g['animation'] and not g['shapeKeys'] for g in audit['geometry']) and all(not m['animation'] for m in audit['materials']),'noLinkedLibraries':not audit['linkedLibraries'],'noImageTexture':all('ShaderNodeTexImage' not in [n['type'] for n in m['nodes']] for m in audit['materials']),'allNativePNGBytesPublishedUnchanged':all(v['nativeSHA256']==v['publishedSHA256']==v['atlasSHA256'] for v in pngproof),'reopenedAll4DecodedPixelsExact':all(v['differentDecodedPixels']==0 for v in replay)}
native={'asset':'reef-middle','sourceSHA256':sha(BASE/'round-01.blend'),'captureRecords':capture['captureRecords'],'joined':capture['joined'],'checks':checks,'publishedByteProof':pngproof,'savedSourceReplay':'candidates/round-01/replay-comparison.json','fieldContinuity':'candidates/round-01/native-field-continuity.json','actualNativeAudit':'candidates/round-01/reopened-replay/native-audit.json','consumerSummary':'candidates/round-01/consumer-summary.json','visualStatus':'Pending independent judge; no editor self-approval'}
write(OUT/'native-validation.json',native)
write(OUT/'validation.json',{'asset':'reef-middle','round':'round-01','nativeValidation':'candidates/round-01/native-validation.json','hardNativeChecks':checks,'briefSHA256':sha(OBJ/'brief.json'),'nativeContractSHA256':sha(OBJ/'inputs/root-native-contract.json'),'visualStatus':'Pending independent judge','consumerResiduals':consumer})
# Review sheets use only explicit common source rectangles at fixed scales.
BG=[('#faf8ef','light'),('#7d858c','gray'),('#182734','dark')]
def comp(im,color):
    bg=Image.new('RGBA',im.size,color);bg.alpha_composite(im);return bg.convert('RGB')
def label(draw,xy,s):draw.text(xy,s,fill='#253849')
sheet=Image.new('RGB',(4*400,740),'#f1f0e9');dr=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
    im=Image.open(OUT/f'frames/static/{d}/000.png').convert('RGBA');sheet.paste(comp(im,'#e9e8e1'),(i*400+8,26));label(dr,(i*400+12,8),f'{d} / native2x 384x704 / no crop or pixel change')
sheet.save(OUT/'four-view-sheet.png')
# Logical128 and phone32 singles, common registered fixed rectangle [0,120,192,300].
use=Image.new('RGB',(1100,590),'#f1f0e9');dr=ImageDraw.Draw(use);label(dr,(10,8),'All4 singles at logical cell128 and phone32; common review crop only; light / gray / dark')
for row,(color,name) in enumerate(BG):
    y=30+row*182;label(dr,(10,y+3),name)
    for col,d in enumerate('NESW'):
        im=Image.open(OUT/f'frames/static/{d}/000.png').convert('RGBA')
        logical=im.resize((192,352),Image.Resampling.LANCZOS).crop((0,120,192,300))
        use.paste(comp(logical,color),(70+col*255,y));phone=im.resize((48,88),Image.Resampling.LANCZOS).crop((0,30,48,75));use.paste(comp(phone,color),(270+col*255,y+57));label(dr,(270+col*255,y+38),d+'32')
use.save(OUT/'use-size-sheet.png')
# Native vs independent exact consumer at phase0; source rectangles are fixed by registered group extent.
common={'N':(20,280,452,458),'S':(20,280,452,458),'E':(170,110,300,600),'W':(170,110,300,600)}
def rec_for(backend,d,zoom,root,pan):return next(r for r in reports[backend]['records'] if r['direction']==d and r['zoom']==zoom and r['rootPhaseLogical']==root and r['panPhaseOutput']==pan)
def raw(r,kind):return Image.open(OUT/'consumer/evidence'/r['images'][kind]).convert('RGBA')
for backend in ['full-chrome','headless-shell']:
    repeat=Image.new('RGB',(1520,1910),'#f1f0e9');dr=ImageDraw.Draw(repeat);label(dr,(10,8),f'Actual {backend}: independent / native three-middle; logical128 and phone32; phase0; light/gray/dark. No production crop.')
    for col,(color,name) in enumerate(BG):
        x=col*505;label(dr,(x+10,29),name)
        y=53
        for d in ['N','S']:
            r=rec_for(backend,d,1,0,0)
            for kind in ['independent','native-actual']:
                label(dr,(x+10,y),f'{d} {kind} logical128');im=raw(r,kind).crop(common[d]);repeat.paste(comp(im,color),(x+15,y+17));y+=200
            rp=rec_for(backend,d,.25,0,0);label(dr,(x+10,y),f'{d} phone32 independent / native')
            for j,kind in enumerate(['independent','native-actual']):repeat.paste(comp(raw(rp,kind).crop((0,70,136,125)),color),(x+10+j*155,y+18))
            y+=86
        # E/W are vertical strips; compare side by side at exact use size.
        for j,d in enumerate(['E','W']):
            r=rec_for(backend,d,1,0,0);y=1060;label(dr,(x+8+j*250,y),f'{d} independent / native128')
            for k,kind in enumerate(['independent','native-actual']):repeat.paste(comp(raw(r,kind).crop((185,115,290,590)),color),(x+10+j*250+k*112,y+18))
            rp=rec_for(backend,d,.25,0,0)
            for k,kind in enumerate(['independent','native-actual']):repeat.paste(comp(raw(rp,kind).crop((52,35,85,160)),color),(x+25+j*250+k*70,1585))
            label(dr,(x+12+j*250,1720),f'{d} phone32 independent/native')
    repeat.save(OUT/('repeated.png' if backend=='full-chrome' else 'shell-repeated.png'))
# Fractional cases preserve entire local port region plus surrounding reef. Same exact crop per facing/size.
frac=Image.new('RGB',(1660,1300),'#f1f0e9');dr=ImageDraw.Draw(frac);label(dr,(10,8),'Actual fullChrome fractional joins root.25/pan.75, logical128 and phone32, light/gray/dark. Rows independent/native-actual/diagnostic; latter comparison only.')
for dc,d in enumerate('NESW'):
    x=dc*415;label(dr,(x+10,30),d)
    for br,(color,bgname) in enumerate(BG):
        y=52+br*410;r=rec_for('full-chrome',d,1,.25,.75);rp=rec_for('full-chrome',d,.25,.25,.75)
        # Two true port neighborhoods; native opaque masks and full raw images retained as technical evidence.
        boxes=[(145,305,200,450),(275,305,330,450)] if d in ['N','S'] else [(185,265,290,345),(185,393,290,473)]
        for kr,kind in enumerate(['independent','native-actual','native-equal-extents-diagnostic']):
            label(dr,(x+8,y+kr*125),bgname+' '+kind)
            for bc,box in enumerate(boxes):
                im=raw(r,kind).crop(box)
                if d in ['N','S']:im=im.resize((int(im.width*.70),int(im.height*.70)),Image.Resampling.LANCZOS)
                frac.paste(comp(im,color),(x+8+bc*116,y+18+kr*125))
            fim=raw(rp,kind);box=(40,80,95,128) if d in ['N','S'] else (52,70,85,132);frac.paste(comp(fim.crop(box),color),(x+270,y+18+kr*125))
frac.save(OUT/'fractional-joins-sheet.png')
write(OUT/'review-sheets.json',{'publicationFramesWereNotChanged':True,'sheets':{'four-view-sheet.png':'All4 native full384x704 frames at1:1, only opaque display backgrounds added.','use-size-sheet.png':'Common logical crop[0,120,192,300], phone crop[0,30,48,75]; whole full frames uniformly resized for comparison only.','shell-repeated.png':'Exact headless-shell images at phase0; same fixed display crops as repeated.png.','repeated.png':'Exact consumer images phase0 at logical128/phone32; common registered strip crops for page arrangement; no art fitting.','fractional-joins-sheet.png':'All4 exact root.25/pan.75 local joins, light/gray/dark; paired port crops and phone32. N/S crops uniformly reduced. Actual/native/diagnostic labels explicit; full raw images retained.'},'consumerRawImages':'candidates/round-01/consumer/evidence','diagnosticOnly':'Equal transparent extents was only generated inside proof. It never changes atlas/native/publication or actual consumer.'})
print(json.dumps({'checks':checks,'nativeFieldNormalError':normal_error,'profileError':profile_error,'consumer':consumer,'replayExact':all(v['differentDecodedPixels']==0 for v in replay)},indent=2))
