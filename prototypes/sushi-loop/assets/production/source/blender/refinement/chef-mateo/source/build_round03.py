"""Narrow canonical-food dependency replacement. Approved native body is frozen."""
import bpy,sys,json,shutil,hashlib,importlib.util,math
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('mateo_r03_common',HERE/'round03_common.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
C.OUT.mkdir(parents=True,exist_ok=True);C.RES.mkdir(exist_ok=True)
assert C.sha(Path(bpy.data.filepath))==C.brief['source']['projectSHA256']
sc,asset,arm,food=C.owned();C.N.apply_clip(asset,C.rig,'idle',1,'S',sc)
before=C.invariants(sc,asset,arm,food);beforeFood=C.object_def(food);beforeNormals=[list(n.vector) for n in food.data.corner_normals]
image_node=next(n for n in food.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');oldimage=image_node.image;oldbytes=bytes(oldimage.packed_file.data)
oldpath=C.RES/'historical-salmon.png';oldpath.write_bytes(oldbytes);assert C.sha(oldpath)=='5de7475813a133bb643fa9de09adbef104c7bd20a572514a297cba54846ceafe'
canonicalpath=C.RES/'canonical-salmon.png'
if not canonicalpath.exists():shutil.copyfile((C.OBJ/C.brief['foodDependency']['artwork']).resolve(),canonicalpath)
assert C.sha(canonicalpath)==C.brief['foodDependency']['sha256']
oldverts=[list(v.co) for v in food.data.vertices];olduv=[list(x.uv) for x in food.data.uv_layers.active.data];oldImageDef={'alphaMode':oldimage.alpha_mode,'colorSpace':oldimage.colorspace_settings.name,'name':oldimage.name}
baseline=[]
for clip in C.rig['clips']:
 for d in ['N','E','S','W']:
  for i in range(12):baseline.append(C.evaluate(sc,asset,arm,food,clip,d,i))
C.N.apply_clip(asset,C.rig,'idle',1,'S',sc)
# This is the frozen single global mapping, in the source food-plane basis.
m=C.mapping;scale=1.25;w,h=m['newFullQuadWorldSizeWhenVisible'];dx,dy=m['newQuadBottomCenterDeltaCameraRightUpWorld']
quad=[[(dx-w/2)/scale,dy/scale,0],[(dx+w/2)/scale,dy/scale,0],[(dx+w/2)/scale,(dy+h)/scale,0],[(dx-w/2)/scale,(dy+h)/scale,0]]
for v,co in zip(food.data.vertices,quad):v.co=co
uvcoords=[(0,0),(1,0),(1,1),(0,1)]
for polygon in food.data.polygons:
 for li in polygon.loop_indices:food.data.uv_layers.active.data[li].uv=uvcoords[food.data.loops[li].vertex_index]
food.data.update()
newimage=bpy.data.images.load(str(canonicalpath),check_existing=False);newimage.alpha_mode=oldImageDef['alphaMode'];newimage.colorspace_settings.name=oldImageDef['colorSpace'];newimage.pack();image_node.image=newimage
oldname=oldimage.name
if oldimage.users==0:bpy.data.images.remove(oldimage)
newimage.name=oldname;newimage.filepath='//round03-resources/canonical-salmon.png'
assert hashlib.sha256(bytes(newimage.packed_file.data)).hexdigest()==C.brief['foodDependency']['sha256']
bpy.context.view_layer.update()
after=C.invariants(sc,asset,arm,food)
if before!=after:
 print('DIFF_OBJECTS',[(k,before['objects'].get(k),after['objects'].get(k)) for k in before['objects'] if before['objects'].get(k)!=after['objects'].get(k)],flush=True)
 print('DIFF_FOOD',before['foodTopology'],after['foodTopology'],flush=True)
 print('FOOD_VALUES',[(k,beforeFood[k],C.object_def(food)[k]) for k in beforeFood if beforeFood[k]!=C.object_def(food)[k]],flush=True)
 print('FOOD_NORMALS',beforeNormals,[list(n.vector) for n in food.data.corner_normals],flush=True)
assert before==after,[(k,before[k]==after[k]) for k in before]
base={'approvedProjectSHA256':C.brief['source']['projectSHA256'],'briefSHA256':C.sha(C.BRIEF),'frozenInvariants':before,'sourceFoodRestVertices':oldverts,'sourceFoodUV':olduv,'sourceFoodImage':{'sha256':C.sha(oldpath),**oldImageDef},'mapping':m,'globalMappedRestQuad':quad,'samples':baseline,'notes':'Food custom source strings are retained unchanged as historical provenance. Actual image-node binding/packed bytes and this fixed mapping are authoritative for the canonical followup.'}
C.write(HERE/'round03-baseline.json',base)
for name in ['camera.json','assetRecord.json','rig.json']:shutil.copyfile(C.OBJ/'candidates/round02'/name,C.OUT/name)
record=json.loads((C.OUT/'assetRecord.json').read_text());record['authoredSourceArtStyleMetadata']=record['artStyle'];record['artStyle']=json.loads((C.OUT/'camera.json').read_text())['artStyle'];record['metadataProvenance']='Original registration, footprint, nominal height, source static socket fields and clip records retained. Static authored sockets are provenance; evaluated actual palms/feet/knife/food behavior are measured in validation.json. artStyle now records unchanged approved round02 native capture settings.';record['heldFoodDependency']={'representation': 'Exact canonical2D RGBA on a fixed native quad, not modeled3D food', 'resource': 'source/round03-resources/canonical-salmon.png', 'sha256': '4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4', 'mapping': 'brief-v3-held-food-semantic-contact.json constraints.heldFoodSemanticMapping', 'validation': 'candidates/round03/validation.json'};C.write(C.OUT/'assetRecord.json',record)
sourceDigest=C.sha(HERE/'round02.blend');assert sourceDigest==C.brief['source']['projectSHA256']
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round03.blend'),compress=True,check_existing=False)
C.write(C.OUT/'dependency-change.json',{'approvedBodySHA256':sourceDigest,'candidateProjectSHA256':C.sha(HERE/'round03.blend'),'canonicalResource':'source/round03-resources/canonical-salmon.png','canonicalSHA256':C.sha(canonicalpath),'historicalControlResource':'source/round03-resources/historical-salmon.png','historicalSHA256':C.sha(oldpath),'allowedChangesOnly':['food image binding/packed bytes','one fixed food rest quad','full food UV0..1'],'unchangedInvariants':True,'globalMappedRestQuad':quad,'originalSourceCustomStringsRetainedAsHistoricalOnly':True,'imageFormat':'Exact731x505 canonicalRGBA, fullUV, no image processing','semanticWidthWorld':m['occupiedWorldWidth']})
print('MATEO_ROUND03_BUILT',C.sha(HERE/'round03.blend'))
