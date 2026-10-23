import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent
# Reuse only own source loading/action assignment; avoid rerunning or replacing completed extraction.
code=(R/'extract-native.py').read_text().split('for d,a in ')[0];exec(compile(code,str(R/'extract-native.py'),'exec'),globals())
for ob,p in [(fr,(0,0,0)),(er,(0,-1.5,0))]:ob.rotation_euler=(0,0,0);ob.location=p
snapshots={};parity=[]
for aid,q in list(comp.items())+[('approvedHut',{'collection':ah})]:
 col=q['collection'];dst=bpy.data.collections.new('OWN_STATIC_'+aid);sc.collection.children.link(dst);wrap=bpy.data.objects.new('OWN_STATIC_ROOT_'+aid,None);dst.objects.link(wrap);dg=bpy.context.evaluated_depsgraph_get();rows=[]
 for ob in col.all_objects:
  if ob.type!='MESH'or ob.hide_render:continue
  ev=ob.evaluated_get(dg);em=ev.to_mesh();v=[tuple(ev.matrix_world@p.co)for p in em.vertices];ev.to_mesh_clear();mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg);cp=bpy.data.objects.new('OWN_'+ob.name,mesh);dst.objects.link(cp);cp.parent=wrap;cp.matrix_world=ev.matrix_world.copy()
  for i,mat in enumerate(mesh.materials):
   if mat:
    m=mat.copy();m.animation_data_clear()
    if m.use_nodes:m.node_tree.animation_data_clear()
    mesh.materials[i]=m
  after=[tuple(cp.matrix_world@p.co)for p in mesh.vertices];err=max((Vector(a)-Vector(b)).length for a,b in zip(v,after));assert err<1e-9;rows.append({'source':ob.name,'vertices':len(v),'maxWorldVertexError':err})
 col.hide_render=True;snapshots[aid]={'root':wrap,'collection':dst};parity.append({'id':aid,'objects':rows})
sc.render.resolution_x=1792;sc.render.resolution_y=1792;cam=sc.camera;cam.data.ortho_scale=7;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*896,(1-p.y)*896))
p0=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-p0.y;cam.data.shift_y=(512-p0.y)/dy;bpy.context.view_layer.update();renders=[];out=R/'native-replay';out.mkdir(exist_ok=True)
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 rot=Matrix.Rotation(a,3,'Z');fr.rotation_euler.z=a;er.rotation_euler.z=a;er.location=rot@Vector((0,-1.5,0))
 for q in snapshots.values():q['root'].rotation_euler.z=a
 for cid,fixture in [('first-tread','current-b176'),('transfer','current-b176'),('exterior-stop','current-b176'),('exterior-stop','approved-hut01')]:
  case=next(c for c in plan['cases']if c['id']==cid);assign(hc,rig,case['actorClip'],case['nativeFrame']);hr.location=rot@Vector((*case['sourceFacingXY'],case['solvedRootZ']));hr.rotation_euler.z=a
  snapshots['hut']['collection'].hide_render=fixture!='current-b176';snapshots['approvedHut']['collection'].hide_render=fixture!='approved-hut01';bpy.context.view_layer.update();p=out/f'{fixture}-{d}-{cid}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders.append({'path':str(p.relative_to(R)),'packetCorresponding':str((B/'candidates/round-05/native-human-context'/p.name).relative_to(B)),'sha256':sha(p),'direction':d,'case':case,'fixture':fixture,'root':list(hr.location),'scale':list(hr.scale)})
report={'scope':'Own independently assembled native source replay, stand12 and walk7, actual evaluated companion12 snapshots with parity,16representative views acrossall4 facings and both hut fixtures; no source saved.','sourcesBefore':before,'sourcesAfter':{k:sha(v)for k,v in paths.items()},'parity':parity,'renders':renders,'calibration':{'root':list(px((0,0,0))),'unitX':list(px((1,0,0))-px((0,0,0))),'unitDepth':list(px((0,-1,0))-px((0,0,0))),'unitZ':list(px((0,0,1))-px((0,0,0)))},'filterSize':sc.render.filter_size};assert report['sourcesBefore']==report['sourcesAfter'];(R/'own-native-replay.json').write_text(json.dumps(report,indent=2)+'\n')
