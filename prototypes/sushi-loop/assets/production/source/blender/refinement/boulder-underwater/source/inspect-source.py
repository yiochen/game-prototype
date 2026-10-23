import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
root=bpy.data.objects['S33 production concept cobalt-crags root']
col=next(c for c in bpy.data.collections if root in list(c.objects))
def mat(m):return [list(r) for r in m]
scene=next(s for s in bpy.data.scenes if col.name in s.collection.children)
bpy.context.window.scene=scene;bpy.context.view_layer.update()
objects=[];points=[]
for o in col.all_objects:
 if o.type=='MESH':
  p=[o.matrix_world@v.co for v in o.data.vertices];points+=p
  objects.append({'name':o.name,'type':o.type,'matrix':mat(o.matrix_world),'bounds':[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]],'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'modifiers':[m.type for m in o.modifiers],'materials':[m.name for m in o.data.materials],'customProperties':dict(o.items())})
obs={'inspectionOrder':'Independent source scene and original/target image inspection, before judge critique/proposals. Frozen criteria embedded in brief was present during source-context read; no review file read.','sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':scene.name,'collection':col.name,'groundRoot':root.name,'rootMatrix':mat(root.matrix_world),'rootEuler':list(root.rotation_euler),'rootProperties':dict(root.items()),'physicalBounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]],'meshCount':len(objects),'meshes':objects,'activeCameraUnrelated':{'name':scene.camera.name,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'matrix':mat(scene.camera.matrix_world)},'images':{'original':'A dominant tall blue polygon column with three smaller surrounding long columns; flat crown, sharp linear shoulders, long dark blank lower planes.','target':'Natural blue crag cluster with dominant broad crown, staggered shoulder rocks, rounded worn edges, varied fracture planes and bright cyan crown accents; target is an aesthetic guide, not registration proof.'},'nativePlan':'Rebuild clustered volumetric stone forms with deliberate asymmetry and worn native bevels, broad geologic facets and controlled blue material variation. Keep registered physical envelope, root, four cardinal rotations and exact camera with native square-footing capture deformation.'}
(base/'initial-observations.json').write_text(json.dumps(obs,indent=2,default=list)+'\n')
print(json.dumps({'scene':scene.name,'collection':col.name,'bounds':obs['physicalBounds'],'meshCount':len(objects),'objects':[x['name'] for x in objects],'rootMatrix':obs['rootMatrix'],'camera':obs['activeCameraUnrelated']},indent=2))
