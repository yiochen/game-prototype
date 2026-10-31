"""Read-back evidence from the saved candidate; never alters candidate bytes."""
import bpy,pathlib,json,sys,argparse,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent;EXP=P.parent
a=argparse.ArgumentParser();a.add_argument('--round',required=True);arg=a.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=EXP/'candidates'/arg.round
def rows(m):return [[float(v) for v in r] for r in m]
def lights(sc):return {o.name:{'matrix':rows(o.matrix_world),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'type':o.data.type} for o in sc.objects if o.type=='LIGHT'}
def camera(sc):return {'matrix':rows(sc.camera.matrix_world),'ortho':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'frame':[sc.render.resolution_x,sc.render.resolution_y]}
def world(sc):return {'nodes':[{'type':n.type,'color':list(n.inputs['Color'].default_value),'strength':n.inputs['Strength'].default_value} for n in sc.world.node_tree.nodes if n.type=='BACKGROUND']}
src=EXP/'backups/original.blend';bpy.ops.wm.open_mainfile(filepath=str(src));sourceCamera=camera(bpy.context.scene);sourceLights=lights(bpy.context.scene);sourceWorld=world(bpy.context.scene)
sourceRoot=rows(bpy.data.objects['garbage-sofa__root'].matrix_world)
project=P/(arg.round+'.blend');bpy.ops.wm.open_mainfile(filepath=str(project));sc=bpy.context.scene;root=bpy.data.objects['garbage-sofa__root'];coll=bpy.data.collections['Mustard worn armchair native parts'];dg=bpy.context.evaluated_depsgraph_get()
def bounds(ps):return {'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}
parts=[];allpoints=[]
for o in coll.objects:
    ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices];allpoints+=ps
    parts.append({'name':o.name,'type':o.type,'bounds':bounds(ps),'vertices':len(me.vertices),'faces':len(me.polygons),'zeroAreaFaces':sum(p.area<1e-12 for p in me.polygons),'materials':[m.name if m else None for m in me.materials],'nullMaterialFaces':sum(p.material_index>=len(me.materials) or me.materials[p.material_index] is None for p in me.polygons)});ev.to_mesh_clear()
b=bounds(allpoints);currentCamera=camera(sc);currentLights=lights(sc);currentWorld=world(sc)
def px(v):
    p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*896,(1-p.y)*1152]
pts={'root':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1))}
cal={'root':pts['root'],**{k:[pts[k][i]-pts['root'][i] for i in [0,1]] for k in ['unitX','unitDepth','unitHeight']}}
expected={'root':[448,704],'unitX':[256,0],'unitDepth':[0,256],'unitHeight':[0,-179.2]};err=max(abs(x-y) for k in cal for x,y in zip(cal[k],expected[k]))
materials=[]
for m in bpy.data.materials:
    nodes=list(m.node_tree.nodes) if m.use_nodes else [];bs=[n for n in nodes if n.type=='BSDF_PRINCIPLED'];materials.append({'name':m.name,'alpha':[n.inputs['Alpha'].default_value for n in bs],'externalImageNodes':[n.image.filepath for n in nodes if n.type=='TEX_IMAGE' and n.image],'animated':bool(m.animation_data or m.node_tree.animation_data)})
checks={'sourceCameraExact':currentCamera==sourceCamera,'sourceRootExact':rows(root.matrix_world)==sourceRoot,'sourceLightsExact':currentLights==sourceLights,'sourceWorldExact':currentWorld==sourceWorld,'nativeFrame896x1152':currentCamera['frame']==[896,1152] and sc.render.resolution_percentage==100,'physicalEnvelope':b['min'][0]>=-.5 and b['max'][0]<=.5 and b['min'][1]>=-.5 and b['max'][1]<=.5,'groundContact':abs(b['min'][2])<1e-6,'heightMaximum':b['max'][2]<=1.5,'fourShortFootContacts':len([p for p in parts if 'short_foot' in p['name'] and abs(p['bounds']['min'][2])<1e-6])==4,'projectionCalibrationWithin005px':err<.05,'opaqueMaterials':all(all(v==1 for v in m['alpha']) for m in materials),'noExternalResources':not bpy.data.libraries and not any(m['externalImageNodes'] for m in materials),'nativeGeometryOnly':all(o.type in {'MESH','CURVE'} for o in coll.objects),'staticNoAnimations':not bpy.data.actions,'transparentCanvas':sc.render.film_transparent,'backupUntouched':hashlib.sha256(src.read_bytes()).hexdigest()=='7fa178bbfc0bde281a7b8c6188602662c5dac7e2a133363375fb037be909d7e6'}
audit={'round':arg.round,'project':str(project.relative_to(EXP)),'sourceCamera':sourceCamera,'currentCamera':currentCamera,'rootMatrix':rows(root.matrix_world),'nativeBounds':b,'parts':parts,'projectionPoints':pts,'calibration':cal,'maxProjectionErrorPx':err,'sourceLights':sourceLights,'currentLights':currentLights,'sourceWorld':sourceWorld,'currentWorld':currentWorld,'materials':materials,'checks':checks,'allPassed':all(checks.values()),'topologyNotes':'Native bevel/solidified cloth and evaluated capped curves can retain zero-area corner/cap facets. Counts are recorded per part; appearance is reviewed in every required facing. No opacity cutout or target image nodes.'}
(OUT/'readback-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
sc.render.filepath=str(OUT/'replay-S.png');bpy.ops.render.render(write_still=True)
print('AUDIT',json.dumps(checks));print('BOUNDS',b)
