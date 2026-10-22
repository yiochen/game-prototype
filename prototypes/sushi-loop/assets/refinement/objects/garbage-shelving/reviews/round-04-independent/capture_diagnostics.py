import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');OUT=O/'reviews/round-04-independent';R=json.loads((O/'candidates/round-04/rig.json').read_text());S=bpy.context.scene;root=bpy.data.objects[R['groundRootObject']];cam=S.camera
for r in R['clips']['idle']['actions']:
 o=bpy.data.objects[r['ownerName']];a=bpy.data.actions[r['action']];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=next(s for s in a.slots if s.identifier==r['slotIdentifier'])
S.frame_set(1);cam.data.shift_x=0;cam.data.shift_y=0;cam.data.ortho_scale=3.5
outputs=[]
for kind,pos,target in [('contact',(0,-8,.7),(0,-.1,.7)),('underside',(2.5,-4,-2),(0,0,.6))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 if kind=='underside':
  ld=bpy.data.lights.new('Judge diagnostic centered underside fill','AREA');ld.energy=120;ld.size=4;lo=bpy.data.objects.new(ld.name,ld);S.collection.objects.link(lo);lo.location=(0,0,-3);lo.rotation_euler=(Vector((0,0,.6))-lo.location).to_track_quat('-Z','Y').to_euler()
 for d,yaw in {'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}.items():
  root.rotation_euler=(0,0,yaw);bpy.context.view_layer.update();p=OUT/f'native-{kind}-{d}.png';S.render.filepath=str(p);bpy.ops.render.render(write_still=True);outputs.append({'kind':kind,'direction':d,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cameraPosition':list(pos),'cameraTarget':list(target),'orthoScale':3.5,'shiftY':0,'diagnosticFill':'centered under Z=-3,120W area4' if kind=='underside' else None})
 if kind=='underside':bpy.data.objects.remove(lo,do_unlink=True)
(OUT/'supplemental-diagnostic-captures.json').write_text(json.dumps({'inputProject':bpy.data.filepath,'inputProjectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'purpose':'Supplementary4facing ground/underside inspections. Registered exports stay authoritative and unchanged. No native-source/candidate file saved or modified.','outputs':outputs},indent=2)+'\n')
