import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];E=B/'evidence';R=B/'resources'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,default=str)+'\n')
def material(m):
 nt=m.node_tree;nodes=[]
 for n in nt.nodes:
  q={'type':n.type,'name':n.name,'inputs':[(i,s.identifier,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value) for i,s in enumerate(n.inputs) if hasattr(s,'default_value') and s.type in ['VALUE','VECTOR','RGBA','BOOLEAN','INT']]}
  if n.type=='VALTORGB':q['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[(e.position,list(e.color)) for e in n.color_ramp.elements]}
  nodes.append(q)
 return {'nodes':nodes,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links],'animation':bool(m.animation_data) or bool(nt.animation_data)}
def inspect(path,aid):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;r=bpy.data.objects[aid+'__root'];c=bpy.data.collections[aid];r.rotation_euler.z=0;s.frame_set(1)
 for l in s.view_layers[0].layer_collection.children:l.exclude=False;l.hide_viewport=False
 c.hide_render=False;c.hide_viewport=False;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();allpts=[];rows=[];bands={};ground=[];ports={}
 for ob in c.all_objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();m=r.matrix_world.inverted()@ev.matrix_world;nm=m.to_3x3().inverted().transposed();vs=[m@v.co for v in me.vertices];allpts+=vs
  q={'name':ob.name,'parent':ob.parent.name if ob.parent else None,'meshUsers':ob.data.users,'objectAnimation':bool(ob.animation_data),'dataAnimation':bool(ob.data.animation_data),'shapeKeys':bool(ob.data.shape_keys),'bounds':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)],'materialNames':[x.name for x in me.materials],'modifiers':[x.type for x in ob.modifiers]}
  if 'continuous_core' in ob.name:
   ec={}
   for p in me.polygons:
    for edge in p.edge_keys:k=tuple(sorted(edge));ec[k]=ec.get(k,0)+1
   q['edgeIncidenceHistogram']={str(v):list(ec.values()).count(v) for v in set(ec.values())}
   for t in me.loop_triangles:
    ps=[vs[i] for i in t.vertices]
    if all(abs(v.z)<1e-7 for v in ps):ground.append({'vertices':[list(v) for v in ps],'area':(ps[1]-ps[0]).cross(ps[2]-ps[0]).length/2})
   for side,x,sgn in [('W',-.5,-1),('E',.5,1)]:
    ports[side]=[list(v) for v in vs if abs(v.x-x)<1e-6];ts=[]
    for t in me.loop_triangles:
     ps=[vs[i] for i in t.vertices]
     if all(v.x*sgn>=.42-1e-6 for v in ps) and not all(abs(v.x-x)<1e-6 for v in ps):ts.append({'vertices':[list(v) for v in ps],'geometricNormal':list(nm@t.normal),'cornerNormals':[list(nm@me.corner_normals[i].vector) for i in t.loops],'materialName':me.materials[t.material_index].name,'actualNativeMaterial':material(me.materials[t.material_index])})
    bands[side]=ts
  rows.append(q);ev.to_mesh_clear()
 cam=s.camera
 def px(v):p=world_to_camera_view(s,cam,Vector(v));return [p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]
 origin=px((0,0,0));bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND')
 return {'asset':aid,'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'objects':rows,'bounds':[[min(v[k] for v in allpts),max(v[k] for v in allpts)] for k in range(3)],'groundTriangles':ground,'groundArea':sum(q['area'] for q in ground),'ports':ports,'bands':bands,'allMaterials':{m.name:material(m) for m in bpy.data.materials if m.users},'libraries':[x.filepath for x in bpy.data.libraries],'images':[i.name for i in bpy.data.images if i.source=='FILE'],'actions':list(bpy.data.actions.keys()),'lighting':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'],'world':{'color':list(bg.inputs['Color'].default_value),'strength':bg.inputs['Strength'].default_value},'render':{'resolution':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'samples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'engine':s.render.engine,'transparent':s.render.film_transparent,'fps':s.render.fps,'frame':s.frame_current,'frameRange':[s.frame_start,s.frame_end],'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'compositor':s.compositing_node_group.name if s.compositing_node_group else None},'camera':{'matrix':[list(v) for v in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'root':origin,'unit':{k:[p[i]-origin[i] for i in range(2)] for k,p in [('X',px((1,0,0))),('depth',px((0,-1,0))),('height',px((0,0,1)))]}}}
canonical=inspect(R/'canonical-middle02.blend','reef-middle');write(E/'canonical-reopened-audit.json',canonical)
candidate=inspect(R/'candidate.blend','reef-edge');write(E/'candidate-reopened-audit.json',candidate)
checks={'exactFullWBands':canonical['bands']['W']==candidate['bands']['W'],'exactFullEBands':canonical['bands']['E']==candidate['bands']['E'],'exactPortRings':canonical['ports']==candidate['ports'],'exactSharedLights':canonical['lighting']==candidate['lighting'],'exactSharedWorld':canonical['world']==candidate['world'],'exactRender':canonical['render']==candidate['render'],'exactCamera':canonical['camera']==candidate['camera'],'groundArea':abs(candidate['groundArea']-.76)<1e-5,'closedCore':next(o for o in candidate['objects'] if 'continuous_core' in o['name'])['edgeIncidenceHistogram'].keys()=={'2'},'envelope':all(candidate['bounds'][k][0]>=lo-1e-5 and candidate['bounds'][k][1]<=hi+1e-5 for k,lo,hi in [(0,-.5,.5),(1,-.38,.38),(2,0,.68)]),'staticPrivateGeometry':all(not o['objectAnimation'] and not o['dataAnimation'] and not o['shapeKeys'] and o['meshUsers']==1 for o in candidate['objects']),'noImagesLibrariesActions':not(candidate['images'] or candidate['libraries'] or candidate['actions'])}
write(E/'independent-native-findings.json',{'checks':checks,'allPassed':all(checks.values()),'candidatePacketSHA256':'270d330ded27fa71bc0b1484698e5e75ef671ce5d45bde767d66af559a4ad453','blender':bpy.app.version_string,'python':sys.version})
s=bpy.context.scene;root=bpy.data.objects['reef-edge__root'];angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};ledger={'heroes':[],'primary':[]}
for d,a in angles.items():
 root.rotation_euler.z=a;s.frame_set(1);bpy.context.view_layer.update();p=E/('reopened-'+d+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);ledger['heroes'].append({'facing':d,'rootMatrix':[list(row) for row in root.matrix_world],'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
root.rotation_euler.z=0;bpy.context.view_layer.update()
with bpy.data.libraries.load(str(R/'canonical-middle02.blend'),link=False) as (data_from,data_to):data_to.collections=['reef-middle']
original=data_to.collections[0];fixtureRoots=[]
for label,offset in [('left',-1),('right',1)]:
 col=bpy.data.collections.new('judge-fixture-'+label);s.collection.children.link(col);mapping={ob:ob.copy() for ob in original.all_objects}
 for old,ob in mapping.items():col.objects.link(ob);ob.parent=mapping.get(old.parent);ob.name='judge-'+label+'-'+old.name
 rr=next(ob for ob in mapping.values() if ob.type=='EMPTY' and '__root' in ob.name);fixtureRoots.append((offset,rr))
cam=s.camera;s.render.resolution_x=1408;s.render.resolution_y=1728;cam.data.ortho_scale=704/128;cam.data.shift_y=0;cam.data.shift_x=0;bpy.context.view_layer.update()
def px(v):p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(1120-b.y)/dy;bpy.context.view_layer.update()
for d,a in angles.items():
 root.rotation_euler.z=a
 for offset,rr in fixtureRoots:rr.location=(offset*math.cos(a),offset*math.sin(a),0);rr.rotation_euler.z=a
 bpy.context.view_layer.update();p=E/('native-primary-'+d+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 ledger['primary'].append({'facing':d,'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rootPixels':list(px((0,0,0))),'roots':[{'role':'edge','matrix':[list(row) for row in root.matrix_world]}]+[{'role':str(offset),'matrix':[list(row) for row in rr.matrix_world]} for offset,rr in fixtureRoots]})
write(E/'native-replay-ledger.json',ledger);print(json.dumps(checks));print('INDEPENDENT_NATIVE_COMPLETE')
