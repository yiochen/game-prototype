import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-05';sys.path.insert(0,str(P));from semantic_round05 import snapshot,compare,digest,ROOT,PLANE,SCENE
EXPECTED='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4';SOURCE='2767a8239378e0e44b41c6a4f2870ca9fece3eed9390cac78594f54efb4033a4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'round-04.blend')==SOURCE;assert sha(BASE/'inputs/approved-round04.blend')==SOURCE
canonical=P/'dependencies/round05/dish-salmon.png';assert sha(canonical)==EXPECTED
sc=bpy.data.scenes[SCENE];bpy.context.window.scene=sc;before=snapshot();(OUT/'approved04-semantic.json').write_text(json.dumps(before,separators=(',',':')))
plane=bpy.data.objects[PLANE];root=bpy.data.objects[ROOT];old=bpy.data.images['dish-salmon.png'];oldHash=hashlib.sha256(old.packed_file.data).hexdigest();new=bpy.data.images.load(str(canonical),check_existing=False);new.name='dish-salmon-canonical-731x505.png';new.alpha_mode=old.alpha_mode;new.colorspace_settings.name=old.colorspace_settings.name;new.pack();new.filepath='//dependencies/round05/dish-salmon.png'
assert list(new.size)==[731,505];assert hashlib.sha256(new.packed_file.data).hexdigest()==EXPECTED
for m in plane.data.materials:
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image==old:n.image=new
assert old.users==0;bpy.data.images.remove(old)
height=(.35*505/731)/1.25
for v in plane.data.vertices:
 if v.co.y>0:v.co.y=height
uv=[(0,0),(1,0),(1,1),(0,1)]
for x,co in zip(plane.data.uv_layers.active.data,uv):x.uv=co
plane['fixed_alpha_rectangle']=[0,0,731,505];plane['source_image']='//dependencies/round05/dish-salmon.png';plane['source_sha256']=EXPECTED;plane['representation']='Canonical approved packed2D salmon; not modeled3D food';plane['source_size']=[731,505];plane['source_uv_rectangle']=[0.,0.,1.,1.];plane['world_height_cells']=.35*505/731
food=json.loads(root['held_food_source']);food.update(path='//dependencies/round05/dish-salmon.png',sha256=EXPECTED,alphaRectangleBottomOrigin=[0,0,731,505],worldHeightCells=.35*505/731,sourceSize=[731,505],uvRectangle=[0,0,1,1],registration='Full canonical source UV, existing lower quad edge at unchanged evaluated palm attachment',sourceVersion='approved canonical dish-salmon round01');root['held_food_source']=json.dumps(food);root['food_composition']='Canonical approved731x505 packed2D salmon, fullUV and true aspect; original lower-edge palm anchor, yaw cancellation and0.60world-cell camera-ray bias; native3D knife during work.'
plane.data.update();bpy.context.view_layer.update();after=snapshot();diff=compare(before,after);(OUT/'in-memory-semantic-delta.json').write_text(json.dumps(diff,indent=2))
# Preserve every original name, scene and original action. New file changes only food data/version metadata.
ids={sc}|set(bpy.data.actions);bpy.data.libraries.write(str(P/'round-05.blend'),ids,fake_user=True,compress=True)
recipe=json.loads((P/'recipe-round04.json').read_text());recipe.update(round=5,activeBrief='brief-v2-food.json',sourceSHA256=SOURCE,approvedBodyBaseline={'project':'source/round-04.blend','sha256':SOURCE},nativeChangeScope='Exact approved04 body/knife/camera/light/rig/actions preserved; canonical packed2D salmon binding, fullUV and quad height only',foodRevision={'oldPackedSHA256':oldHash,'oldSize':[1254,1254],'newPackedSHA256':EXPECTED,'newSize':[731,505],'fullUV':[0,0,1,1],'localWidth':.28,'localHeight':height,'worldWidth':.35,'worldHeight':.35*505/731,'lowerEdgeLocalY':0,'cameraRayDepthBiasWorld':.6,'resource':'source/dependencies/round05/dish-salmon.png'},notes=['No approved body/knife/native response changes','All names and native action/driver owners retained','Separate canonical raster remains explicitly packed2D']);brief=json.loads((BASE/'brief-v2-food.json').read_text());recipe.update(activeBriefSHA256=sha(BASE/'brief-v2-food.json'),criteriaSHA256=sha(BASE/'reviews/criteria-v2-food.json'),approvedBodyBaseline=brief['approvedBodyBaseline'],foodDependency=brief['foodDependency'],backupSHA256=sha(BASE/'inputs/approved-round04.blend'));(P/'recipe-round05.json').write_text(json.dumps(recipe,indent=2));print('ROUND05_SAVED',sha(P/'round-05.blend'),'SEMANTIC_DIFF_COUNT',len(diff),flush=True)
