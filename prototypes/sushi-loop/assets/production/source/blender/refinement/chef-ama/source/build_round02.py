"""Canonical salmon semantic mapping only; approved Ama native body is immutable."""
import bpy,json,sys,hashlib,shutil
from pathlib import Path
P=Path(__file__).parent;B=P.parent;C=B/'candidates/round-02'
briefpath=B/'brief-v3-held-food-semantic-contact.json';brief=json.loads(briefpath.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(briefpath)=='08f3f5fa4f4112023519180a61c43902f36cce5de82dff45c2a73f8a9bd2a837'
assert sha(Path(bpy.data.filepath))==brief['approvedBody']['sha256']
sc=bpy.data.scenes['Ama warm soft round01'];bpy.context.window.scene=sc
coll=bpy.data.collections['S33_CHARACTER_chef_ama.002'];root=bpy.data.objects['chef_ama__ground_root.002'];arm=bpy.data.objects['chef_ama__armature.001'];plane=next(o for o in coll.all_objects if '__image_plane' in o.name)
node=next(n for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');old=node.image
canonical=(B/brief['foodDependency']['artwork']).resolve();assert sha(canonical)==brief['foodDependency']['sha256']
dep=P/'dependencies-round02/dish-salmon.png';shutil.copyfile(canonical,dep)
oldrecord={'name':old.name,'alphaMode':old.alpha_mode,'colorSpace':old.colorspace_settings.name,'packedSHA256':hashlib.sha256(old.packed_file.data).hexdigest()}
new=bpy.data.images.load(str(dep),check_existing=False);new.alpha_mode=old.alpha_mode;new.colorspace_settings.name=old.colorspace_settings.name;new.pack();node.image=new
assert list(new.size)==[731,505] and hashlib.sha256(new.packed_file.data).hexdigest()==brief['foodDependency']['sha256']
oldname=old.name
if old.users==0:bpy.data.images.remove(old)
new.name=oldname;new.filepath='//dependencies-round02/dish-salmon.png'
m=brief['semanticFoodMapping'];x0,x1=m['localX'];y0,y1=m['localY'];verts=[(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)]
assert len(plane.data.vertices)==4 and [list(p.vertices) for p in plane.data.polygons]==[[0,1,2,3]]
for v,co in zip(plane.data.vertices,verts):v.co=co
for loop,uv in zip(plane.data.uv_layers.active.data,m['fullUV']):loop.uv=uv
plane.data.update()
# No transforms, action, driver, ray-law, material, light or physical body edits.
ids={sc}
rig=json.loads((P/'rig-round01.json').read_text())
for c in rig['clips'].values():
 for t in c['actions']:ids.add(bpy.data.actions[t['action']])
bpy.data.libraries.write(str(P/'round-02.blend'),ids,fake_user=True,compress=True)
recipe={'asset':'chef-ama','round':'round-02','scope':'canonical-salmon-semantic-mapping-only','brief':briefpath.name,'briefSHA256':sha(briefpath),'approvedSource':str(Path(bpy.data.filepath)),'approvedSourceSHA256':brief['approvedBody']['sha256'],'project':'source/round-02.blend','projectSHA256':sha(P/'round-02.blend'),'scene':sc.name,'collection':coll.name,'root':root.name,'armature':arm.name,'plane':plane.name,'allowedChanges':['Exact packed canonical731x505RGBA image pointer/dependency','One global native food quad and fullUV per semanticFoodMapping'],'semanticFoodMapping':m,'actualNativeQuad':[list(v.co) for v in plane.data.vertices],'actualUV':[list(v.uv) for v in plane.data.uv_layers.active.data],'food':{'path':'source/dependencies-round02/dish-salmon.png','sha256':sha(dep),'size':list(new.size),'original':oldrecord,'alphaMode':new.alpha_mode,'colorSpace':new.colorspace_settings.name,'interpolation':node.interpolation,'extension':node.extension},'renderer':json.loads((P/'recipe-round01.json').read_text())['renderer'],'notes':['Native original Ama ray/XYZ/yaw/visibility law unchanged.','Approved physical body and knife remain exact; no form/material/light/camera redesign.','Food remains explicitly2D on original native animated holder; no modeled3D plate claim.']}
(P/'recipe-round02.json').write_text(json.dumps(recipe,indent=2)+'\n');shutil.copyfile(P/'rig-round01.json',P/'rig-round02.json')
print('BUILT',recipe['projectSHA256'],flush=True)
