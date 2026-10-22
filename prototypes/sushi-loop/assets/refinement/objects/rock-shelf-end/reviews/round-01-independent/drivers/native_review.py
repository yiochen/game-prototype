import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parents[1];O=R.parent.parent;C=O/'candidates/round-01'
write=lambda p,v:(R/p).write_text(json.dumps(v,indent=2)+'\n')
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except TypeError:return str(v)
def mat(m):
 rec={'nodes':[],'links':[],'animationData':bool(m.animation_data),'nodeAnimationData':bool(m.node_tree.animation_data)}
 for n in m.node_tree.nodes:
  d={'name':n.name,'type':n.type,'inputs':[(s.identifier,val(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]}
  for k in ['operation','attribute_name','voronoi_dimensions','feature','normalize','interpolation_type','blend_type']:
   if hasattr(n,k):d[k]=getattr(n,k)
  if hasattr(n,'color_ramp'):d['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[(e.position,list(e.color)) for e in n.color_ramp.elements]}
  rec['nodes'].append(d)
 rec['links']=sorted([(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]);return rec
s=bpy.context.scene;root=bpy.data.objects['rock-shelf-end__root'];root.rotation_euler=(0,0,0);coll=root.users_collection[0];coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update();core=bpy.data.objects['rock-shelf-end__rounded_shelf']
cam=s.camera
pts=[];objects=[];actions=[];image_nodes=[];shape=[];bottomedges={};groundarea=0
for ob in coll.all_objects:
 if ob.animation_data:actions.append(ob.name)
 if ob.type!='MESH':continue
 if ob.data.shape_keys:shape.append(ob.name)
 vs=[root.matrix_world.inverted()@ob.matrix_world@v.co for v in ob.data.vertices];pts+=vs
 objects.append({'name':ob.name,'vertices':len(vs),'faces':len(ob.data.polygons),'bounds':[[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]],'modifiers':[m.type for m in ob.modifiers]})
 for mm in ob.data.materials:
  if mm.animation_data or mm.node_tree.animation_data:actions.append(mm.name)
  image_nodes.extend([{'material':mm.name,'image':n.image.name} for n in mm.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])
 for p in ob.data.polygons:
  polygon=[vs[i] for i in p.vertices]
  if all(abs(v.z)<1e-7 for v in polygon):
   groundarea+=abs(sum(polygon[i].x*polygon[(i+1)%len(polygon)].y-polygon[(i+1)%len(polygon)].x*polygon[i].y for i in range(len(polygon)))/2)
   for a,b in zip(polygon,polygon[1:]+polygon[:1]):
    a=tuple(round(v,7) for v in a);b=tuple(round(v,7) for v in b);key=tuple(sorted((a,b)));bottomedges[key]=bottomedges.get(key,0)+1
boundary=[k for k,c in bottomedges.items() if c%2]
def on_perimeter(a,b):return any(abs(a[k]-x)<1e-6 and abs(b[k]-x)<1e-6 for k,x in [(0,-.5),(0,.34),(1,-.45),(1,.45)])
badground=[e for e in boundary if not on_perimeter(*e)]
def band(ob):
 me=ob.data;at=me.color_attributes['rock_shelf_albedo'];res=[]
 for p in me.polygons:
  if all(me.vertices[i].co.x<=-.44+1e-6 for i in p.vertices):
   corners=[{'position':list(me.vertices[me.loops[i].vertex_index].co),'normal':list(me.corner_normals[i].vector),'albedo':list(at.data[me.loops[i].vertex_index].color)} for i in p.loop_indices]
   # Canonical polygon rotation/winding compares by exact spatial corner keys.
   res.append({'faceNormal':list(p.normal),'materialIndex':p.material_index,'smooth':p.use_smooth,'corners':sorted(corners,key=lambda c:c['position'])})
 return sorted(res,key=lambda f:(f['materialIndex'],f['faceNormal'],[c['position'] for c in f['corners']]))
candidateband=band(core);candidate_mats=[mat(m) for m in core.data.materials]
# Independent bounded replay: saved native camera/rig, source meshes untouched.
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};ledger={'singles':{},'assemblies':{}}
def camrec():
 def px(v):
  p=world_to_camera_view(s,cam,Vector(v));return [p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]
 p=px((0,0,0));return {'frame':[s.render.resolution_x,s.render.resolution_y],'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'root':p,'basis':{k:[a-b for a,b in zip(px(v),p)] for k,v in [('X',(1,0,0)),('depth',(0,-1,0)),('height',(0,0,1))]},'cameraMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'filter':s.render.filter_size,'samples':s.eevee.taa_render_samples,'fps':s.render.fps,'nativeFrame':s.frame_current,'rootMatrix':[list(r) for r in root.matrix_world]}
s.frame_set(1)
for d,a in angles.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();ledger['singles'][d]=camrec();s.render.filepath=str(R/f'captures/native/single-{d}-4x.png');bpy.ops.render.render(write_still=True)
root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
with bpy.data.libraries.load(str(R/'resources/canonical-middle03.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('rock-shelf-middle__')]
mc=bpy.data.collections.new('judge-readonly-exact-middle');s.collection.children.link(mc)
for ob in dst.objects:
 if ob:mc.objects.link(ob)
mr=next(o for o in mc.objects if o.type=='EMPTY');mr.rotation_euler=(0,0,0);mr.location=(0,0,0);bpy.context.view_layer.update();middlecore=next(o for o in mc.objects if 'sculpted_core' in o.name)
canonicalband=band(middlecore);canonical_mats=[mat(m) for m in middlecore.data.materials]
assert len(candidateband)==len(canonicalband)==7
# Coordinate/material identity, direct stored custom normal values and point albedo.
parity={'bandFaceCount':7,'coordinatesExact':True,'cornerNormalMax':0,'pointAlbedoMax':0,'materialsExact':candidate_mats[:2]==canonical_mats[:2]}
for a,b in zip(candidateband,canonicalband):
 for ca,cb in zip(a['corners'],b['corners']):
  parity['coordinatesExact']&=ca['position']==cb['position'];parity['cornerNormalMax']=max(parity['cornerNormalMax'],max(abs(x-y) for x,y in zip(ca['normal'],cb['normal'])));parity['pointAlbedoMax']=max(parity['pointAlbedoMax'],max(abs(x-y) for x,y in zip(ca['albedo'],cb['albedo'])))
lights=[{'name':o.name,'type':o.data.type,'shape':o.data.shape,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'shadow':o.data.use_shadow} for o in s.objects if o.type=='LIGHT']
write('measurements/native-audit.json',{'sourceSHA256':hashlib.sha256((R/'resources/round-01.blend').read_bytes()).hexdigest(),'canonicalSHA256':hashlib.sha256((R/'resources/canonical-middle03.blend').read_bytes()).hexdigest(),'objects':objects,'bounds':[[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]],'groundArea':groundarea,'groundBoundaryEdges':boundary,'groundInteriorBoundaryErrors':badground,'upperBeyondX.34':[[v.x,v.y,v.z] for v in pts if v.x>.34001],'actions':actions,'armatures':sum(o.type=='ARMATURE' for o in coll.all_objects),'shapeKeys':shape,'imageNodes':image_nodes,'linkedLibrariesBeforeAppend':[],'staticFrameRange':[s.frame_start,s.frame_end],'lights':lights,'fieldComparison':parity,'candidateBand':candidateband,'canonicalBand':canonicalband,'candidateMaterials':candidate_mats[:2],'canonicalMaterials':canonical_mats[:2],'worldStrength':s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'filmTransparent':s.render.film_transparent})
# Capture-only independent family instances use actual byte-exact sources and authored transforms.
ass=bpy.data.collections.new('judge-capture-only-assemblies');s.collection.children.link(ass)
plan=json.loads((O/'reviews/preparation-v1/evidence-plan.json').read_text())['minimumCandidateNative']['assemblies']
def common_camera():
 s.render.resolution_x=448*4;s.render.resolution_y=608*4;cam.data.ortho_scale=448/128;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def py():return (1-world_to_camera_view(s,cam,Vector((0,0,0))).y)*s.render.resolution_y
 a=py();cam.data.shift_y=1;bpy.context.view_layer.update();cam.data.shift_y=(376*4-a)/(py()-a);bpy.context.view_layer.update()
for d in angles:
 for kind in ['pair','closedRun']:
  for ob in list(ass.objects):bpy.data.objects.remove(ob,do_unlink=True)
  coll.hide_render=True;mc.hide_render=True
  transforms=[]
  for p in plan[d][kind]:
   cc=coll if p['asset']=='candidate-end' else mc;rr=bpy.data.objects.new('judge-instance',None);ass.objects.link(rr);rr.location=p['rootNative'];rr.rotation_euler.z=angles[p['direction']]
   for ob in cc.objects:
    if ob.type!='MESH':continue
    cp=ob.copy();cp.data=ob.data;ass.objects.link(cp);cp.parent=rr;cp.matrix_parent_inverse=Matrix.Identity(4);cp.matrix_basis=ob.matrix_basis.copy()
   transforms.append(p)
  common_camera();ledger['assemblies'][kind+'-'+d]={'camera':camrec(),'instances':transforms};s.render.filepath=str(R/f'captures/native/{kind}-{d}-4x.png');bpy.ops.render.render(write_still=True)
write('measurements/native-capture-ledger.json',ledger)
print('JUDGE INDEPENDENT NATIVE REVIEW COMPLETE '+json.dumps(parity))
