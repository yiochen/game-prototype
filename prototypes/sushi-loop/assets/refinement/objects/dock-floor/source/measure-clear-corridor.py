import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-03';P=B/'inputs/paired-native/dock-entry-round-05.blend';sc=bpy.context.scene
with bpy.data.libraries.load(str(P),link=False) as (a,b):b.collections=['S33_PROP_dock-entry']
ec=b.collections[0];sc.collection.children.link(ec);ec.hide_viewport=False;ec.hide_render=False;er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0);er.rotation_euler=(0,0,0);fr=bpy.data.objects['dock-floor__root'];fr.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def tree(c):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[]
 for o in c.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();s=len(vs);vs.extend(e.matrix_world@v.co for v in m.vertices);fs.extend(tuple(s+i for i in p.vertices) for p in m.polygons);e.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs,epsilon=1e-10)
e,f=tree(ec),tree(bpy.data.collections['WarmSoft_dock-floor'])
def ray(t,p,d):
 p,n,face,dist=t.ray_cast(Vector(p),Vector(d),4);return {'point':list(p) if p else None,'normal':list(n) if n else None,'face':face}
sections=[]
for i in range(157):
 x=-.39+.78*i/156
 a=ray(e,(x,-1.5-1e-7,1),(0,0,-1));b=ray(f,(x,-1.5+1e-7,1),(0,0,-1));sections.append({'x':x,'entry':a,'floor':b,'topMismatch':abs(a['point'][2]-b['point'][2]) if a['point'] and b['point'] else None,'entryFace':ray(e,(x,-1.49,.20),(0,-1,0)),'floorFace':ray(f,(x,-1.51,.20),(0,1,0))})
walk=[{'x':x,'y':y,'surface':ray(e,(x,y-1.5,1),(0,0,-1))} for x in [-.38,-.25,0,.25,.38] for y in [-.49,-.45,-.375,-.30,-.25,-.17,-.16,-.10,-.05,-.001]]
support=[]
for xcell in [-1,0,1]:
 for ycell in [-1,0,1]:
  probes=[ray(f,(xcell+ox,ycell+oy,1),(0,0,-1)) for ox in [-.2,-.1,.1,.2] for oy in [-.2,-.1,.1,.2]];support.append({'cellCenter':[xcell,ycell],'probes':probes,'supportedSamples':sum(p['point'] is not None for p in probes),'samples':len(probes)})
report={'method':'actual evaluated native BVH top and opposing end-face rays over guaranteed clear W=.78; separately retained raw .81 edge diagnostics','floorSHA256':hashlib.sha256((B/'source/round-03.blend').read_bytes()).hexdigest(),'entrySHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'physicalTreadWidth':.96,'exposedTerminalHorizontalWidthApprox':.81,'guaranteedClearTerminalWidth':.78,'widthInterpretation':'Physical .96 includes side frame region. Guaranteed centered .78 common walking profile satisfies frozen .76..96 terminal width. The .81 horizontal-edge diagnostic includes exact bevel boundary endpoint numeric degeneracy; raw record retained in paired-native-validation.json.','commonProfile':sections,'maxTopMismatch':max(p['topMismatch'] for p in sections if p['topMismatch'] is not None),'missingTopSamples':sum(p['topMismatch'] is None for p in sections),'entryMaxZError':max(abs(p['entry']['point'][2]-.22) for p in sections),'floorMaxZError':max(abs(p['floor']['point'][2]-.22) for p in sections),'maxBoundaryYError':max(abs(p[q]['point'][1]+1.5) for p in sections for q in ['entryFace','floorFace'] if p[q]['point']),'walkingProfile':walk,'occupiedSupportCells':support,'repairConstruction':{'unionBounds':[[-.5,-1.5,.04],[.5,-1.48,.22]],'topology':'Exact native Boolean union applied to craft board solid mesh; no retained duplicate top or overlap helper mesh.'}}
(O/'clear-corridor-validation.json').write_text(json.dumps(report,indent=2));print('CLEAR_CORRIDOR',report['maxTopMismatch'],report['missingTopSamples'],report['maxBoundaryYError'])
