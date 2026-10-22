import bpy,json,pathlib,hashlib
from mathutils import Vector,Matrix
O=pathlib.Path(__file__).resolve().parent;R=O/'resources';F=R/'frozen-main-v1';s=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];root.location=(0,0,0);root.rotation_euler=(0,0,0)
actions=json.loads(root['nativeActions'])
for owner,an in actions['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def bb(p):return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
parts=[]
for o in s.objects:
 if o.type!='MESH':continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();ps=[eo.matrix_world@v.co for v in me.vertices];faces=[]
 if 'collector_contact_seat' in o.name:
  for p in me.polygons:
   n=(eo.matrix_world.to_3x3().inverted().transposed()@p.normal).normalized()
   if n.y<-.999:faces.append({'normal':list(n),'bounds':bb([ps[i] for i in p.vertices]),'vertices':[list(ps[i]) for i in p.vertices],'area':p.area})
 parts.append({'name':o.name,'parent':o.parent.name if o.parent else None,'bounds':bb(ps),'finiteFaces':faces});eo.to_mesh_clear()
mount=bpy.data.objects['MOUNT__sub-collector-inlet'];manifest=json.loads((F/'manifest.json').read_text());hashes=[{'path':x['path'],'expected':x['sha256'],'actual':hashlib.sha256((F/x['path']).read_bytes()).hexdigest()} for x in manifest['files']]
(O/'frozen-main-native-audit.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256((F/'project.blend').read_bytes()).hexdigest(),'freezeSHA256':hashlib.sha256((F/'body-freeze.json').read_bytes()).hexdigest(),'manifestHashes':hashes,'allManifestHashesMatch':all(x['actual']==x['expected'] for x in hashes),'scene':s.name,'root':root.name,'nativeActions':actions,'collectorMountMatrix':[list(r) for r in mount.matrix_local],'parts':parts},indent=2)+'\n')
print(json.dumps({'scene':s.name,'collectorMountMatrix':[list(r) for r in mount.matrix_local],'parts':[x for x in parts if any(t in x['name'] for t in ['lamp','light','collector','skid'])]},indent=2))
