import bpy,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];R=B/'source/resources/approved-human-v3';rig=json.loads((R/'rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in bpy.data.collections if root in list(c.all_objects));sc=bpy.data.scenes.new('ApprovedHumanPhysicalAudit');sc.collection.children.link(col);col.hide_viewport=False;col.hide_render=False;bpy.context.window.scene=sc
sp=importlib.util.spec_from_file_location('human_native_actions',R/'native_actions.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
records=[]
for frame in [1,12]:
 mod.apply_clip({'root':root,'collection':col},rig,'stand',frame,'S',sc);root.location=(0,0,0);root.rotation_euler=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();a=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices];a.append({'name':o.name,'visibleRenderMesh':not o.hide_render,'bounds':[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]});e.to_mesh_clear()
 visible=[o for o in a if o['visibleRenderMesh']];bounds=[[min(o['bounds'][0][i] for o in visible) for i in range(3)],[max(o['bounds'][1][i] for o in visible) for i in range(3)]];feet=[o for o in visible if any(s in o['name'].lower() for s in ['foot','sole'])];records.append({'clip':'stand','frame':frame,'rootMatrix':[list(r) for r in root.matrix_world],'rootScale':list(root.scale),'visibleBounds':bounds,'visibleHeight':bounds[1][2]-bounds[0][2],'visibleFootMeshes':feet,'minVisibleFootZ':min(o['bounds'][0][2] for o in feet),'allMeshAudit':a})
p=B/'candidates/round-04/approved-human-physical-audit.json';p.write_text(json.dumps({'sourceProject':'source/resources/approved-human-v3/customer-rosa-approved.blend','sourceSHA256':hashlib.sha256((R/'customer-rosa-approved.blend').read_bytes()).hexdigest(),'nativeCoordinateUnits':'Original world units, root at0; no geometry scaling or per-view fit applied. Consumer catalog uses exact current atlas frame/scale/35degreecamera as recorded separately.','measurements':records,'legacyNativeContext':'B176nativeRosa55degree environment reference is separate olderbody(height1.5125), not current approvedbody or pixelparity. Current publishedsprites primary consumer reference.','expectedGeometryContractHeightFromCoordinator':1.2746186554},indent=2));print('APPROVED_HUMAN',[(r['frame'],r['visibleHeight'],r['minVisibleFootZ']) for r in records])
