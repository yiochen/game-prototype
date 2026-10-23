import bpy,runpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent;g=runpy.run_path(str(R/'audit-human-and-profile-v2.py'));sc=g['sc'];fr=g['fr'];er=g['er'];hr=g['hr'];hc=g['hc'];rig=g['rig'];native=g['native'];path=g['path'];cam=sc.camera
sc.render.resolution_x=1792;sc.render.resolution_y=1792;cam.data.ortho_scale=896/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return[p.x*1792,(1-p.y)*1792]
b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];cam.data.shift_y=(1152-b[1])/dy;bpy.context.view_layer.update();records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 for i in [0,1,2]:
  native.apply_clip({'root':hr,'collection':hc},rig,'walk',i+1,d,sc);rot=Matrix.Rotation(a,3,'Z');fr.rotation_euler.z=a;er.rotation_euler.z=a;er.location=rot@Vector((0,-1.5,0));hr.location=rot@Vector(path[i]);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();feet=[]
  for o in hc.all_objects:
   if o.type!='MESH' or o.hide_render or not any(s in o.name.lower() for s in ['shoe','sole','foot']):continue
   e=o.evaluated_get(dg);m=e.to_mesh();feet.extend(px(e.matrix_world@v.co) for v in m.vertices);e.to_mesh_clear()
  p=R/f'own-current-native-human-{d}-{i}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'facing':d,'pathIndex':i,'walkFrame':i+1,'rootWorld':list(hr.location),'rootScale':list(hr.scale),'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'projectedFootBounds':[min(x[0] for x in feet),min(x[1] for x in feet),max(x[0] for x in feet),max(x[1] for x in feet)],'cameraScope':'Current approved native Rosa body at native environment55degree camera; primary actual35degree consumer sprites remain separate.'})
(R/'own-current-human-native-captures.json').write_text(json.dumps(records,indent=2)+'\n')
