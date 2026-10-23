from pathlib import Path
from collections import Counter
import json,hashlib
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-02'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
old=read(OBJ/'candidates/round-01/reopened-replay/native-audit.json');new=read(OUT/'reopened-replay/native-audit.json')
vm=lambda v:tuple(round(x,8) for x in v)
edges=Counter(tuple(sorted((vm(t['vertices'][i]),vm(t['vertices'][(i+1)%3])))) for t in new['evaluatedTriangles'] for i in range(3))
port_same=True
for side in ['W','E']:
    a,b=old['ports'][side],new['ports'][side]
    port_same &= a['orderedYZ']==b['orderedYZ']
    for p,q in zip(a['adjacentBands'],b['adjacentBands']):
        for key in ['sectionEdge','vertices','normal','cornerNormals','material','baseColor']:port_same &= p[key]==q[key]
material_names=set(p['material'] for p in new['ports']['W']['adjacentBands']);om={m['name']:m for m in old['materials']};nm={m['name']:m for m in new['materials']}
material_same=all(om[n]==nm[n] for n in material_names)
preservation=read(OUT/'round-01-preservation.json');prior=read(BASE/'round-02-prior-integrity.json')
bad=[r['path'] for r in prior['files'] if sha(OBJ/r['path'])!=r['sha256']]
checks={'actualPortProfileAndAdjacentTriangleCornerFieldsPreservedFromRound01':bool(port_same),'endpointNativeAlbedoMaterialGraphsPreservedFromRound01':material_same,'continuousCoreClosedManifold':set(edges.values())=={2},'allPriorFrozenAndDevelopmentBytesUnchanged':not bad,**preservation['checks']}
assert all(checks.values()),checks
stone_names=['reef-middle__focal_rock','reef-middle__front_rock','reef-middle__left_stone','reef-middle__right_stone'];old_geo={g['name']:g for g in old['geometry']};new_geo={g['name']:g for g in new['geometry']}
volumes=[{'object':n,'round01Bounds':old_geo[n]['bounds'],'round02Bounds':new_geo[n]['bounds'],'round01Extent':[old_geo[n]['bounds'][1][i]-old_geo[n]['bounds'][0][i] for i in range(3)],'round02Extent':[new_geo[n]['bounds'][1][i]-new_geo[n]['bounds'][0][i] for i in range(3)]} for n in stone_names]
alpha=[]
for d in 'NESW':
    p=OUT/f'frames/static/{d}/000.png';im=Image.open(p).convert('RGBA');a=im.getchannel('A');bbox=a.getbbox();w,h=im.size
    edgesa=[a.crop((0,0,w,1)).getbbox(),a.crop((0,h-1,w,h)).getbbox(),a.crop((0,0,1,h)).getbbox(),a.crop((w-1,0,w,h)).getbbox()]
    alpha.append({'direction':d,'nativeFrame':list(im.size),'alphaBounds':list(bbox),'frameBoundaryHasNonzeroAlpha':any(v is not None for v in edgesa),'nativeSHA256':sha(OUT/f'native/static/{d}/000.png'),'publishedSHA256':sha(p),'atlasSHA256':sha(OUT/f'atlases/static-{d}.png')})
assert all(not v['frameBoundaryHasNonzeroAlpha'] for v in alpha)
consumer_source=(BASE/'resources/consumer/world-sprite-raster.js').read_text();start=consumer_source.index('export function worldRasterPlan');end=consumer_source.index('export function useWorldSpriteRaster')
assert consumer_source[start:end].strip()==(BASE/'resources/consumer/exact-used-raster-functions.js').read_text().strip()
checks.update(noFrameAlphaClipping=True,exactFrozenConsumerFunctionExtraction=True)
write(OUT/'round-02-native-construction-and-preservation.json',{'method':'Actual saved-source audit, old/new endpoint band and native material-graph comparison, geometric triangle-edge incidence, native boulder extent measurements, prior-byte verification and alpha bounds. Technical checks only; original judge owns visual verdict.','checks':checks,'coreTriangleEdges':len(edges),'coreEdgeIncidenceCounts':dict(Counter(edges.values())),'nativeStoneChanges':volumes,'newRearCrown':new_geo['reef-middle__rear_crown'],'priorFilesVerified':len(prior['files']),'priorFailures':bad,'alphaFrames':alpha,'consumerSHA256':sha(BASE/'resources/consumer/world-sprite-raster.js'),'spriteLayoutSHA256':sha(BASE/'resources/consumer/sprite-layout.js')})
for name in ['native-validation.json','validation.json']:
    p=OUT/name;v=read(p);key='checks' if name=='native-validation.json' else 'hardNativeChecks';v[key].update(checks);v['rockConstructionAndPriorIntegrity']='candidates/round-02/round-02-native-construction-and-preservation.json';v['replayObservations']='candidates/round-02/replay-comparison.json';write(p,v)
# Common registered review crop and uniform scale. No fitting and no publication changes.
sheet=Image.new('RGB',(1120,510),'#efeee7');draw=ImageDraw.Draw(sheet)
draw.text((10,8),'Round01 sealed candidate / Round02 candidate, same registered camera and lights. Logical128 with phone32. Common review crops only.',fill='#253849')
for row,rn in enumerate(['round-01','round-02']):
    y=30+row*235;draw.text((10,y+5),rn,fill='#253849')
    for col,d in enumerate('NESW'):
        full=Image.open(OBJ/f'candidates/{rn}/frames/static/{d}/000.png').convert('RGBA')
        im=full.resize((192,352),Image.Resampling.LANCZOS).crop((0,120,192,320));bg=Image.new('RGBA',im.size,'#a0a5a5');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(75+col*260,y+10))
        small=full.resize((48,88),Image.Resampling.LANCZOS).crop((0,30,48,80));bg=Image.new('RGBA',small.size,'#a0a5a5');bg.alpha_composite(small);sheet.paste(bg.convert('RGB'),(272+col*260,y+75));draw.text((272+col*260,y+55),d+'32',fill='#253849')
sheet.save(OUT/'round-01-round-02-comparison.png')
reviews=read(OUT/'review-sheets.json');reviews['sheets']['round-01-round-02-comparison.png']='Exact sealed round01 and new round02 source frames uniformly scaled and common fixed crop[0,120,192,320]logical; phone crop[0,30,48,80], opaque gray display. Source PNGs remain unchanged; older frames are bound resources.';write(OUT/'review-sheets.json',reviews)
print(json.dumps({'checks':checks,'priorFilesVerified':len(prior['files']),'coreTriangleEdges':len(edges),'coreEdgeIncidenceCounts':dict(Counter(edges.values()))},indent=2))
