import sys
sys.dont_write_bytecode=True
import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent;EXP=BASE.parent;OUT=EXP/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'resources/canonical-middle03.blend'))
s=bpy.context.scene;s.name='rock-shelf-end rounded finished termination round01'
root=bpy.data.objects['rock-shelf-middle__root'];root.name='rock-shelf-end__root';coll=root.users_collection[0];coll.name='rock-shelf-end native finite shelf'
core=bpy.data.objects['rock-shelf-middle__sculpted_core'];core.name='rock-shelf-end__rounded_shelf';mesh=core.data
# Captured actual west cap/band field, not reconstructed IDs/names.
oldnorm={};oldraw={}
for p in mesh.polygons:
 for li in p.loop_indices:
  co=mesh.vertices[mesh.loops[li].vertex_index].co
  key=(tuple(round(v,6) for v in co),p.material_index,tuple(round(v,5) for v in p.normal))
  oldnorm[key]=tuple(mesh.corner_normals[li].vector);oldraw[key]=tuple(mesh.attributes['custom_normal'].data[li].value)
oldbypos={}
for (pos,mat,no),value in oldnorm.items():oldbypos.setdefault((tuple(round(v,4) for v in pos),mat),[]).append((Vector(no),Vector(value)))
for ob in list(coll.objects):
 if ob.type=='MESH' and ob!=core:bpy.data.objects.remove(ob,do_unlink=True)
# Inset finite end reach while the complete normative W[-.5,-.44] band remains untouched.
for v in mesh.vertices:
 if v.co.x>-.42:v.co.x=-.42+(v.co.x+.42)*(.76/.92)
mesh.update()
# Bevel only the exposed upper E boundary. Bottom contact and W band are untouched.
bm=bmesh.new();bm.from_mesh(mesh)
for e in list(bm.edges):
 if all(abs(v.co.x-.34)<1e-5 and abs(abs(v.co.y)-.45)<1e-5 for v in e.verts) and min(v.co.z for v in e.verts)<1e-6 and max(v.co.z for v in e.verts)>.279:
  low=min(e.verts,key=lambda v:v.co.z);bmesh.utils.edge_split(e,low,.04/.28)
edges=[e for e in bm.edges if all(abs(v.co.x-.34)<1e-5 for v in e.verts) and min(v.co.z for v in e.verts)>=.0399]
assert len(edges)==5,len(edges)
res=bmesh.ops.bevel(bm,geom=edges,offset=.085,segments=7,affect='EDGES',clamp_overlap=True,loop_slide=True,profile=.5)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
bm.to_mesh(mesh);bm.free();mesh.update()
# Area-weighted turning normals. Exact actual W field wins over local smoothing.
acc=[Vector((0,0,0)) for v in mesh.vertices]
for p in mesh.polygons:
 # Keep exposed planar E field from averaging into broad crown.
 if p.normal.x>.999 and all(abs(mesh.vertices[vi].co.x-.34)<1e-5 for vi in p.vertices):continue
 if p.normal.z<-.9:continue
 for vi in p.vertices:acc[vi]+=p.normal*p.area
norms=[];preserved=0
for p in mesh.polygons:
 p.use_smooth=not (all(abs(mesh.vertices[v].co.x+.5)<1e-6 for v in p.vertices))
 for li in p.loop_indices:
  vi=mesh.loops[li].vertex_index;co=mesh.vertices[vi].co
  key=(tuple(round(v,6) for v in co),p.material_index,tuple(round(v,5) for v in p.normal))
  if co.x<=-.44+1e-6:
   n=oldnorm.get(key)
   if n is None:
    # Face geometric normal may differ harmlessly through polygon recalc; use actual band corner by position/material.
    choices=[value for (pos,mat,no),value in oldnorm.items() if pos==key[0] and mat==p.material_index and (Vector(no)-p.normal).length<.1]
    assert choices,(key,p.index);n=choices[0]
   preserved+=1
  elif p.normal.z<-.9:n=(0,0,-1)
  elif p.normal.x>.999 and all(abs(mesh.vertices[v].co.x-.34)<1e-5 for v in p.vertices):n=(1,0,0)
  else:
   # Unchanged native vertices use the saved authored normal transformed by X compression.
   ox=co.x if co.x<=-.42 else -.42+(co.x+.42)/(.76/.92)
   pos=(round(ox,4),round(co.y,4),round(co.z,4))
   choices=oldbypos.get((pos,p.material_index),[])
   if choices:
    oldface,originalnn=min(choices,key=lambda item:(Vector((item[0].x/(.76/.92),item[0].y,item[0].z)).normalized()-p.normal).length)
    nn=originalnn.copy()
    if co.x>-.42:nn.x/=(.76/.92)
    n=tuple(nn.normalized())
   else:n=tuple(acc[vi].normalized() if acc[vi].length else p.normal)
  norms.append(n)
mesh.normals_split_custom_set(norms)
# Preserve the normative packed-short normal bytes in the unchanged west band.
# Decoding/re-encoding adds an avoidable ~5e-5 angular quantization; copied bytes retain exact field.
for p in mesh.polygons:
 for li in p.loop_indices:
  co=mesh.vertices[mesh.loops[li].vertex_index].co
  if co.x<=-.44+1e-6:
   key=(tuple(round(v,6) for v in co),p.material_index,tuple(round(v,5) for v in p.normal))
   mesh.attributes['custom_normal'].data[li].value=oldraw[key]
mesh.update()
# Purposeful embedded pebble pair near finite closed end, substantial at use size.
def pebble(name,loc,scale,color):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=28,ring_count=16,radius=1,location=loc)
 o=bpy.context.object;o.name='rock-shelf-end__'+name
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for v in o.data.vertices:v.co.z=min(v.co.z,.449-loc[2])
 for p in o.data.polygons:p.use_smooth=True
 m=bpy.data.materials.new(name+' lavender-blue native stone');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.38;bs.inputs['Specular IOR Level'].default_value=.25;bs.inputs['Coat Weight'].default_value=.08;o.data.materials.append(m)
 return o
# Rest directly inside the existing fitted top trough; embedded rather than floating.
pebble('embedded_lavender_stone',(-.03,.07,.365),(.054,.047,.041),(.19,.30,.55))
pebble('embedded_teal_stone',(.055,-.015,.348),(.033,.031,.030),(.10,.36,.48))
root['asset']='rock-shelf-end';root['asset_id']='rock-shelf-end';root['ports']=json.dumps([{'direction':'W','position':[-.5,0,0],'profile':'rock-shelf-section-v1','normal':[-1,0,0]}]);root['clip']='static';root['frames']=1;root['fps']=12;root['loop']=False;root.rotation_euler=(0,0,0);root.location=(0,0,0)
s['asset']='rock-shelf-end';s['publication']='native filter0.5; uniform whole-frame BOX4x-to2x';s['static']=True;s['loop']=False
# Remove inherited embedded build text. Scene is self contained, no external images.
for t in list(bpy.data.texts):bpy.data.texts.remove(t)
t=bpy.data.texts.new('build-round-01.py');t.write(Path(__file__).read_text())
# Retain exact saved normative 5light, compositor and single camera.
s.render.filter_size=.5;s.render.fps=12;s.frame_start=s.frame_end=1;s.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'round-01.blend'),compress=True)
(OUT/'build-measurements.json').write_text(json.dumps({'westPreservedCornerCount':preserved,'beveledUpperEndEdges':len(edges),'bevelWidth':.085,'bevelSegments':7,'ground':'unchanged finite rectangle X[-.5,.34] Y±.45 Z0','canonicalSHA256':hashlib.sha256((BASE/'resources/canonical-middle03.blend').read_bytes()).hexdigest()},indent=2))
s.render.filepath=str(OUT/'working-S.png');bpy.ops.render.render(write_still=True)
