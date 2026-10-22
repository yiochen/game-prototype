import bpy,json,sys,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[2];P=B/'source';sys.path.insert(0,str(P));import native_actions_round03 as native
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()=='4f81f6e29a8b587ea03bf4a22e6ac4762585aea643bad7569c5a4506ea7a0073'
sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];plane=bpy.data.objects['chef_lena__ground_root.002__held_dish-salmon__image_plane'];mat=plane.data.materials[0];texture=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE');width=plane.data.vertices[1].co.x-plane.data.vertices[0].co.x
imagepath=B/'candidates/round-03/resources/dish-salmon.png';assert hashlib.sha256(imagepath.read_bytes()).hexdigest()=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
# Only the permitted resource, fullUV and two top coordinates are changed, transiently.
im=bpy.data.images.load(str(imagepath),check_existing=False);im.colorspace_settings.name='sRGB';im.alpha_mode='STRAIGHT';texture.image=im
for i in [2,3]:plane.data.vertices[i].co.y=width*505/731
for loop,uv in zip(plane.data.uv_layers.active.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=uv
plane.data.update();bpy.context.view_layer.update();asset={'collection':coll,'root':root,'armature':arm};rig=json.loads((P/'rig-round03.json').read_text())
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
folder=Path(__file__).resolve().parent/'controls';folder.mkdir(exist_ok=True);rows=[]
for clip,direction,index in [('idle','S',0),('work','E',5),('hold','S',0),('hold','E',4),('hold','W',5),('load','E',0),('load','E',5),('load','N',11)]:
 native.apply_clip(asset,rig,clip,index+1,direction,sc);p=folder/(clip+'-'+direction+'-'+str(index)+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);rows.append({'key':[clip,direction,index],'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});print('CANONICAL_CONTROL',str(p),flush=True)
Path(__file__).resolve().parent/'control-regeneration-manifest.json'.write_text(json.dumps({'basisSHA256':'4f81f6e29a8b587ea03bf4a22e6ac4762585aea643bad7569c5a4506ea7a0073','canonicalFoodSHA256':hashlib.sha256(imagepath.read_bytes()).hexdigest(),'patch':'image binding, fullUV, top2Y=existingLocalWidth*505/731 only; no source save','rows':rows},indent=2))
