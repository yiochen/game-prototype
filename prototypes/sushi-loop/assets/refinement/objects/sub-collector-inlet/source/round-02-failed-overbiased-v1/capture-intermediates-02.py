import bpy,pathlib,json,sys,math,importlib.util
sys.dont_write_bytecode=True
from bpy_extras.object_utils import world_to_camera_view
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-02'
sp=importlib.util.spec_from_file_location('round02_native_recipe',H/'round-02.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A)
bpy.ops.wm.open_mainfile(filepath=str(H/'round-02.blend'));s=bpy.context.scene;c=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root'];records=[]
for di in 'NESW':
 for fr in [1.5,3.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5]:
  A.apply_clip(s,c,'active',di,math.floor(fr));s.frame_set(math.floor(fr),subframe=fr-math.floor(fr));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();parts=[];pts=[]
  for o in c.all_objects:
   if o.type!='MESH':continue
   eo=o.evaluated_get(dg);me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];pts+=vs;parts.append({'name':o.name,'bounds':A.bounds(vs),'matrix':[list(r) for r in eo.matrix_world]});eo.to_mesh_clear()
  p=O/'native-intermediates'/di/f'{fr:04.1f}.png';p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  records.append({'direction':di,'clip':'active','nativeFrame':float(s.frame_current_final),'runtimeAtlasFrame':False,'rootRotationZ':float(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'parts':parts,'bounds':A.bounds(pts),'path':str(p.relative_to(E)),'sha256':A.sha(p)})
A.savej(O/'intermediate-capture-audit.json',{'project':'source/round-02.blend','projectSHA256':A.sha(H/'round-02.blend'),'frames':records,'settings':A.settings(s,root),'qualification':'Real native subframe evaluation/captures with unchanged common camera/light48sample/filter.5 recipe. Supplemental inspection only; runtime remains12frames/12fps.'});print('INTERMEDIATE CAPTURES',len(records))
