"""Fresh-process diagnostic, exact source or independent patch; no saves/settings edits."""
import bpy,json,sys,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-04/alpha-diagnostic';C.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round02 as native
args=sys.argv[sys.argv.index('--')+1:];label=args[0];readpixels=args[1]=='read';digest=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();control=digest=='4f81f6e29a8b587ea03bf4a22e6ac4762585aea643bad7569c5a4506ea7a0073';assert control or digest=='0bb3a656a5194329292663166623edc7fbc823d4d5b85ebffcbb0d094fc31dce';sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;plane=bpy.data.objects['chef_lena__ground_root.002__held_dish-salmon__image_plane'];tex=next(n for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
if control:
 old=tex.image;im=bpy.data.images.load(str(O/'candidates/round-04/resources/dish-salmon.png'),check_existing=False);im.alpha_mode=old.alpha_mode;im.colorspace_settings.name=old.colorspace_settings.name;tex.image=im;width=plane.data.vertices[1].co.x-plane.data.vertices[0].co.x
 for i in [2,3]:plane.data.vertices[i].co.y=width*505/731
 for loop,uv in zip(plane.data.uv_layers.active.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=uv
 plane.data.update();bpy.context.view_layer.update()
if readpixels:
 pixels=np.empty(len(tex.image.pixels),dtype=np.float32);tex.image.pixels.foreach_get(pixels)
asset={'collection':bpy.data.collections['S33_CHARACTER_chef_lena.002'],'root':bpy.data.objects['chef_lena__ground_root.002'],'armature':bpy.data.objects['chef_lena__armature.002']};rig=json.loads((P/'rig-round02.json').read_text());native.apply_clip(asset,rig,'hold',8,'W',sc);prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
sc.render.filepath=str(C/(label+'.png'));bpy.ops.render.render(write_still=True);(C/(label+'.json')).write_text(json.dumps({'label':label,'basisSHA256':digest,'independentApproved02ControlPatch':control,'imagePixelsReadBeforeRender':readpixels,'path':str(Path(sc.render.filepath).relative_to(O)),'sha256':hashlib.sha256(Path(sc.render.filepath).read_bytes()).hexdigest(),'settingsUnchanged':True,'sourceSaved':False},indent=2))
