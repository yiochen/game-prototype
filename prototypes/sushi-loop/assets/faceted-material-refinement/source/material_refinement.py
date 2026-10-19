"""Native material-only follow-up to the selected Faceted study. Author via MCP.
The prior frozen study remains unchanged. Render this saved project via --render.
"""
import bpy, copy, hashlib, json, math, sys
from pathlib import Path
DIRECTIONS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
WOOD_MULTIPLIER=.42
RAIL_SRGB='#966B60'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def linear_hex(color):
 values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
 return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]+[1]
def phase(scene,value):
 found=[]
 for mat in {slot.material for o in scene.objects if o.type=='MESH' for slot in o.material_slots if slot.material}:
  for n in mat.node_tree.nodes:
   if n.type=='VALUE' and n.label=='Deck travel phase':n.outputs[0].default_value=value;found.append(mat.name)
 return sorted(found)
def clone_scene(source,name):
 s=source.copy();s.name=name;assert s.collection!=source.collection
 objects={}
 for old in list(s.collection.objects):
  new=old.copy()
  if old.data:new.data=old.data.copy()
  new.name=name+' '+old.name
  s.collection.objects.unlink(old);s.collection.objects.link(new);objects[old]=new
 mats={}
 for old,new in objects.items():
  new.parent=objects.get(old.parent)
  for slot in new.material_slots:
   m=slot.material
   if m:
    if m not in mats:
     mats[m]=m.copy();mats[m].name=name+' '+m.name
     if mats[m].node_tree.animation_data:mats[m].node_tree.animation_data_clear()
    slot.material=mats[m]
 s.camera=objects[source.camera];s.world=source.world.copy()
 s['studyRoot']=objects[bpy.data.objects[source['studyRoot']]].name
 s.compositing_node_group=source.compositing_node_group.copy()
 for n in s.compositing_node_group.nodes:
  if n.type=='R_LAYERS':n.scene=s
 bpy.data.objects[s['studyRoot']].rotation_euler.z=0
 phase(s,0)
 return s,list(mats.values())
def build(repo):
 repo=Path(repo);old=repo/'prototypes/sushi-loop/assets/environment-lighting-study';folder=repo/'prototypes/sushi-loop/assets/faceted-material-refinement';previous=bpy.context.window.scene
 m=copy.deepcopy(json.loads((old/'manifest.json').read_text()));scenes=[];changes=[]
 try:
  for subject in m['subjects']:
   original=next(v for v in subject['variants'] if v['id']=='faceted')
   subject['variants']=[];subject['reviewVariantIds']=['faceted','faceted-tuned'];subject['selectedLighting']='faceted'
   for tuned in (False,True):
    v=copy.deepcopy(original);v['id']='faceted-tuned' if tuned else 'faceted';name='S33 material refinement '+subject['id']+' '+v['id']
    s,mats=clone_scene(bpy.data.scenes[original['scene']],name);scenes.append(s);s['lightingStudyVariant']=v['id']
    if tuned:
     for mat in mats:
      is_wood=subject['id']=='crate-wood' and 'wood' in mat.name.lower();is_rail='S33_FB_red' in mat.name
      if not(is_wood or is_rail):continue
      output=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
      shader=output.inputs['Surface'].links[0].from_node;assert shader.type=='BSDF_PRINCIPLED'
      low=next(n for n in mat.node_tree.nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY' and n.inputs[2].is_linked and n.inputs[2].links[0].from_node.type=='VALTORGB')
      assert not low.inputs[1].is_linked
      before=list(low.inputs[1].default_value);after=[v*WOOD_MULTIPLIER for v in before[:3]]+[1] if is_wood else linear_hex(RAIL_SRGB)
      low.inputs[1].default_value=after;shader.inputs['Roughness'].default_value=1;shader.inputs['Specular IOR Level'].default_value=0
      mat['materialRefinement']='wood-linear-albedo-0.42' if is_wood else 'muted-clay-'+RAIL_SRGB
      changes.append({'subject':subject['id'],'material':mat.name,'kind':'wood' if is_wood else 'rail','beforeLinear':before,'afterLinear':after,'roughness':1,'specular':0})
    v['scene']=s.name;v['name']=('Faceted · matte wood' if subject['id']=='crate-wood' else 'Faceted · muted clay rails') if tuned else 'Faceted · before materials'
    v['description']=('Same chosen Faceted light. Matte, lower-albedo crate wood.' if subject['id']=='crate-wood' else 'Same chosen Faceted light. Muted clay rails; original deck and legs.') if tuned else ('Selected 140 W lighting with the original pale wood.' if subject['id']=='crate-wood' else 'Selected 140 W lighting with the original bright red rails.')
    v['materialRefinement']=bool(tuned)
    for d,c in v['captures'].items():
     c['image']=f'sprites/{subject["id"]}/{v["id"]}-{d}.png'
     if c.get('frames'):c['frames']=[c['image']]+[f'frames/{subject["id"]}/{v["id"]}-{f:03d}.png' for f in range(1,24)]
    subject['variants'].append(v)
   subject['source']={'blend':'source/faceted-materials.blend','recipe':'source/material_refinement.py'}
   if subject.get('maskScene'):
    mask,_=clone_scene(bpy.data.scenes[subject['maskScene']],'S33 material refinement '+subject['id']+' mask');scenes.append(mask);subject['maskScene']=mask.name
   if subject['id']=='crate-wood':subject['description']='Selected Faceted lighting: compare the original pale boards with matte, lower-albedo wood. The lighting, facets, lower shading, geometry and projection are unchanged.'
   elif subject['id']=='belt-straight':subject['description']='Selected Faceted lighting: compare the bright red rails with a muted clay finish. The charcoal moving deck and full-width shape are unchanged.'
   else:subject['description']='The same joined L and synchronized 24-frame deck animation, now comparing original red rails with muted clay rails under the selected Faceted lighting.'
  m['version']=2;m['selectedLighting']='faceted';m['status']='faceted-selected-material-refinement-awaiting-review'
  m['materialRefinement']={'woodScope':'crate-wood only; belt legs unchanged','woodLinearAlbedoMultiplier':WOOD_MULTIPLIER,'railSRGB':RAIL_SRGB,'roughness':1,'specular':0,'lightsUnchanged':True,'geometryUnchanged':True,'lowerRampUnchanged':True,'changes':changes}
  m['source']={'blend':'source/faceted-materials.blend','recipe':'source/material_refinement.py','productionBlendSHA256':m['source']['productionBlendSHA256'],'previousStudySHA256':sha(old/'source/environment-lighting.blend'),'previousStudyManifestSHA256':sha(old/'manifest.json')}
  path=folder/'source/faceted-materials.blend';bpy.data.libraries.write(str(path),set(scenes),fake_user=True,compress=True)
  m['source']['sha256']=sha(path);m['source']['recipeSHA256']=sha(__file__);write(folder/'manifest.json',m)
  return {'path':str(path),'scenes':len(scenes),'changes':len(changes),'sha256':m['source']['sha256']}
 finally:bpy.context.window.scene=previous

def render(folder,subjects=None,preview=False):
 folder=Path(folder);m=json.loads((folder/'manifest.json').read_text());records=[];tag='-'.join(subjects or ['all'])
 for subject in m['subjects']:
  if subjects and subject['id'] not in subjects:continue
  v=next(v for v in subject['variants'] if v['id']=='faceted-tuned');scene=bpy.data.scenes[v['scene']];bpy.context.window.scene=scene
  plan=[(d,0,c['image']) for d,c in v['captures'].items()]
  if preview:plan=[('S',0,v['captures']['S']['image'])]
  else:plan += [('S',f,p) for f,p in enumerate(v['captures'].get('S',{}).get('frames',[])) if f]
  for d,f,path in plan:
   bpy.data.objects[scene['studyRoot']].rotation_euler.z=DIRECTIONS[d];names=phase(scene,-7*f/24);scene.view_layers[0].update();target=folder/path;target.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(target);bpy.ops.render.render(write_still=True,scene=scene.name)
   records.append({'subject':subject['id'],'variant':v['id'],'direction':d,'frame':f,'phase':-7*f/24,'phaseMaterials':names,'image':path,'sha256':sha(target),'geometrySHA256':scene['studyGeometrySHA256'],'camera':v['camera']})
   write(folder/f'capture-status-{tag}.json',{'state':'rendering','done':len(records),'current':[subject['id'],d,f]})
 write(folder/f'captures-{tag}.json',{'sourceSHA256':m['source']['sha256'],'records':records});write(folder/f'capture-status-{tag}.json',{'state':'complete','done':len(records)})
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--render',type=Path);p.add_argument('--subjects',nargs='+');p.add_argument('--preview',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if args.render:render(args.render,args.subjects,args.preview)
