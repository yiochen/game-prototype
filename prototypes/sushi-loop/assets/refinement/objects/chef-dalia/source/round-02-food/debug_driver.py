import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.dont_write_bytecode=True
from common import *
rec,root,col,arm,foodroot,plane=context();sc=bpy.context.scene
for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
na.apply_clip({'root':root,'collection':col,'armature':arm},rec,'idle',1,'N',sc)
print('AUTOEXEC',bpy.context.preferences.filepaths.use_scripts_auto_execute,bpy.app.autoexec_fail,bpy.app.autoexec_fail_message)
for fc in na._fcurves(plane.animation_data.action):
 if fc.data_path in ['hide_render','hide_viewport']:fc.mute=True
plane.hide_render=False;plane.hide_viewport=False;plane.hide_set(False);foodroot.hide_render=False;foodroot.hide_viewport=False;foodroot.hide_set(False)
sc.frame_set(1);plane.update_tag(refresh={'OBJECT','DATA','TIME'});bpy.context.view_layer.update()
def show(label):
 dg=bpy.context.evaluated_depsgraph_get();print(label,'visible',plane.visible_get(),'render',plane.hide_render,'viewport',plane.hide_viewport,'hide',plane.hide_get(),'inViewLayer',plane.name in bpy.context.view_layer.objects,'rootrot',list(root.rotation_euler),'loc',list(plane.location),'rot',list(plane.rotation_euler),'matrix',[list(z) for z in plane.matrix_world],'evalmatrix',[list(z) for z in plane.evaluated_get(dg).matrix_world]);print('DRIVERS',[{'path':f.data_path,'index':f.array_index,'isvalid':f.is_valid,'driverValid':f.driver.is_valid,'expr':f.driver.expression,'target':f.driver.variables[0].targets[0].id.name,'targetPath':f.driver.variables[0].targets[0].data_path,'targetIsRoot':f.driver.variables[0].targets[0].id==root} for f in plane.animation_data.drivers])
show('BEFORE_REFRESH')
for fc in plane.animation_data.drivers:fc.driver.expression=fc.driver.expression
plane.update_tag(refresh={'OBJECT','DATA','TIME'});sc.frame_set(2);sc.frame_set(1);bpy.context.view_layer.update();show('AFTER_EXPRESSION_REFRESH')
