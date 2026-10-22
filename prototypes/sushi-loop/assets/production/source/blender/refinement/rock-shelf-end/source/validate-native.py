import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent;O=B.parent/'candidates/round-01'
bpy.ops.wm.open_mainfile(filepath=str(B/'round-01.blend'))
s=bpy.context.scene;r=bpy.data.objects['rock-shelf-end__root'];coll=r.users_collection[0];c=bpy.data.objects['rock-shelf-end__rounded_shelf'];r.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def field(mesh):
 a=mesh.color_attributes['rock_shelf_albedo'];rows=[]
 for p in mesh.polygons:
  if all(mesh.vertices[i].co.x<=-.44+1e-6 for i in p.vertices):
   rows.append({'normal':list(p.normal),'materialIndex':p.material_index,'smooth':p.use_smooth,'corners':[{'position':list(mesh.vertices[mesh.loops[li].vertex_index].co),'normal':list(mesh.corner_normals[li].vector),'albedo':list(a.data[mesh.loops[li].vertex_index].color)} for li in p.loop_indices]})
 return rows
def key(row):return (row['materialIndex'],tuple(sorted(tuple(round(v,5) for v in a['position']) for a in row['corners'])))
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def mat(m):
 nodes=[]
 for n in m.node_tree.nodes:
  a={'type':n.type,'name':n.name,'inputs':{i.identifier:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}}
  for k in ['attribute_name','operation','interpolation_type','voronoi_dimensions','feature','normalize','blend_type']:
   if hasattr(n,k):a[k]=getattr(n,k)
  if hasattr(n,'color_ramp'):a['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[[e.position,list(e.color)] for e in n.color_ramp.elements]}
  nodes.append(a)
 return {'nodes':nodes,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links]}
cf=field(c.data);cm=[mat(m) for m in c.data.materials];savedSourceLibraries=[l.filepath for l in bpy.data.libraries]
with bpy.data.libraries.load(str(B/'resources/canonical-middle03.blend'),link=False) as (src,dst):dst.meshes=['rock-shelf-middle sculpted continuous low core']
canon=dst.meshes[0];mf=field(canon);mm=[mat(m) for m in canon.materials]
md={key(p):p for p in mf};errors=[]
for pp in cf:
 qq=md.get(key(pp));assert qq,key(pp)
 other={tuple(round(v,5) for v in cc['position']):cc for cc in qq['corners']}
 for cc in pp['corners']:
  oc=other[tuple(round(v,5) for v in cc['position'])]
  errors.append({'position':max(abs(a-b) for a,b in zip(cc['position'],oc['position'])),'normal':max(abs(a-b) for a,b in zip(cc['normal'],oc['normal'])),'albedo':max(abs(a-b) for a,b in zip(cc['albedo'],oc['albedo']))})
pts=[];objects=[];actions=[];images=[]
for ob in coll.objects:
 if ob.animation_data:actions.append(ob.name)
 if ob.type!='MESH':continue
 p=[ob.matrix_world@v.co for v in ob.data.vertices];pts+=p;objects.append({'name':ob.name,'vertices':len(p),'faces':len(ob.data.polygons),'bounds':[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]],'shapeKeys':bool(ob.data.shape_keys),'modifiers':[m.type for m in ob.modifiers]})
 for m in ob.data.materials:
  if m.animation_data or m.node_tree.animation_data:actions.append(m.name)
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':images.append(n.image.name if n.image else None)
# Projected area of every actual planar support face, no inferred cell opacity.
area=0;bottom=[]
for p in c.data.polygons:
 vs=[c.data.vertices[i].co for i in p.vertices]
 if all(abs(v.z)<1e-7 for v in vs):
  aa=abs(sum(vs[i].x*vs[(i+1)%len(vs)].y-vs[(i+1)%len(vs)].x*vs[i].y for i in range(len(vs)))/2);area+=aa;bottom.append(p.index)
lights=[{'name':o.name,'type':o.data.type,'shape':o.data.shape,'position':list(o.location),'rotation':list(o.rotation_euler),'power':o.data.energy,'size':o.data.size,'shadow':o.data.use_shadow,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT']
ledger=json.loads((O/'capture-ledger.json').read_text())
d={'asset':'rock-shelf-end','sourceProjectSHA256':hashlib.sha256((B/'round-01.blend').read_bytes()).hexdigest(),'views':ledger['views'],'objects':objects,'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'finiteGround':{'actualProjectedArea':area,'faceIndices':bottom,'expectedArea':.756,'polygon':[[-.5,-.45],[.34,-.45],[.34,.45],[-.5,.45]]},'upperExtentBeyondGround':[list(v) for v in pts if v.x>.34001],'westField':{'candidate':cf,'canonical':mf,'faceCount':[len(cf),len(mf)],'maxPositionError':max(e['position'] for e in errors),'maxCornerNormalComponentError':max(e['normal'] for e in errors),'maxPointAlbedoError':max(e['albedo'] for e in errors),'materialGraphsEqual':cm==mm,'candidateMaterialGraphs':cm,'canonicalMaterialGraphs':mm,'policy':'actual saved field comparison; 1e-5 representation tolerance only; visual continuity reserved to independent judge'},'lights':lights,'camera':ledger['views']['S'],'static':{'frames':1,'fps':s.render.fps,'loop':False,'frameRange':[s.frame_start,s.frame_end],'actions':actions,'armatures':sum(o.type=='ARMATURE' for o in coll.objects),'imageTextures':images,'libraries':savedSourceLibraries,'comparisonAppendLibraries':[l.filepath for l in bpy.data.libraries]},'noApproval':'Technical measurements only; judge owns aesthetic and seam decision.'}
assert abs(area-.756)<1e-6
assert max(e['normal'] for e in errors)<1e-5
assert cm==mm
assert not actions and not images
assert all(-.50001<=v.x<=.35901 and abs(v.y)<=.45001 and -.00001<=v.z<=.45001 for v in pts)
(O/'native-validation.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:d[k] for k in ['bounds','finiteGround','static']},indent=2));print('WEST',d['westField']['maxCornerNormalComponentError'],cm==mm)
