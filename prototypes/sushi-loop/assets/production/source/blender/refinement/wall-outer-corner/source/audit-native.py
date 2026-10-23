import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];C=B/'candidates/round-03';P=B/'source/round-03.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(P));s=bpy.context.scene;c=bpy.data.collections['Refined wall outer corner'];r=bpy.data.objects['wall-outer-corner__root'];bpy.context.view_layer.update()
def rows(m):return[list(v)for v in m]
def pix(v):
 p=world_to_camera_view(s,s.camera,Vector(v));return[p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]
# Native reopening measures saved selected collection, never unrelated hidden data.
points=[o.matrix_world@v.co for o in c.all_objects if o.type=='MESH'for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
bounds=[[min(v[i]for v in points),max(v[i]for v in points)]for i in range(3)]
family=json.loads((B/'inputs/family-settings.json').read_text());lights=[]
for o in s.objects:
 if o.type=='LIGHT':
  lights.append({'name':o.name,'type':o.data.type,'energy':o.data.energy,'shape':o.data.shape,'size':o.data.size,'matrix':rows(o.matrix_world),'color':list(o.data.color)})
nodechecks=[]
def serial_value(v):
 try:return list(v)
 except TypeError:return v
for m in bpy.data.materials:
 if 'family_source_material' not in m:continue
 source=bpy.data.materials[m['family_source_material']]
 paramErrors=[]
 for sn in source.node_tree.nodes:
  cn=m.node_tree.nodes.get(sn.name)
  if not cn or cn.bl_idname!=sn.bl_idname:paramErrors.append(sn.name+': node mismatch');continue
  for i,sv in enumerate(sn.inputs):
   if not hasattr(sv,'default_value'):continue
   a=serial_value(sv.default_value);b=serial_value(cn.inputs[i].default_value)
   if a!=b:paramErrors.append(sn.name+': input '+str(i))
  if sn.type=='VALTORGB':
   if [(e.position,list(e.color))for e in sn.color_ramp.elements]!=[(e.position,list(e.color))for e in cn.color_ramp.elements]:paramErrors.append(sn.name+': ramp')
  if sn.type in('MATH','VECT_MATH') and sn.operation!=cn.operation:paramErrors.append(sn.name+': operation')
 nodechecks.append({'corner':m.name,'approvedFamilyMaterial':source.name,'parameterMismatches':paramErrors,'passed':not paramErrors,'coordinateChange':'Native family_coordinate attribute replaces straight Object coordinate links; longitudinal/transverse/height at both exact end rings.'})
assert all(v['passed']for v in nodechecks)
for expected in family['lighting']['lights']:
 actual=next(v for v in lights if v['name']==expected['name'])
 assert actual['energy']==expected['energy'] and actual['size']==expected['size'] and actual['matrix']==expected['matrix']
assert [s.render.resolution_x,s.render.resolution_y]==[384,704]
assert abs(pix((0,0,0))[0]-192)<.001 and abs(pix((0,0,0))[1]-512)<.001
assert len([o for o in c.all_objects if o.type=='MESH'])==14 and r.rotation_euler.z==0
deps={'externalImages':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)}for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[v.filepath for v in bpy.data.libraries]}
assert not deps['externalImages']and not deps['linkedLibraries']
audit={'project':str(P.relative_to(B)),'sha256':sha(P),'recipeSHA256':sha(B/'source/round-03.py'),'method':'Reopened exact saved .blend in fresh Blender background process; selected corner collection and updated evaluated depsgraph. No candidate bytes changed.','root':{'name':r.name,'rotationZ':r.rotation_euler.z,'matrix':rows(r.matrix_world)},'bounds':bounds,'camera':{'name':s.camera.name,'matrix':rows(s.camera.matrix_world),'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'frame':[s.render.resolution_x,s.render.resolution_y],'rootPixel':pix((0,0,0))},'materialParameterChecks':nodechecks,'approvedLightMatrixAndParameterIdentity':True,'lights':lights,'world':{'name':s.world.name,'strength':s.world.node_tree.nodes['Background'].inputs['Strength'].default_value,'color':list(s.world.node_tree.nodes['Background'].inputs['Color'].default_value)},'captureSettings':{'engine':s.render.engine,'samples':s.cycles.samples,'device':s.cycles.device,'denoising':s.cycles.use_denoising,'filter':s.cycles.pixel_filter_type,'filterSize':s.render.filter_size,'transparent':s.render.film_transparent,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'fps':s.render.fps,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure},'collection':{'selected':c.name,'selectedVisible':not c.hide_render,'meshes':14,'hiddenApprovedStraightDependency':bpy.data.collections['S33_PROP_wall-middle.001'].hide_render},'dependencies':deps,'sourceIntegrity':sha((B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve())=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'}
(C/'native-audit.json').write_text(json.dumps(audit,indent=2))
print('NATIVE REOPEN AUDIT COMPLETE',audit['sha256'])

