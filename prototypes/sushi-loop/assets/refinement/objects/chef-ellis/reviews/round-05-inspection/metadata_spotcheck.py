import bpy,sys,json,hashlib
from pathlib import Path
base=Path.cwd()/'prototypes/sushi-loop/assets';obj=base/'refinement/objects/chef-ellis';out=obj/'reviews/round-05-inspection';sys.path.insert(0,str(base/'production/source/blender'));import native_actions

def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if hasattr(x,'items'):return {str(k):val(v) for k,v in x.items()}
 try:return [val(y) for y in x]
 except:return str(x)
def drivers(o):
 return [{'path':f.data_path,'index':f.array_index,'type':f.driver.type,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'path':t.data_path,'bone':t.bone_target,'transform_type':t.transform_type,'transform_space':t.transform_space} for t in v.targets]} for v in f.driver.variables]} for f in o.animation_data.drivers] if o.animation_data else []
def state(tag):
 c=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];p=bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon__image_plane'];r={'file':bpy.data.filepath,'objects':{o.name:val(dict(o.items())) for o in c.all_objects if o.keys()},'collection':val(dict(c.items())),'scenes':{s.name:val(dict(s.items())) for s in bpy.data.scenes if s.keys()},'images':[{'name':i.name,'path':i.filepath,'size':list(i.size),'packed':i.packed_file is not None,'hash':hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None,'custom':val(dict(i.items()))} for i in bpy.data.images], 'plane':{'parent':p.parent.name,'matrixBasis':[list(row) for row in p.matrix_basis],'matrixParentInverse':[list(row) for row in p.matrix_parent_inverse],'drivers':drivers(p),'constraints':[str(co.type) for co in p.constraints],'modifiers':[str(m.type) for m in p.modifiers],'meshVertices':[list(v.co) for v in p.data.vertices],'uv':[list(v.uv) for v in p.data.uv_layers.active.data]}}
 (out/(tag+'-metadata.json')).write_text(json.dumps(r,indent=2)+'\n');return r
bpy.ops.wm.open_mainfile(filepath=str(obj/'source/round-04.blend'));a=state('baseline04')
bpy.ops.wm.open_mainfile(filepath=str(obj/'source/round-05.blend'));b=state('candidate05')
print('plane transform/driver lock',all(a['plane'][k]==b['plane'][k] for k in ['parent','matrixBasis','matrixParentInverse','drivers','constraints','modifiers']))
c=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];c.hide_render=False;c.hide_viewport=False;bpy.context.view_layer.update();asset={'collection':c,'root':bpy.data.objects['chef_ellis__ground_root.001'],'armature':bpy.data.objects['chef_ellis__armature.001']};record=json.loads((obj/'inputs/source-rig.json').read_text());native_actions.apply_clip(asset,record,'hold',6,'S',bpy.context.scene)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
bpy.context.scene.render.filepath=str(out/'native-spotcheck-hold-S-005.png');bpy.ops.render.render(write_still=True)
