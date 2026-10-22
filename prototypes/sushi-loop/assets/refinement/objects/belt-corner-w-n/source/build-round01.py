import bpy, math, json, pathlib, hashlib, bmesh
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
RES=P/'source/resources'; OUT=P/'candidates/round-01'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(RES/'approved-family.blend')); s=bpy.context.scene
family=bpy.data.collections['S33_FB_belt-straight-n.001']
with bpy.data.libraries.load(str(RES/'original-library.blend'),link=False) as (a,b):
 b.collections=['S33_FB_belt-corner-w-n.001']; b.actions=['S33_NATIVE__belt-corner-w-n__running__Shader_Nodetree.002']
c=b.collections[0]; s.collection.children.link(c)
for o in c.all_objects: o.hide_render=False; o.hide_viewport=False; o.hide_set(False)
c.hide_render=False; c.hide_viewport=False; s.collection.children.unlink(family)
root=next(o for o in c.objects if '__root.' in o.name); orient=next(o for o in c.objects if '__orientation.' in o.name); deck=next(o for o in c.objects if 'connected_turn_deck' in o.name)
originalUV=[list(x.uv) for x in deck.data.uv_layers.active.data]
originalAnimation=deck.data.materials[0].node_tree.animation_data
originalAction=b.actions[0]
familydeck=next(o for o in family.objects if 'connected_straight_deck' in o.name)
mat=familydeck.data.materials[0].copy(); mat.name='WarmSoft_Corner_OriginalAngularUV_Deck'; mat.node_tree.animation_data_create(); mat.node_tree.animation_data.action=originalAction; mat.node_tree.animation_data.action_slot=originalAction.slots[0]
for tr in mat.node_tree.animation_data.nla_tracks: tr.mute=True
deck.data.materials.clear(); deck.data.materials.append(mat)
rail=bpy.data.materials['WarmSoft_CoralRail'].copy(); rail.name='WarmSoft_CoralRail_CurvedSection'
nt=rail.node_tree; at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name='RailSection'; at.name='Exact_native_rail_cross_section'
for n in list(nt.nodes):
 if n.type=='TEX_COORD':
  for l in list(nt.links):
   if l.from_node==n and l.from_socket.name=='Object': nt.links.new(at.outputs['Vector'],l.to_socket)
for o in [x for x in c.objects if 'stationary_' in x.name and 'rail' in x.name]:
 inside='inside' in o.name; r0,r1=(.02,.15) if inside else (.85,.98); mid=(r0+r1)/2
 vs=[]; fs=[]
 for j in range(49):
  a=math.pi+j*math.pi/96
  for r,z in [(r0,.505),(r1,.505),(r1,.695),(r0,.695)]: vs.append((.5+r*math.cos(a),.5+r*math.sin(a),z))
 for j in range(48):
  for k in range(4): fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
 me=bpy.data.meshes.new('Native_open_quarter_annular_rail'); me.from_pydata(vs,[],[tuple(reversed(f)) for f in fs]); me.update(); o.data=me; me.materials.append(rail)
 a=me.attributes.new('RailSection','FLOAT_VECTOR','POINT')
 for v,d in zip(me.vertices,a.data): d.vector=(math.hypot(v.co.x-.5,v.co.y-.5)-mid,0,v.co.z-.6)
 normals=[]
 for poly in me.polygons:
  poly.use_smooth=True
  for vid in poly.vertices:
   v=me.vertices[vid].co; rad=Vector((v.x-.5,v.y-.5,0)).normalized()
   if poly.index%4==0: n=Vector((0,0,-1))
   elif poly.index%4==2: n=Vector((0,0,1))
   else: n=rad*(1 if poly.index%4==1 else -1)
   normals.append(n)
 me.normals_split_custom_set(normals)
wood=bpy.data.materials['WarmSoft_HoneyWood']; foot=bpy.data.materials['WarmSoft_WoodFoot']; brass=bpy.data.materials['WarmSoft_BrassFastener']
for o in list(c.objects):
 if 'wood_leg' in o.name or 'lower_wood_frame' in o.name: bpy.data.objects.remove(o,do_unlink=True)
def attach(o):
 for cc in list(o.users_collection): cc.objects.unlink(o)
 c.objects.link(o); o.parent=orient; return o
def soften(o,w):
 be=o.modifiers.new('Crafted_soft_edges','BEVEL'); be.width=w; be.segments=4; be.harden_normals=True
 wn=o.modifiers.new('Weighted_surface_normals','WEIGHTED_NORMAL'); wn.keep_sharp=True; return o
def box(name,loc,size,mat,rot=0,bev=.018):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=attach(bpy.context.object); o.name=name; o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.rotation_euler.z=rot; o.data.materials.append(mat); soften(o,bev); return o
vs=[]; fs=[]
for j in range(49):
 a=math.pi+j*math.pi/96
 for r,z in [(.13,.42),(.87,.42),(.87,.54),(.13,.54)]: vs.append((.5+r*math.cos(a),.5+r*math.sin(a),z))
for j in range(48):
 for k in range(4): fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
fs.extend([(3,2,1,0),(192,193,194,195)])
me=bpy.data.meshes.new('Continuous_quarter_turn_bearing'); me.from_pydata(vs,[],fs); me.update(); bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free(); o=bpy.data.objects.new('Crafted_curved_honey_bearing',me); c.objects.link(o); o.parent=orient; me.materials.append(wood); soften(o,.012)
for frac,r in [(.30,.24),(.18,.76),(.70,.24),(.82,.76)]:
 a=math.pi+frac*math.pi/2; x=.5+r*math.cos(a); y=.5+r*math.sin(a)
 width=.15 if r<.5 else .18
 box('Arc_leg_%s'%frac,(x,y,.245),(width,width,.49),wood,a,.021)
 cuff=.16 if r<.5 else .198
 box('Foot_cuff_%s'%frac,(x,y,.04),(cuff,cuff,.08),foot,a,.017)
 for angle in [a,a+math.pi]:
  pos=(x+(width/2+.002)*math.cos(angle),y+(width/2+.002)*math.sin(angle),.34)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=pos); o=attach(bpy.context.object); o.name='Brass_structural_pin'; o.scale=(.010,.021,.021); o.rotation_euler.z=angle; o.data.materials.append(brass)
  for f in o.data.polygons: f.use_smooth=True
s.name='Corner_Registered_Native'; s['asset_id']='belt-corner-w-n'; s['source_project_sha256']='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'; s['authored_child_orientation_radians']=float(orient.rotation_euler.z); s['native_phase_function']='-7*(frame-1)/24'; s['nativeCaptureScale']=2; s['publishedSourceScale']=2
root.rotation_euler.z=0; s.frame_set(1); bpy.context.view_layer.update()
assert originalUV==[list(x.uv) for x in deck.data.uv_layers.active.data]
keep=set(c.all_objects)|set(family.all_objects)|set(s.objects)
for sc in list(bpy.data.scenes):
 if sc!=s: bpy.data.scenes.remove(sc)
for o in list(bpy.data.objects):
 if o not in keep: bpy.data.objects.remove(o,do_unlink=True)
for im in list(bpy.data.images):
 if im.users==0: bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-01.blend'))
recipe={'schemaVersion':1,'asset':'belt-corner-w-n','executable':'source/build-round01.py','nativeProject':'source/round-01.blend','portableInputs':['source/resources/original-library.blend','source/resources/approved-family.blend'],'method':'Direct user authorized recipe reuse; exact source angular deck geometry/UV and original stored action explicitly restored;  approved family camera, shaders, lighting and deterministic native capture. Rails rebuilt as open quarter-annular cross sections with native RailSection attribute in equivalent family section basis. Continuous curved honey bearing, rounded arc legs, foot cuffs and small brass pins. No image textures or raster correction.','nativeCaptureScale':2,'publishedSourceScale':2,'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,248],'nominalFunctionalHeight':.695,'footprint':[1,1]}
(P/'source/recipe-round01.json').write_text(json.dumps(recipe,indent=2))
for d,rot in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=rot; bpy.context.view_layer.update(); s.render.filepath=str(OUT/('initial-'+d+'.png')); bpy.ops.render.render(write_still=True)
print('BUILD_READY',flush=True)
