"""Round02: preserve exact neutral resources; revise active guard trajectory only."""
import bpy,json,pathlib,sys,math,importlib.util
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;E=HERE.parent;OUT=E/'candidates/round-02'
sp=importlib.util.spec_from_file_location('immutable_original_native_tools',HERE/'round-01.py');V1=importlib.util.module_from_spec(sp);sp.loader.exec_module(V1)
FACINGS=V1.FACINGS;savej=V1.savej;sha=V1.sha;bounds=V1.bounds;apply_clip=V1.apply_clip;settings=V1.settings
def setup():
 bpy.ops.wm.open_mainfile(filepath=str(HERE/'round-01.blend'))
 s=bpy.context.scene;col=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root'];guard=bpy.data.objects['collector__guard_rock'];actions=json.loads(root['nativeActions']);a=bpy.data.actions[actions['active'][guard.name]]
 changed=[]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path=='rotation_euler' and fc.array_index==0:
      for k in fc.keyframe_points:
       fr=round(k.co.x);phase=2*math.pi*((fr-1)%12)/12
       old=float(k.co.y);k.co.y=.11+.10*math.sin(phase+.55);k.interpolation='LINEAR';changed.append({'frame':fr,'old':old,'new':float(k.co.y)})
 # 0.006 local-unit active eccentric path keeps the unchanged fixed shaft inside
 # the finite bottom rail while providing housing clearance at nearly-upright angles.
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path=='location' and fc.array_index==1:
      for k in fc.keyframe_points:
       old=float(k.co.y);k.co.y=-.255;k.interpolation='LINEAR';changed.append({'frame':round(k.co.x),'channel':'locationY','old':old,'new':float(k.co.y)})
 apply_clip(s,col,'idle','S',1);bpy.context.view_layer.update()
 bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-02.blend'),compress=True)
 savej(HERE/'round-02-settings.json',settings(s,root))
 savej(OUT/'native-change-record.json',{'source':'source/round-01.blend','sourceSHA256':sha(HERE/'round-01.blend'),'newProject':'source/round-02.blend','newProjectSHA256':sha(HERE/'round-02.blend'),'changedOnly':'INLET_NATIVE active guard rotation_euler.x and locationY keys: upright outward rock with0.006 local-unit eccentric working pivot, continuously joined to unchanged fixed lower shaft inside the native bottom rail. Native neutral meshes/normals/UV/materials/stored transforms, source camera/lights/sample/filter/publication, mouthpulse channels and all timing retained.','guardKeys':changed,'closingKeyUsesSamePhaseAs1':True,'approval':False})
 return s,col,root
if __name__=='__main__':setup()
