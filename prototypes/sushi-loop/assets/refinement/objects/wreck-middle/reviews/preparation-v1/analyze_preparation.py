"""Source measurements, bounded replay comparisons and visual evidence only."""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import numpy as np
OUT=Path(__file__).resolve().parent
OBJECT=OUT.parent.parent
PRODUCTION=OBJECT.parents[2]/'production'
def dump(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(a,b):
    x=np.asarray(a.convert('RGBA'),dtype=np.int16);y=np.asarray(b.convert('RGBA'),dtype=np.int16)
    delta=np.abs(x-y); visible=(x[:,:,3]>0)|(y[:,:,3]>0)
    px=np.concatenate([x[:,:,:3].astype(float)*x[:,:,3:]/255,x[:,:,3:]],2)
    py=np.concatenate([y[:,:,:3].astype(float)*y[:,:,3:]/255,y[:,:,3:]],2)
    pd=np.abs(px-py)
    return {'changedPixels':int(np.any(delta!=0,2).sum()),'visiblePixels':int(visible.sum()),'rgbaMax':int(delta.max()),
        'alphaMax':int(delta[:,:,3].max()),'premultipliedMax':float(pd.max()),
        'premultipliedVisibleMean':float(pd[visible].mean()) if visible.any() else 0,'decodedRGBAEqual':bool(not delta.any())}
source=json.loads((OUT/'source-inspection.json').read_text())
mesh=[o for o in source['objects'] if 'mesh' in o]
report={'sourceSHA256':sha(PRODUCTION/'source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'),
 'coordinateConvention':'local X length; local +Y rear; Z up. Outward W=-X, E=+X. Ordered yz rings below follow authored +X extrusion, not outward winding at W.',
 'tolerance':1e-6, 'geometryBounds':[[min(v[i] for o in mesh for v in o['mesh']['vertices']),max(v[i] for o in mesh for v in o['mesh']['vertices'])] for i in range(3)],
 'ports':{},'materials':{},'finiteSupport':{},'perPartBounds':[]}
for o in mesh:
    vs=o['mesh']['vertices']; report['perPartBounds'].append({'name':o['name'],'bounds':[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]})
for side,x in [('W',-.5),('E',.5)]:
    port={'position':[x,0,0],'outwardNormal':[-1 if x<0 else 1,0,0],'sections':[]}
    for o in mesh:
        m=o['mesh'];ids=[i for i,v in enumerate(m['vertices']) if abs(v[0]-x)<1e-6]
        if not ids:continue
        incident=[q for q in m['polygons'] if any(i in ids for i in q['vertices'])]
        section={'name':o['name'],'authoredRingVertices':[m['vertices'][i] for i in ids],
          'cap':[q for q in incident if all(i in ids for i in q['vertices'])],
          'sideFields':[{'vertices':[m['vertices'][i] for i in q['vertices']], 'materialName':m['materials'][q['material']],
            'normal':q['normal_local'],'loopNormals':[l['normal_local'] for l in q['loops']],'smooth':q['smooth']} for q in incident if not all(i in ids for i in q['vertices'])]}
        port['sections'].append(section)
    report['ports'][side]=port
for m in source['materials']:
    nodes={n['name']:n for n in m['nodes']}
    base=next(i['value'] for i in nodes['Mix (Legacy)']['inputs'] if i['index']==1)
    lo=nodes['Color Ramp']['color_ramp'][0]['color']
    shader=nodes['Principled BSDF.001']; inputs={i['name']:i['value'] for i in shader['inputs']}
    samples=[]
    for z in [.04,.12,.16,.2,.275,.35,.6,.67,.74]:
        t=min(1,max(0,z/(.78*.9)))
        samples.append({'worldZ':z,'linearAlbedo':[base[i]*(lo[i]+(1-lo[i])*t) for i in range(3)]+[1]})
    report['materials'][m['name']]={'activeSurface':'Principled BSDF.001','baseLinear':base,'albedoFormula':'baseRGB * lerp((.37,.3848,.407), (1,1,1), clamp(worldZ/(.78*.9),0,1))',
      'samples':samples,'roughness':inputs['Roughness'],'specularIORLevel':inputs['Specular IOR Level'],'metallic':inputs['Metallic'],'IOR':inputs['IOR'],'alpha':inputs['Alpha'],
      'normalField':'No active normal input link; native flat per-face corner normals. Original inactive view-tone/emission branch is bypassed.'}
report['finiteSupport']={'geometricZ0Intersection':[], 'minimumZ':.03999999910593033,
 'lowestFace':{'z':.03999999910593033,'xyPolygon':[[-.5,-.18000000715255737],[.5,-.18000000715255737],[.5,.18000000715255737],[-.5,.18000000715255737]],'area':.36000001430511475},
 'declaredSupportCells':[[0,0]],'occupiedCells':[[0,0]],'sockets':{},
 'interpretation':'Support cell is gameplay occupancy, not a solid full-floor ground footprint. Keep empty z0, root and finite lowest lower-rail patch. Native fullfloor or dropped base would invent ground contact.'}
report['clearanceAndEnvelope']={'hardDerived':'Three finite port patches at x ±.5; original repeat clears neighboring cells because all geometry x is within ±.5 and y -.237...26. Geometry never reaches z0. Endpoint collar x[-.5,-.35] and [.35,.5] is free of ribs/plates, contains only these continuous rail extrusions.',
 'proposedRootFreeze':'Preserve source port profiles, finite lowest lower-rail patch and no geometric z0 contact. Use measured finite source outer convex hull as a conservative outer-envelope proposal (explicit root freeze needed); .78 remains nominal catalog height rather than measured geometry. Interior construction and decoration may change meaningfully inside it. Source part counts, source per-part boxes and blank bays are not automatically functional constraints.',
 'clearanceSamples':[{'x':x,'nativeEmptyBay':{'y':[-.18,.18],'z':[.21,.59]}} for x in [-.4,0,.4]],
 'limits':'Empty bay probes establish the original construction only; they do not lock weak blank areas. No collider mesh or explicit gameplay subcell free-space contract was supplied. The proposed hull is an upper envelope, not a requirement to fill it or a source occupied solid. AABB alone cannot certify unchanged finite contact or port geometry. Editor must use actual mesh-plane/cross-section checks, not infer a volume grant from nominal 1x1x.78.',
 'sourceOuterConvexHull':source['sourceOuterConvexHull']}
dump(OUT/'native-contract-measurements.json',report)

records=json.loads((OUT/'historical-replay/capture-records.json').read_text())
summary={'recipe':'Native4x registered camera, source scene filter_size retained; fixed whole-frame Pillow LANCZOS to2x. No crops/fitting/patches. One all4 historical replay only.', 'directions':{},'software':{'pillow':Image.__version__}}
sheet=Image.new('RGB',(4*192,2*352+80),(86,86,86));draw=ImageDraw.Draw(sheet)
for j,d in enumerate('NESW'):
    raw=OUT/'historical-replay/native'/('static-'+d)/'000.png'; refraw=PRODUCTION/'source/registered/wreck-middle'/('static-'+d)/'source-captures/000.png'
    atlas=PRODUCTION/'sprites/wreck-middle'/('static-'+d+'.png')
    a=Image.open(raw).convert('RGBA'); ref=Image.open(atlas).convert('RGBA')
    sampled=a.resize((384,704),Image.Resampling.LANCZOS)
    dest=OUT/'historical-replay/published'/('static-'+d+'.png');dest.parent.mkdir(exist_ok=True);sampled.save(dest)
    fingerprint=json.loads((refraw.parent.parent/'capture-fingerprint.json').read_text())
    summary['directions'][d]={'rawSHA256':sha(raw),'referenceRawSHA256':fingerprint['sourceFrames'][0]['sha256'],'atlasSHA256':sha(atlas),
      'replayPublishedSHA256':sha(dest),'publishedPNGBytesEqual':dest.read_bytes()==atlas.read_bytes(),
      'nativeReplayVsHistoricalRaw':'Historical raw is referenced by hash in registered fingerprint but PNG is absent from this checkout. Decoded raw equality cannot be tested.',
      'replayPublishedVsOriginalAtlas':metrics(sampled,ref)}
    for row,img in enumerate([ref,sampled]):
        tile=Image.new('RGBA',img.size,(86,86,86,255));tile.alpha_composite(img)
        sheet.paste(tile.convert('RGB').resize((192,352),Image.Resampling.LANCZOS),(j*192,30+row*372))
        draw.text((j*192+8,12+row*372),d+(' original atlas' if row==0 else ' replay LANCZOS'),fill='white')
sheet.save(OUT/'historical-replay/comparison-all4.png')
dump(OUT/'historical-replay/comparison.json',summary)
print(json.dumps(summary,indent=2))
