import bpy,sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;out=[]
for label,file,rootName in [('original',R/'source/original-library.blend','wreck-corner__root.001'),('middle02',R/'canonical/wreck-middle/source/round-02.blend','wreck-middle__root'),('edge02',R/'canonical/wreck-edge/source/round-02.blend','wreck-edge__root')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));root=bpy.data.objects[rootName];owned=[root]+list(root.children_recursive);mats={m for o in owned if hasattr(o.data,'materials')for m in o.data.materials if m};images=[];groups=[];objects=[];seen=set()
 def tree(t):
  if t is None or t.as_pointer()in seen:return
  seen.add(t.as_pointer())
  for n in t.nodes:
   if hasattr(n,'image')and n.image:images.append({'name':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file)})
   if hasattr(n,'node_tree')and n.node_tree:groups.append(n.node_tree.name);tree(n.node_tree)
   if hasattr(n,'object')and n.object:objects.append(n.object.name)
 for m in mats:tree(m.node_tree)
 out.append({'source':label,'sourceSHA256':hashlib.sha256(file.read_bytes()).hexdigest(),'root':rootName,'rootParent':root.parent.name if root.parent else None,'ownedObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'animationData':bool(o.animation_data),'constraints':[c.type for c in o.constraints],'instanceCollection':o.instance_collection.name if o.instance_collection else None,'modifiers':[{'type':m.type,'name':m.name}for m in o.modifiers]}for o in owned],'ownedMaterialCount':len(mats),'ownedShaderImages':images,'ownedShaderGroups':groups,'ownedShaderObjectReferences':objects,'externalLibraries':[l.filepath for l in bpy.data.libraries],'ownedArmatures':[o.name for o in owned if o.type=='ARMATURE'],'scope':'Only actual own/root descendants and active material resources; unused other source-library assets are not dependencies of this source baseline.'})
(R.parent/'actual-used-resource-closure.json').write_text(json.dumps({'pathBase':'object-root','blender':bpy.app.version_string,'sources':out},indent=2)+'\n')
print('RESOURCE_AUDIT',[(x['source'],len(x['ownedObjects']),x['ownedShaderImages'],x['externalLibraries'])for x in out])
