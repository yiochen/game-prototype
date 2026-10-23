import bpy,json,sys,math,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parents[1];OUT=O/'candidates/round-01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(H/'cover.blend'));sc=bpy.context.scene;root=bpy.data.objects['dock-cover__root'];cloth=bpy.data.objects['dock-cover__attached_canvas_hems_and_stitches'];sk=cloth.data.shape_keys;rig=json.loads((H/'rig.json').read_text());r={'sourceSHA256':sha(H/'cover.blend'),'filter_size':sc.render.filter_size,'engine':sc.render.engine,'fps':sc.render.fps,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'cameraMatrix':[list(v)for v in sc.camera.matrix_world],'rootMatrix':[list(v)for v in root.matrix_world],'externalLibraries':[l.filepath for l in bpy.data.libraries],'externalImageResources':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)}for i in bpy.data.images if i.source=='FILE'],'actionMechanism':'One mesh shape-key owner; native attached cloth/hem/stitch vertex geometry, LINEAR baked shape-key values. No opacity/UV/image animation.','actions':[],'cleanProcessReplay':[]}
for clip in ['covered','uncover']:
 a=bpy.data.actions[rig['clips'][clip]['action']];curves=[fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves];r['actions'].append({'clip':clip,'name':a.name,'curves':[{'path':fc.data_path,'arrayIndex':fc.array_index,'extrapolation':fc.extrapolation,'keys':[[p.co.x,p.co.y,p.interpolation]for p in fc.keyframe_points]}for fc in curves]})
for clip,f,d,ang in [('covered',1,'S',0),('uncover',12,'E',math.pi/2)]:
 sk.animation_data.action=None
 for k in sk.key_blocks:k.value=0
 sk.animation_data.action=bpy.data.actions[rig['clips'][clip]['action']]
 if sk.animation_data.action.slots:sk.animation_data.action_slot=sk.animation_data.action.slots[0]
 root.rotation_euler.z=ang;sc.frame_set(f);bpy.context.view_layer.update();p=OUT/'replay'/f'{clip}-{d}-{f}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);orig=OUT/'frames'/f'{clip}-{d}'/f'{f-1:03d}.png';r['cleanProcessReplay'].append({'path':str(p.relative_to(O)),'sha256':sha(p),'reference':str(orig.relative_to(O)),'referenceSHA256':sha(orig),'exactPNGBytes':sha(p)==sha(orig)})
(OUT/'saved-source-reopen-audit.json').write_text(json.dumps(r,indent=2)+'\n');print('REOPEN VERIFIED',r['cleanProcessReplay'])
