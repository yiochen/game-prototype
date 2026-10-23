import bpy,json,pathlib,hashlib
B=pathlib.Path(__file__).parent;s=bpy.context.scene
for l in s.view_layers[0].layer_collection.children:l.exclude=False;l.hide_viewport=False
for c in s.collection.children:c.hide_viewport=False
for o in s.objects:o.hide_viewport=False;o.hide_set(False)
s.frame_set(1);s.view_layers[0].update();dep=bpy.context.evaluated_depsgraph_get()
def sig(v):return hashlib.sha256(json.dumps(v,separators=(',',':')).encode()).hexdigest()
rows=[]
for o in s.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dep);m=ev.to_mesh();attrs=[]
 for a in m.color_attributes:attrs.append({'name':a.name,'domain':a.domain,'dataType':a.data_type,'count':len(a.data),'rgbaSHA256':sig([list(v.color) for v in a.data])})
 rows.append({'object':o.name,'mesh':o.data.name,'meshUsers':o.data.users,'materials':[p.name for p in o.data.materials],'evaluatedWorldVerticesSHA256':sig([list(ev.matrix_world@v.co) for v in m.vertices]),'evaluatedCornerNormalsSHA256':sig([list(ev.matrix_world.to_3x3()@n.vector) for n in m.corner_normals]),'albedoResources':attrs});ev.to_mesh_clear()
(B/'evidence/resource-signatures.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256((B/'resources/source.blend').read_bytes()).hexdigest(),'staticFrame':s.frame_current,'objects':rows,'materialGraphEvidence':'native-inspection.json materials (actual full node inputs and links); signatures bind source vertex albedo/custom-normal resources, not labels alone','imageAndLinkedLibraries':{'images':[i.filepath for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]},'noSourceSave':True},indent=2)+'\n')
