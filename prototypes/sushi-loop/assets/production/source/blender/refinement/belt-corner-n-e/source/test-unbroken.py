import bpy,pathlib
s=bpy.context.scene;o=bpy.data.objects['True_unbroken_welded_native_reference'];m=bpy.data.materials.new('TEST');m.diffuse_color=(1,.2,0,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(1,.2,0,1)
o.data.materials.clear();o.data.materials.append(m)
for p in o.data.polygons:p.material_index=0
s.render.use_persistent_data=False;s.render.filepath=str(pathlib.Path(__file__).resolve().parents[1]/'candidates/round-01/test-unbroken.png');bpy.ops.render.render(write_still=True)
print('holdout',o.is_holdout,'indirect',o.is_shadow_catcher,'rays',o.visible_camera,o.visible_diffuse)
