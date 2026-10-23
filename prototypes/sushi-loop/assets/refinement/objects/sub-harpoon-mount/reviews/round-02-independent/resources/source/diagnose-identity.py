"""Reopen-only native capture, resource identity, finite-surface and main context audit.
No authoring builder imports. All output stays within this object.
"""
import bpy,json,pathlib,math,sys,hashlib
sys.dont_write_bytecode=True
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent;E=P.parent.parent;C=E/'candidates/round-02';C.mkdir(exist_ok=True)
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
contract=json.loads((E/'inputs/root-native-contract.json').read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x):pathlib.Path(p).write_text(json.dumps(x,indent=2)+'\n')
def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [val(v) for v in x]
 except:return str(x)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def matrix(x):return [list(r) for r in x]
def matrec(m):
 return {'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'identifier':i.identifier,'value':val(getattr(i,'default_value',None))} for i in n.inputs]} for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.identifier,'toNode':l.to_node.name,'toSocket':l.to_socket.identifier} for l in m.node_tree.links]}
def resource(o):
 d=o.data;d.calc_loop_triangles()
 return {'object':o.name,'mesh':d.name,'vertices':[list(v.co) for v in d.vertices],'vertexNormals':[list(v.normal) for v in d.vertices],'cornerNormals':[list(n.vector) for n in d.corner_normals],'polygons':[{'vertices':list(f.vertices),'material':f.material_index,'smooth':f.use_smooth,'normal':list(f.normal)} for f in d.polygons],'uvLayers':[{'name':u.name,'data':[list(v.uv) for v in u.data]} for u in d.uv_layers],'materials':[matrec(m) for m in d.materials if m],'matrixLocal':matrix(o.matrix_local),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
def surf(o):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];normals=[list((eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()) for f in me.polygons];eo.to_mesh_clear();return vs,fs,normals
def tree(surface):return BVHTree.FromPolygons(surface[0],surface[1],all_triangles=False,epsilon=0)
def bounds(v):return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
def rootrec(sc,root,clip,d,f,path):
 q=world_to_camera_view(sc,sc.camera,root.matrix_world.translation)
 return {'clip':clip,'direction':d,'index':f-1,'sourceFrame':f,'path':str(path.relative_to(E)),'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':matrix(root.matrix_world),'projectedRootPixels':[q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y],'nativeSize':[sc.render.resolution_x,sc.render.resolution_y]}

canonical=json.loads((C/'canonical-neutral-resources.json').read_text())['objects']
bpy.ops.wm.open_mainfile(filepath=str(P/'resources/frozen-main-v1/project.blend'))
sc=bpy.context.scene
with bpy.data.libraries.load(str(P/'project.blend'),link=False) as (src,dst):dst.collections=['CANONICAL__sub-harpoon-mount']
c=bpy.data.collections['CANONICAL__sub-harpoon-mount'];sc.collection.children.link(c);root=bpy.data.objects['harpoon__root'];root.parent=bpy.data.objects['MOUNT__sub-harpoon-mount'];root.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
after=[resource(o) for o in sorted(c.all_objects,key=lambda o:o.name) if o.type=='MESH']
def diff(a,b,path=''):
 if type(a)!=type(b):return [(path,str(a),str(b))]
 if isinstance(a,dict):return sum([diff(a[k],b.get(k),path+'/'+k) for k in a],[])
 if isinstance(a,list):return sum([diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))],[]) if len(a)==len(b) else [(path,'length'+str(len(a)),'length'+str(len(b)))]
 return [] if a==b else [(path,a,b)]
r=diff(canonical,after);dump(C/'identity-diagnostic.json',{'diffCount':len(r),'diffs':r[:100]});print(json.dumps(r[:25]))
