import bpy,json,runpy,math,hashlib
from pathlib import Path
from mathutils import Vector
ns=runpy.run_path(str(Path(__file__).with_name('audit-approved-human-round04.py')));B=ns['B'];root=ns['root'];col=ns['col'];sc=ns['sc'];rig=ns['rig'];mod=ns['mod']
with bpy.data.libraries.load(str(B/'inputs/paired-native/dock-entry-round-06.blend'),link=False) as(a,b):b.collections=['S33_PROP_dock-entry']
ec=b.collections[0];sc.collection.children.link(ec);ec.hide_viewport=False;ec.hide_render=False;er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0);er.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def points(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices];m.calc_loop_triangles();f=[list(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return v,f
dg=bpy.context.evaluated_depsgraph_get();blocks=[]
for o in ec.all_objects:
 if o.type=='MESH' and any(t in o.name for t in ['__cap_','__post_']):
  vs,_=points(o,dg);blocks.append({'name':o.name,'bounds':[[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]]})
def clip(poly,axis,value,greater):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  dp=(p[axis]-value)*(1 if greater else -1);dq=(q[axis]-value)*(1 if greater else -1);a=dp>=0;b=dq>=0
  if a:out.append(p)
  if a!=b:
   t=dp/(dp-dq);out.append([p[i]+t*(q[i]-p[i]) for i in range(3)])
 return out
path=[[0,-2.1,0],[0,-1.9,.0733333333],[0,-1.75,.1466666667],[0,-1.55,.22],[0,-1.5,.22],[0,-1.3,.22],[.15,-.65,.22],[0,.12,.22],[.78,-.18,.22]];records=[]
for index,p in enumerate(path):
 mod.apply_clip({'root':root,'collection':col},rig,'walk',index+1,'S',sc);root.location=p;root.rotation_euler=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();tris=[];feet=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  vs,fs=points(o,dg);tris.extend([[list(vs[i]) for i in f] for f in fs])
  if any(t in o.name.lower() for t in ['shoe','sole','foot']):feet.append({'name':o.name,'minZ':min(v.z for v in vs),'maxZ':max(v.z for v in vs),'minX':min(v.x for v in vs),'maxX':max(v.x for v in vs)})
 clear=[]
 for b in blocks:
  lo,hi=b['bounds'];xvalues=[]
  for tri in tris:
   if max(v[1] for v in tri)<lo[1] or min(v[1] for v in tri)>hi[1] or max(v[2] for v in tri)<lo[2] or min(v[2] for v in tri)>hi[2]:continue
   q=tri
   for ax,val,g in [(1,lo[1],True),(1,hi[1],False),(2,lo[2],True),(2,hi[2],False)]:
    q=clip(q,ax,val,g) if q else []
   xvalues.extend(v[0] for v in q)
  clearance=None if not xvalues else (lo[0]-max(xvalues) if lo[0]>0 else min(xvalues)-hi[0]);clear.append({'blocker':b['name'],'nativeBounds':b['bounds'],'actorSurfaceCrossSectionX':None if not xvalues else[min(xvalues),max(xvalues)],'conservativeLateralClearance':clearance,'hasNoTriangleInYZSlab':not xvalues})
 records.append({'pathIndex':index,'sourceClip':'walk','sourceFrame':index+1,'sourceCatalogIndex':index,'rootWorld':p,'soleMeshes':feet,'minSoleZRelativeToSupport':min(f['minZ'] for f in feet)-p[2],'postCapCrossSections':clear})
report={'approvedNativeSourceSHA256':hashlib.sha256((B/'source/resources/approved-human-v3/customer-rosa-approved.blend').read_bytes()).hexdigest(),'entrySourceSHA256':hashlib.sha256((B/'inputs/paired-native/dock-entry-round-06.blend').read_bytes()).hexdigest(),'method':'Actual visible approved actor walk geometry at exact same root positions/frames used by primary browser. Native unitworldscale unchanged. Each actual actor triangle clipped to actual post/cap Y/Z slab, then Xextent compared conservatively to native blocker innerbounds. Positive clearance proves no overlap even before rounded blocker corners. No shrink, warp, perview nudge or contact compensation.','projectionScope':'Physical native geometry independent of camera. Legacyb176 stand native55degree render is separateolderreference; primary current35degreepublishedsprite remains unchanged and is not claimed pixelidentical to that legacy render.','records':records};(B/'candidates/round-04/approved-human-contact-clearance.json').write_text(json.dumps(report,indent=2));print('APPROVED_CLEARANCE',[(r['pathIndex'],min([x['conservativeLateralClearance'] for x in r['postCapCrossSections'] if x['conservativeLateralClearance'] is not None],default=None),r['minSoleZRelativeToSupport'])for r in records])
