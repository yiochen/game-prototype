"""Fresh-process multiple exact-phase native repeats. No source/settings/pixel changes."""
import bpy,json,sys,hashlib,math
from pathlib import Path
import numpy as np
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-04/alpha-diagnostic';sys.path.insert(0,str(P));import native_actions_round02 as native
from control_audit_common_round04 import semantic,capture,rna,tree,drivers,simple,jhash,arrayhash
args=sys.argv[sys.argv.index('--')+1:];label=args[0];prep=args[1];count=int(args[2]);digest=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();control=digest=='4f81f6e29a8b587ea03bf4a22e6ac4762585aea643bad7569c5a4506ea7a0073';assert control or digest=='0bb3a656a5194329292663166623edc7fbc823d4d5b85ebffcbb0d094fc31dce'
sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;plane=bpy.data.objects['chef_lena__ground_root.002__held_dish-salmon__image_plane'];tex=next(n for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');canonical=O/'candidates/round-04/resources/dish-salmon.png'
if control:
 old=tex.image;im=bpy.data.images.load(str(canonical),check_existing=False);im.alpha_mode=old.alpha_mode;im.colorspace_settings.name=old.colorspace_settings.name;tex.image=im;width=plane.data.vertices[1].co.x-plane.data.vertices[0].co.x
 for i in [2,3]:plane.data.vertices[i].co.y=width*505/731
 for loop,uv in zip(plane.data.uv_layers.active.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=uv
 plane.data.update();bpy.context.view_layer.update()
asset={'collection':bpy.data.collections['S33_CHARACTER_chef_lena.002'],'root':bpy.data.objects['chef_lena__ground_root.002'],'armature':bpy.data.objects['chef_lena__armature.002']};rig=json.loads((P/'rig-round02.json').read_text())
if prep=='main-capture':
 pixels=np.empty(len(tex.image.pixels),dtype=np.float32);tex.image.pixels.foreach_get(pixels)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
def snapshot():
 dg=bpy.context.evaluated_depsgraph_get();ep=plane.evaluated_get(dg);me=ep.to_mesh();mat=np.array(ep.matrix_world,dtype=np.float32);v=np.array([tuple(x.co) for x in me.vertices],dtype=np.float32);n=np.array([tuple(x.normal) for x in me.vertices],dtype=np.float32);uv=np.array([tuple(x.uv) for x in me.uv_layers.active.data],dtype=np.float32);poly=np.array([tuple(x.normal) for x in me.polygons],dtype=np.float32);world=np.array([tuple(ep.matrix_world@x.co) for x in me.vertices],dtype=np.float32);ep.to_mesh_clear();arrays={'foodWorldMatrix':mat,'foodEvaluatedLocalVertices':v,'foodEvaluatedWorldVertices':world,'foodEvaluatedVertexNormals':n,'foodEvaluatedPolygonNormals':poly,'foodEvaluatedUV':uv};render=rna(sc.render);render.pop('filepath',None)
 data={'arrays':{k:{'values':x.tolist(),'float32SHA256':arrayhash(x),'losslessHexScalars':[float(z).hex() for z in x.flatten()]} for k,x in arrays.items()},'foodDrivers':drivers(plane),'foodRayFlags':{k:getattr(plane,k) for k in ['visible_camera','visible_diffuse','visible_glossy','visible_transmission','visible_volume_scatter','visible_shadow']},'foodParentMatrix':simple(plane.parent.matrix_world),'foodRootParentMatrix':simple(asset['root'].matrix_world),'foodTextureNode':{'interpolation':tex.interpolation,'projection':tex.projection,'extension':tex.extension,'alphaMode':tex.image.alpha_mode,'colorspace':tex.image.colorspace_settings.name},'foodMaterialExceptImage':tree(plane.data.materials[0].node_tree,ignore_image=True),'world':tree(sc.world.node_tree),'lights':{o.name:{'matrix':simple(o.matrix_world),'data':rna(o.data)} for o in sc.objects if o.type=='LIGHT'},'camera':{'matrix':simple(sc.camera.matrix_world),'data':rna(sc.camera.data)},'render':render,'cycles':rna(sc.cycles),'view':rna(sc.view_settings),'frame':sc.frame_current,'rootRotationZ':asset['root'].rotation_euler.z};data['snapshotSHA256']=jhash(data);return data
rows=[]
for repeat in range(count):
 native.apply_clip(asset,rig,'hold',8,'W',sc)
 if prep=='main-capture':capture(sc,asset['collection'],asset['root'],asset['armature'])
 p=C/(label+f'-{repeat:02d}.png');assert not p.exists();sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);snap=snapshot();rows.append({'repeat':repeat,'path':str(p.relative_to(O)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'snapshot':snap});print('REPEAT',label,repeat,snap['snapshotSHA256'],flush=True)
(C/(label+'-repeats.json')).write_text(json.dumps({'label':label,'basisSHA256':digest,'sourceSaved':False,'independentApproved02Patch':control,'preparation':prep,'meaning':'Same native settings/rays/shader/light/camera/seed. Minimal or exact main-loop hidden dependency sampling preparation only; source never saved and pixels never altered. Full evaluated float32 values and lossless hex recorded after each render.','rows':rows},indent=2))
