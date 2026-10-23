import bpy,json,hashlib,pathlib
B=pathlib.Path(__file__).resolve().parent.parent

def plain(x):
 if isinstance(x,(str,bool,int,float)) or x is None:return x
 return [plain(y) for y in x]
def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':'),sort_keys=True).encode()).hexdigest()
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));root=bpy.data.objects['chef_mateo__ground_root.001'];col=next(c for c in bpy.data.collections if root.name in c.objects);meshes={};rests={}
 for o in col.all_objects:
  if o.type=='MESH':
   meshes[o.name]=digest({'coordinates':[plain(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'uvs':[[plain(v.uv) for v in uv.data] for uv in o.data.uv_layers],'groups':[(g.name,g.index) for g in o.vertex_groups],'weights':[[(g.group,g.weight) for g in v.groups] for v in o.data.vertices],'materials':[m.name if m else None for m in o.data.materials],'parent':o.parent.name if o.parent else None,'matrixLocal':plain(o.matrix_local)})
  if o.type=='ARMATURE':rests[o.name]={z.name:{'matrixLocal':plain(z.matrix_local),'parent':z.parent.name if z.parent else None,'deform':z.use_deform} for z in o.data.bones}
 return {'meshes':meshes,'restBones':rests,'packedImages':[{'name':i.name,'sha256':hashlib.sha256(i.packed_file.data).hexdigest()} for i in bpy.data.images if i.packed_file]}
a=snapshot(B/'source/round01.blend');b=snapshot(B/'source/round02.blend');same=[k for k in a['meshes'] if k in b['meshes'] and a['meshes'][k]==b['meshes'][k]];changed=[k for k in a['meshes'] if k in b['meshes'] and a['meshes'][k]!=b['meshes'][k]];removed=sorted(set(a['meshes'])-set(b['meshes']));added=sorted(set(b['meshes'])-set(a['meshes']));report={'oldProjectSHA256':hashlib.sha256((B/'source/round01.blend').read_bytes()).hexdigest(),'newProjectSHA256':hashlib.sha256((B/'source/round02.blend').read_bytes()).hexdigest(),'unchangedMeshesIncludingCoordinatesWeightsUVsTransformsMaterials':len(same),'unchangedMeshNames':same,'changedSharedMeshes':changed,'removedMeshes':removed,'addedMeshes':added,'restBonesExact':a['restBones']==b['restBones'],'packedImagesExact':a['packedImages']==b['packedImages'],'bodyScopePass':not changed and all(any(tag in n for tag in ['band','headband']) for n in removed+added)};(B/'reviews/round02-independent-scope-evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='unchangedMeshNames'},indent=2))
