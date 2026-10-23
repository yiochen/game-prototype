"""Portable food-only replacement. Run with background Blender --python this file."""
import bpy,sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.dont_write_bytecode=True
from common import *
BRIEF=P/'dependencies/frozen-brief.json';SOURCE=P/'dependencies/approved-body.blend';FOOD=P/'dependencies/dish-salmon.png'
assert sha(BRIEF)=='d500baed2708cdd42bf5830b8bf373dc9f589292d0c333d5e0e1f5341d005107'
assert sha(SOURCE)=='6786550a8d05b9d4563c038cd4d3614ce7c189a5a1e40813e2f536ac67c2709c'
assert sha(FOOD)=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
assert not (BASE/'source/round-02.blend').exists(),'Never overwrite an existing round source'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));sc=bpy.context.scene
record,root,col,arm,foodroot,plane=context();asset={'root':root,'collection':col,'armature':arm}
original=baseline();frozen=json.loads((P/'dependencies/frozen-native-baseline.json').read_text());presentation_source=presentation()
base_checks={k:original[k]==frozen[k] for k in ['bodyAndKnifeMeshes','bodyAndKnifeMeshCount','boneRestSHA256','boneRest','actions','materials','sourceObjectTransforms']}
write(OUT/'source-baseline.json',original);write(OUT/'source-presentation.json',presentation_source);write(OUT/'source-baseline-comparison.json',{'ok':all(base_checks.values()),'checks':base_checks,'sourceSHA256':sha(SOURCE),'frozenBaselineSHA256':sha(P/'dependencies/frozen-native-baseline.json')})
assert all(base_checks.values()),base_checks
source_phases=[]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  for index in range(12):source_phases.append(phase(clip,direction,index))
compact(OUT/'source-phases.json',source_phases);print('SOURCE_PHASES',len(source_phases),flush=True)
# Exactly the frozen canonical full-UV/aspect mapping. Keep D0.6 source offset and all drivers untouched.
frozen_brief=json.loads(BRIEF.read_text());mapping=frozen_brief['constraints']['measuredNativeContract']['nativeContract']['singleCanonicalMapping']
for v,co in zip(plane.data.vertices,mapping['verticesLocal']):v.co=co
for loop in plane.data.loops:plane.data.uv_layers.active.data[loop.index].uv=mapping['UV'][loop.vertex_index]
plane.data.update();image=next(n.image for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
image_name=image.name;alpha=image.alpha_mode;colorspace=image.colorspace_settings.name
image.unpack(method='REMOVE');image.filepath=str(FOOD);image.reload();image.pack();image.filepath='//round-02-food/dependencies/dish-salmon.png'
assert image.name==image_name and image.alpha_mode==alpha=='STRAIGHT' and image.colorspace_settings.name==colorspace=='sRGB'
assert list(image.size)==[731,505] and sha(FOOD)==__import__('hashlib').sha256(image.packed_file.data).hexdigest()
na.apply_clip(asset,record,'idle',1,'S',sc);bpy.context.view_layer.update()
modified=baseline();post=presentation();static_checks={k:original[k]==modified[k] for k in ['bodyAndKnifeMeshes','bodyAndKnifeMeshCount','boneRestSHA256','boneRest','actions','materials','sourceObjectTransforms']};static_checks['presentation']=post==presentation_source
write(OUT/'candidate-baseline-presave.json',modified);write(OUT/'candidate-presentation-presave.json',post);write(OUT/'native-preservation-presave.json',{'ok':all(static_checks.values()),'checks':static_checks,'bodyAndKnifeMeshCount':len(modified['bodyAndKnifeMeshes']),'actionCount':len(modified['actions']),'materialCount':len(modified['materials']),'chosenGlobalDepthWorld':.6,'depthDriversUnchanged':post['drivers']==presentation_source['drivers'],'foodImageSHA256':__import__('hashlib').sha256(image.packed_file.data).hexdigest(),'foodImageSize':list(image.size),'foodVerticesLocal':[list(v.co) for v in plane.data.vertices],'foodUV':[list(v.uv) for v in plane.data.uv_layers.active.data]})
assert all(static_checks.values()),static_checks
recipe={'asset':'chef-dalia','round':'round-02','scope':'Food-only canonical packed image/fullUV/aspect mapping; approved native body locked','frozenBrief':'source/round-02-food/dependencies/frozen-brief.json','frozenBriefSHA256':sha(BRIEF),'approvedBody':'source/round-02-food/dependencies/approved-body.blend','approvedBodySHA256':sha(SOURCE),'canonicalFood':'source/round-02-food/dependencies/dish-salmon.png','canonicalFoodSHA256':sha(FOOD),'project':'source/round-02.blend','recipeScript':'source/round-02-food/build.py','renderScript':'source/round-02-food/render.py','nativeRuntime':'source/round-02-food/native_actions.py','scene':sc.name,'collection':col.name,'root':root.name,'armature':arm.name,'plane':plane.name,'foodRoot':foodroot.name,'mapping':mapping,'globalDepthWorld':.6,'depthPolicy':'Retain exact approved source D0.6 globally. No driver changes and no per-view or per-pose fitting.','presentation':presentation_source,'sourceSupportMeasuredFromActualUV':'source semantic alpha128 pixel CENTER and affine source crop mapping; canonical alpha128 fullUV point uses fixed rebase','legacyRootMetadata':'Original root custom-property food source strings are historical provenance and remain unchanged under strict native preservation. Actual active dependency is proved by packed bytes and this recipe.'}
write(P/'recipe.json',recipe)
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-02.blend'),compress=True)
print('FOOD_ONLY_PROJECT_READY',sha(BASE/'source/round-02.blend'),flush=True)
