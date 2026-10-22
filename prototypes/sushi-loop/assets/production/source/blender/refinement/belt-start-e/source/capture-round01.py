import bpy,math,json,pathlib,hashlib,bmesh,sys
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1]; OUT=P/'candidates/round-01'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if args: OUT=pathlib.Path(args[0]).resolve()
for n in ['frames','closure','family-frames','connected','unbroken']: (OUT/n).mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend')); s=bpy.context.scene; s.render.use_persistent_data=False
c=bpy.data.collections['S33_FB_belt-start-e.001']; root=next(o for o in c.objects if '__root.' in o.name); orient=next(o for o in c.objects if '__orientation.' in o.name); deck=next(o for o in c.objects if 'connected_' in o.name); phase=deck.data.materials[0].node_tree.nodes['Value']
rotations={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}; sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def measured_ports():
 uv=deck.data.uv_layers.active;out={}
 for name,U in [('incoming',0),('outgoing',1)]:
  vids=set(deck.data.loops[i].vertex_index for i,x in enumerate(uv.data) if abs(x.uv.x-U)<1e-6);pts=[deck.matrix_world@deck.data.vertices[i].co for i in vids];pt=sum(pts,Vector())/len(pts);normal=Vector((round(pt.x*2),round(pt.y*2),0));out[name]={'point':pt,'tangent':normal*(-1 if name=='incoming' else 1)}
 return out
root.rotation_euler.z=0; bpy.context.view_layer.update();basePorts=measured_ports();basePorts={k:v for k,v in basePorts.items() if k=='outgoing'};moduleSpecs=[]
for name in ['outgoing']:

 pp=basePorts[name];offset=Vector((round(pp['point'].x*2),round(pp['point'].y*2),0));tangent=pp['tangent'];angle=math.atan2(tangent.y,tangent.x)-math.pi/2;moduleSpecs.append((tuple(offset),angle))

def calibration():
 vals={}
 for k,pt in {'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items():
  v=world_to_camera_view(s,s.camera,Vector(pt)); vals[k]=[v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y]
 r=vals['root']; return {'root':r,**{k:[v[0]-r[0],v[1]-r[1]] for k,v in vals.items() if k!='root'}}
def camera(): return {'worldMatrix':[list(r) for r in s.camera.matrix_world],'projectionMatrix':[list(r) for r in s.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'frame':[s.render.resolution_x,s.render.resolution_y],'calibration':calibration()}
def meshes(collection):
 rows=[]; dep=bpy.context.evaluated_depsgraph_get()
 for o in collection.all_objects:
  if o.type!='MESH': continue
  ev=o.evaluated_get(dep); me=ev.to_mesh(); pts=[ev.matrix_world@v.co for v in me.vertices]
  rows.append({'name':o.name,'vertices':len(pts),'polygons':len(me.polygons),'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'matrixWorld':[list(x) for x in ev.matrix_world],'materials':[m.name for m in me.materials],'modifiers':[m.type for m in o.modifiers]}); ev.to_mesh_clear()
 return rows
def profile(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];out={}
 for name,p in basePorts.items():
  pt=p['point'];tan=p['tangent'];vertices=[list(v) for v in pts if abs((v-pt).dot(tan))<1e-6];caps=[f.index for f in me.polygons if all(abs((pts[i]-pt).dot(tan))<1e-6 for i in f.vertices)];out[name]={'vertices':vertices,'capPolygons':caps,'planePoint':list(pt),'travelTangent':list(tan)}
 ev.to_mesh_clear();return out
root.rotation_euler.z=0; s.frame_set(1); bpy.context.view_layer.update(); geo=meshes(c)
bounds=[[min(x['bounds'][0][i] for x in geo) for i in range(3)],[max(x['bounds'][1][i] for x in geo) for i in range(3)]]
val={'schemaVersion':1,'asset':'belt-start-e','project':'source/round-01.blend','projectSHA256':sha(P/'source/round-01.blend'),'blenderVersion':bpy.app.version_string,'camera':camera(),'collection':c.name,'root':root.name,'intrinsicOrientationRadians':orient.rotation_euler.z,'nominalFunctionalHeight':.695,'measuredPhysicalBounds':bounds,'footprint':[1,1],'geometry':geo,'profiles':{o.name:profile(o) for o in c.objects if o==deck or 'stationary_' in o.name},'originalAngularUV':[list(x.uv) for x in deck.data.uv_layers.active.data],'clearance':{'deckHeight':.64,'nativeCapTop':.71939999,'supportMaxZ':.54,'nonDeckNonRailMaxZ':max(x['bounds'][1][2] for x in geo if 'stationary_' not in x['name'] and x['name']!=deck.name)},'frames':[],'ports':{},'dependencyClosure':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'filepath':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images],'portableRecipe':'source/build-round01.py','nativeCaptureScale':2,'publishedSourceScale':2},'render':{'engine':s.render.engine,'samples':s.cycles.samples,'samplingPattern':s.cycles.sampling_pattern,'scramblingDistance':s.cycles.scrambling_distance,'filter':s.cycles.pixel_filter_type,'filterWidth':s.cycles.filter_width,'dither':s.render.dither_intensity,'denoising':s.cycles.use_denoising,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look},'nativeAssemblies':[]}
for d,r in rotations.items():
 root.rotation_euler.z=r; bpy.context.view_layer.update(); ports={}
 for name,pt,tangent in [(name,tuple(p['point']),tuple(p['tangent'])) for name,p in basePorts.items()]+[('deck',(0,0,.64),(0,0,0))]:
  world=root.matrix_world@Vector(pt); q=world_to_camera_view(s,s.camera,world); ports[name]={'world':list(world),'logicalRootRelative':[q.x*192-96,(1-q.y)*352-248],'worldTangent':list(root.matrix_world.to_3x3()@Vector(tangent))}
 val['ports'][d]=ports
 for i in range(25):
  s.frame_set(i+1); bpy.context.view_layer.update(); v=float(phase.outputs[0].default_value); assert abs(v+7*i/24)<1e-5
  path=OUT/('frames' if i<24 else 'closure')/f'running-{d}-{i:02}.png'; s.render.filepath=str(path); bpy.ops.render.render(write_still=True)
  val['frames'].append({'clip':'running','direction':d,'index':i,'blenderFrame':i+1,'path':path.relative_to(OUT).as_posix(),'phase':v,'rootMatrix':[list(x) for x in root.matrix_world],'sha256':sha(path)})
 (OUT/f'hero-{d}.png').write_bytes((OUT/'frames'/f'running-{d}-00.png').read_bytes())
(OUT/'validation.json').write_text(json.dumps(val,indent=2))
# Load an untouched native approved family; obtain independent native frames from it.
c.hide_render=True
with bpy.data.libraries.load(str(P/'source/resources/approved-family.blend'),link=False) as (a,b): b.collections=['S33_FB_belt-straight-n.001']
fam=b.collections[0]; s.collection.children.link(fam); fam.hide_render=False
fr=next(o for o in fam.objects if '__root.' in o.name)
for o in fam.all_objects: o.hide_render=False; o.hide_viewport=False; o.hide_set(False)
for d,r in rotations.items():
 fr.rotation_euler.z=r; fr.location=(0,0,0)
 for i in range(25):
  s.frame_set(i+1); bpy.context.view_layer.update(); path=OUT/'family-frames'/f'running-{d}-{i:02}.png'; s.render.filepath=str(path); bpy.ops.render.render(write_still=True)
# Incoming family straight N at(0,1); outgoing W at(1,0), before shared publisher rotation.
def clone_collection(collection,name):
 co=bpy.data.collections.new(name); s.collection.children.link(co); mapping={}
 for o in collection.all_objects: q=o.copy(); co.objects.link(q); mapping[o]=q
 for o,q in mapping.items(): q.parent=mapping.get(o.parent,o.parent)
 return co,mapping[fr]
fam2,fr2=clone_collection(fam,'Unused_secondary_family');fam2.hide_render=True; c.hide_render=False
def assembly(r):
 root.rotation_euler.z=r; m=Matrix.Rotation(r,3,'Z')
 for rr,(offset,angle) in zip([fr,fr2],moduleSpecs): rr.rotation_euler.z=r+angle; rr.location=m@Vector(offset)
 bpy.context.view_layer.update()
assembly(0)
# Truly unbroken native reference: weld adjoining deck/rail vertices into shared meshes.
# CORNER attributes preserve exact material cross-section coordinates and angular/linear UVs.
originals=[o for co in [c,fam] for o in co.all_objects if o.type=='MESH' and ('stationary_' in o.name or 'connected_' in o.name)]
verts=[]; faces=[]; faceMat=[]; uvs=[]; sections=[]; nativeNormals=[]; deckmat=deck.data.materials[0]; railmat=next(o for o in c.objects if '_cap.' in o.name).data.materials[0]
for o in originals:
 me=o.data; off=len(verts); verts.extend([tuple(o.matrix_world@v.co) for v in me.vertices]); isdeck='connected_' in o.name
 for f in me.polygons:
  faces.append(tuple(off+i for i in f.vertices)); faceMat.append(0 if isdeck else 1)
  for li in f.loop_indices:
   vid=me.loops[li].vertex_index; uv=tuple(me.uv_layers.active.data[li].uv) if isdeck else (0,0); uvs.append(uv)
   if not isdeck:
    attr=me.attributes.get('RailSection'); section=tuple(attr.data[vid].vector) if attr else tuple(me.vertices[vid].co)
   else: section=(0,0,0)
   sections.append(section); nativeNormals.append(tuple((o.matrix_world.to_3x3().inverted().transposed()@me.corner_normals[li].vector).normalized()))
me=bpy.data.meshes.new('Unbroken_welded_3module_rail_and_deck'); me.from_pydata(verts,[],faces); me.update(); me.materials.append(deckmat); me.materials.append(railmat)
uv=me.uv_layers.new(name='Original_per_surface_UV'); attr=me.attributes.new('RailSection','FLOAT_VECTOR','CORNER'); normalAttr=me.attributes.new('NativeNormal','FLOAT_VECTOR','CORNER')
for f,idx in zip(me.polygons,faceMat): f.material_index=idx
for i in range(len(me.loops)): uv.data[i].uv=uvs[i]; attr.data[i].vector=sections[i]; normalAttr.data[i].vector=nativeNormals[i]
before=len(me.vertices); bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bm.to_mesh(me); bm.free(); me.update()
for poly in me.polygons: poly.use_smooth=True
me.normals_split_custom_set([x.vector for x in me.attributes['NativeNormal'].data])
unbroken=bpy.data.objects.new('True_unbroken_welded_native_reference',me); s.collection.objects.link(unbroken); unbroken.hide_render=True
val['unbrokenReference']={'beforeVertices':before,'afterWeldVertices':len(me.vertices),'verticesWelded':before-len(me.vertices),'method':'Canonical native source meshes transformed to world, identical deck/section materials with per-corner original UV and cross-section attributes; matching boundary vertices welded. Shared reference is independently rendered; no raster reuse.'}
s.render.resolution_x=896; s.render.resolution_y=1216; s.camera.data.ortho_scale*=1216/704; s.camera.data.shift_y*=704/1216
names={'c':c.name,'fam':fam.name,'fam2':fam2.name,'root':root.name,'fr':fr.name,'fr2':fr2.name,'unbroken':unbroken.name,'originals':[o.name for o in originals],'deckmat':deckmat.name}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assembly-source.blend')); bpy.ops.wm.open_mainfile(filepath=str(OUT/'assembly-source.blend')); s=bpy.context.scene
c=bpy.data.collections[names['c']]; fam=bpy.data.collections[names['fam']]; fam2=bpy.data.collections[names['fam2']]; root=bpy.data.objects[names['root']]; fr=bpy.data.objects[names['fr']]; fr2=bpy.data.objects[names['fr2']]; unbroken=bpy.data.objects[names['unbroken']]; originals=[bpy.data.objects[n] for n in names['originals']]; phase=bpy.data.materials[names['deckmat']].node_tree.nodes['Value']
val['assemblyCamera']=camera(); val['assemblyContract']={'frame':[896,1216],'root':[448,752],'cellPitchPixels':256,'canonicalOffsets':[[0,0,0]]+[list(x[0]) for x in moduleSpecs],'familyRelativeRotations':[math.degrees(x[1]) for x in moduleSpecs]}
for d,r in rotations.items():
 assembly(r); unbroken.rotation_euler.z=r
 for i in range(25):
  s.frame_set(i+1); bpy.context.view_layer.update(); matrices=[[list(x) for x in rr.matrix_world] for rr in [root,fr,fr2]]
  for o in originals: o.hide_render=False
  unbroken.hide_render=True; path=OUT/'connected'/f'running-{d}-{i:02}.png'; s.render.filepath=str(path); bpy.ops.render.render(write_still=True)
  for o in originals: o.hide_render=True
  unbroken.hide_render=False; unbroken.hide_set(False); unbroken.update_tag(); bpy.context.view_layer.update(); upath=OUT/'unbroken'/f'running-{d}-{i:02}.png'; s.render.filepath=str(upath); bpy.ops.render.render(write_still=True)
  val['nativeAssemblies'].append({'direction':d,'index':i,'phase':float(phase.outputs[0].default_value),'rootMatrices':matrices,'connectedSHA256':sha(path),'unbrokenSHA256':sha(upath)})
  print('ASSEMBLY',d,i,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assembly-diagnostic.blend')); (OUT/'validation.json').write_text(json.dumps(val,indent=2)); print('CAPTURE_READY',flush=True)
