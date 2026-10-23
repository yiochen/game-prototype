import bpy,sys,math,json,hashlib,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;BASE=RES.parent;EXP=BASE.parent;OUT=EXP/'candidates/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-02.blend'));s=bpy.context.scene;cam=s.camera
root=bpy.data.objects['rock-shelf-corner__root'];coll=root.users_collection[0];core=next(o for o in coll.objects if o.type=='MESH' and 'continuous' in o.name)
bpy.context.view_layer.update();coords=[o.matrix_world@v.co for o in coll.objects if o.type=='MESH' for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
bounds=[[min(p[i] for p in coords) for i in range(3)],[max(p[i] for p in coords) for i in range(3)]]
bm=bmesh.new();bm.from_mesh(core.data);topology={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'wireEdges':sum(e.is_wire for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces)};bm.free()
ground_faces=[]
for p in core.data.polygons:
 if all(abs(core.data.vertices[i].co.z)<1e-7 for i in p.vertices):ground_faces.append({'polygon':p.index,'area':p.area,'vertices':[[float(c) for c in core.data.vertices[i].co] for i in p.vertices]})
asset={'id':'rock-shelf-corner','projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'scale':2,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True}},'footprint':[1,1],'height':.45,'sockets':{},'ports':[{'direction':'W','position':[-.5,0,0],'normal':[-1,0,0],'profile':'rock-shelf-section-v1'},{'direction':'N','position':[0,.5,0],'normal':[0,1,0],'profile':'rock-shelf-section-v1'}],'nonblocking':False,'depth_layer':'world','directions':['N','E','S','W']}
dump(OUT/'assetRecord.json',asset)
rig={'asset':'rock-shelf-corner','root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'static':True,'frameStart':s.frame_start,'frameEnd':s.frame_end,'fps':s.render.fps,'armatures':[],'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixLocal':[list(r) for r in o.matrix_local],'actions':bool(o.animation_data and o.animation_data.action),'shapeKeys':bool(o.type=='MESH' and o.data.shape_keys)} for o in coll.objects],'lights':[{'name':o.name,'type':o.data.type,'power':o.data.energy,'size':o.data.size,'shape':o.data.shape,'position':list(o.location),'rotation':list(o.rotation_euler),'shadow':o.data.use_shadow} for o in s.objects if o.type=='LIGHT']}
dump(OUT/'rig.json',rig)
# Frozen canonical source is appended only for actual family evidence.
with bpy.data.libraries.load(str(BASE/'dependencies/canonical-middle.blend'),link=False) as (data_from,data_to):data_to.collections=[n for n in data_from.collections if n=='rock-shelf-middle canonical LOW shelf']
midcoll=data_to.collections[0];s.collection.children.link(midcoll);midroot=next(o for o in midcoll.objects if o.type=='EMPTY');midmeshes=[o for o in midcoll.objects if o.type=='MESH'];midcore=next(o for o in midmeshes if 'sculpted_core' in o.name)
# Compare actual frozen/candidate point and face-corner fields on six true cap vertices.
port={};m=core.data;ca=m.color_attributes['rock_shelf_albedo'];ref=midcore.data;ra=ref.color_attributes['rock_shelf_albedo']
for name,axis,plane,side in [('W',0,-.5,-.5),('N',1,.5,.5)]:
 samples=[]
 for p in m.polygons:
  if not all(abs(m.vertices[i].co[axis]-plane)<1e-6 for i in p.vertices):continue
  for li in p.loop_indices:
   vi=m.loops[li].vertex_index;pos=m.vertices[vi].co;rp=Vector((side,pos.y,pos.z)) if name=='W' else Vector((side,-pos.x,pos.z));best=min(ref.vertices,key=lambda v:(v.co-rp).length);ps=(best.co-rp).length
   candidates=[(pp,ll) for pp in ref.polygons for ll in pp.loop_indices if ref.loops[ll].vertex_index==best.index and pp.material_index==1]
   pp,ll=candidates[0];rn=ref.corner_normals[ll].vector;rn=rn if name=='W' else Vector((-rn.y,rn.x,rn.z));samples.append({'position':list(pos),'referenceCanonical':list(rp),'positionError':ps,'normalError':(m.corner_normals[li].vector-rn).length,'albedoError':max(abs(ca.data[vi].color[k]-ra.data[best.index].color[k]) for k in range(4))})
 port[name]={'capFaceCount':len([p for p in m.polygons if all(abs(m.vertices[i].co[axis]-plane)<1e-6 for i in p.vertices)]),'capVertices':len(samples),'samples':samples,'maxPositionError':max(x['positionError'] for x in samples),'maxNormalError':max(x['normalError'] for x in samples),'maxPointAlbedoError':max(x['albedoError'] for x in samples)}
validation={'asset':'rock-shelf-corner','round':'round-02','sourceSHA256':sha(BASE/'round-02.blend'),'canonicalSourceSHA256':sha(BASE/'dependencies/canonical-middle.blend'),'briefSHA256':sha(EXP/'brief.json'),'contractSHA256':sha(EXP/'inputs/root-native-contract.json'),'bounds':bounds,'allowedBounds':[[-.5,-.45,0],[.45,.5,.45]],'groundFaces':ground_faces,'groundArea':sum(p['area'] for p in ground_faces),'expectedGroundArea':.8077386037326075,'topology':topology,'ports':port,'materialFieldEvidence':'cap-field-results.json; actual source cap shader albedo/bump normal captures, true N Object transverse=-localX','nativeValidation':'candidates/round-02/pose-ledger.json','views':json.loads((OUT/'pose-ledger.json').read_text())['views'],'limitations':['Finite-area centered singles versus translated assembly have a broad finite-light residual. Numerical bounds do not waive visible seams.','Review scoped to asset-native and browser consumer fixtures; independent judge approval pending.']}
dump(OUT/'validation.json',validation)
print('TOPOLOGY',topology,'BOUNDS',bounds,'GROUND',validation['groundArea'],flush=True)

def camera(frame=(192,352),anchor=(96,248),scale=4):
 s.render.resolution_x=frame[0]*scale;s.render.resolution_y=frame[1]*scale;s.render.resolution_percentage=100;s.render.pixel_aspect_x=math.sqrt(1+.7*.7);s.render.pixel_aspect_y=1;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
 return {'frame':list(frame),'anchor':list(anchor),'captureScale':scale,'nativeFrame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'fps':12,'camera':{'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world]},'filterSize':s.render.filter_size,'calibration':{'root':list(px((0,0,0))),'unitX':list(px((1,0,0))-px((0,0,0))),'unitDepth':list(px((0,-1,0))-px((0,0,0))),'unitHeight':list(px((0,0,1))-px((0,0,0)))}}
def render(path):path.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};ledger=[]
coll.hide_render=True;midcoll.hide_render=False
for d,a in angles.items():
 midroot.rotation_euler.z=a;bpy.context.view_layer.update();rec=camera();rec.update(kind='canonical-single',direction=d,rootRotationZ=float(midroot.rotation_euler.z),rootMatrix=[list(r) for r in midroot.matrix_world]);ledger.append(rec);render(OUT/f'evidence/canonical/native-{d}.png')
midcoll.hide_render=True;coll.hide_render=False
# Saved-source all4 recapture proves source bytes produce candidate native captures.
for d,a in angles.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();camera();render(OUT/f'evidence/recapture/native-{d}.png')
root.rotation_euler.z=0;bpy.context.view_layer.update();rec=camera();dump(OUT/'native-camera.json',rec);pub=json.loads(json.dumps(rec));pub.update(captureScale=2,nativeFrame=[768,1408],publishedFrame=[384,704],rawCaptureScale=4,publishedSourceScale=2,publication='native4x whole-frame BOX to sourceScale2',rawCamera='candidates/round-02/native-camera.json');pub['calibration']={k:[v/2 for v in vals] for k,vals in rec['calibration'].items()};dump(OUT/'published-camera.json',pub)
# Actual L and isolated W/N joins. Canonical objects are copied with native local
# coordinates intact; translations belong to roots and no tile overlap is added.
assembly=bpy.data.collections.new('capture_only_true_corner_family');s.collection.children.link(assembly);ar=bpy.data.objects.new('capture_only_family_root',None);assembly.objects.link(ar)
branches={}
for branch,position,angle in [('W',(-1,0,0),0),('N',(0,1,0),math.pi/2)]:
 br=bpy.data.objects.new('capture_only_'+branch+'_middle',None);assembly.objects.link(br);br.parent=ar;br.location=position;br.rotation_euler.z=angle;branches[branch]=[]
 for original in midmeshes:
  ob=original.copy();ob.data=original.data;assembly.objects.link(ob);ob.parent=br;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=original.matrix_basis.copy();branches[branch].append(ob)
root.parent=ar
for mode in ['L','W','N']:
 for br,objects in branches.items():
  for ob in objects:ob.hide_render=mode not in ['L',br]
 for d,a in angles.items():
  ar.rotation_euler.z=a;bpy.context.view_layer.update();rec=camera((448,608),(224,376));rec.update(kind='native-family',fixture=mode,direction=d,rootRotationZ=float(ar.rotation_euler.z),rootMatrix=[list(r) for r in ar.matrix_world],branches={br:{'matrixWorld':[list(r) for r in objects[0].parent.matrix_world],'visible':not objects[0].hide_render} for br,objects in branches.items()});ledger.append(rec);render(OUT/f'evidence/family/native-{mode}-{d}.png')
dump(OUT/'evidence/capture-ledger.json',ledger)
print('NATIVE EVIDENCE COMPLETE',flush=True)
