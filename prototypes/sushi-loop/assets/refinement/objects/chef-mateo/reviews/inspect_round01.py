import bpy,json,pathlib,sys,hashlib,math
from mathutils import Vector
BASE=pathlib.Path(__file__).resolve().parent.parent
LIB=BASE/'source/round01.blend'
TOOLS=(BASE/'../../../production/source/blender').resolve()
sys.path.insert(0,str(TOOLS))
import native_actions as N
bpy.ops.wm.open_mainfile(filepath=str(LIB.resolve()))
record=json.loads((BASE/'inputs/source-rig.json').read_text())
root=bpy.data.objects[record['groundRootObject']]
cols=[c for c in bpy.data.collections if root.name in c.objects]
col=cols[0]
scene=bpy.data.scenes.new('Mateo independent source inspection')
scene.collection.children.link(col)
bpy.context.window.scene=scene
col.hide_render=False;col.hide_viewport=False
bpy.context.view_layer.update()
asset={'collection':col,'root':root}
objs=list(col.all_objects)
arm=next(o for o in objs if o.type=='ARMATURE')
report={'project':str(LIB.resolve()),'projectSHA256':hashlib.sha256(LIB.read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'collection':col.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'armature':arm.name,'boneNames':[b.name for b in arm.data.bones],'objects':[],'samples':[],'materials':[],'sourceScenes':[]}
for sc in bpy.data.scenes:
 if sc==scene:continue
 report['sourceScenes'].append({'name':sc.name,'camera':sc.camera.name if sc.camera else None,'cameraData':{'matrixWorld':[list(row) for row in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]} if sc.camera else None,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'position':list(o.matrix_world.translation),'size':getattr(o.data,'size',None)} for o in sc.objects if o.type=='LIGHT'],'renderEngine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filmTransparent':sc.render.film_transparent})
for m in {m for o in objs if o.type=='MESH' for m in o.data.materials if m}:
 report['materials'].append({'name':m.name,'diffuseColor':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:N._plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and i.name in ['Base Color','Roughness','Specular IOR Level','Strength']}} for n in m.node_tree.nodes] if m.use_nodes else [],'images':[{'name':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.use_nodes else []})
for o in objs:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixLocal':[list(r) for r in o.matrix_local],'rotationEuler':list(o.rotation_euler),'hideRender':o.hide_render,'custom':{k:N._plain(o[k]) for k in o.keys() if k!='_RNA_UI'}}
 if o.type=='MESH':
  d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),materials=[m.name if m else None for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers])
 report['objects'].append(d)
for clip in record['clips']:
 for direction in ['S','E','N','W']:
  for frame in range(1,13):
   N.apply_clip(asset,record,clip,frame,direction,scene)
   dep=bpy.context.evaluated_depsgraph_get();samples=[];body=[];prop=[];topology={}
   for o in objs:
    if o.type!='MESH':continue
    eo=o.evaluated_get(dep);me=eo.to_mesh();topology[o.name]={'vertices':len(me.vertices),'polygons':len(me.polygons)};vs=[eo.matrix_world@v.co for v in me.vertices];eo.to_mesh_clear()
    if not vs:continue
    hidden=o.hide_render or any(a.hide_render for a in [o.parent] if a)
    bounds=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
    if not hidden:(prop if any(t in o.name for t in ['held_dish','knife_','utensil']) else body).extend(vs)
    if any(t in o.name for t in ['palm','shoe','foot','held_dish','knife_','utensil']):
     samples.append({'name':o.name,'bounds':bounds,'centroid':list(sum(vs,Vector())/len(vs)),'visible':not hidden,'vertices':len(vs),'polygons':len(me.polygons) if False else len(o.data.polygons)})
   bounds=lambda a:[[min(v[i] for v in a),max(v[i] for v in a)] for i in range(3)] if a else None
   ea=arm.evaluated_get(dep)
   bones={b.name:{'head':list(ea.matrix_world@b.head),'tail':list(ea.matrix_world@b.tail)} for b in ea.pose.bones if b.name.startswith(('foot_','hand_')) and 'goal' not in b.name}
   report['samples'].append({'clip':clip,'direction':direction,'frame':frame,'rootRotationZ':root.rotation_euler.z,'bodyBounds':bounds(body),'visiblePropBounds':bounds(prop),'evaluatedBones':bones,'contacts':samples,'topology':topology})
(BASE/'reviews/round01-native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'collection':col.name,'root':root.name,'armature':arm.name,'objects':len(objs),'samples':len(report['samples']),'projectSHA256':report['projectSHA256'],'firstBodyBounds':report['samples'][0]['bodyBounds'],'objectsBrief':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in objs]},indent=2))
