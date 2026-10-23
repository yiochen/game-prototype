"""Clean saved-project control captures; never modifies the saved blend or submitted pixels."""
import bpy,runpy,json,hashlib,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;O=S.parent.parent;C=O/'candidates/round-01';N=runpy.run_path(str(S/'reproduce.py'));sc=bpy.context.scene
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for clip,d,f in [('static',d,1) for d in 'NESW']+[('idle','S',1),('idle','S',7),('idle','S',13)]:
 N['apply_clip'](clip,d,f);p=C/'control'/clip/d/f'{f-1:03}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);root=bpy.data.objects['Coral ground root'];records.append({'clip':clip,'direction':d,'index':f-1,'path':str(p.relative_to(O)),'sourceSHA256':sha(S/'round-01.blend'),'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'camera':N['camera_record'](sc),'filterSize':sc.render.filter_size,'engine':sc.render.engine,'cyclesSamples':sc.cycles.samples})
import bmesh
meshes=[]
for o in bpy.data.collections['Coral warm soft native'].all_objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);meshes.append({'name':o.name,'role':o.get('role'),'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'degenerateFaces':sum(p.area<1e-12 for p in o.data.polygons),'vertexAttributes':[{'name':a.name,'domain':a.domain,'type':a.data_type} for a in o.data.color_attributes],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'parent':o.parent.name if o.parent else None});bm.free()
(C/'control-records.json').write_text(json.dumps({'sourceSHA256':sha(S/'round-01.blend'),'recipeSHA256':sha(S/'reproduce.py'),'blenderVersion':bpy.app.version_string,'captureRecords':records,'nativeTopology':meshes,'libraries':[x.filepath for x in bpy.data.libraries],'fileImages':[x.filepath for x in bpy.data.images if x.source=='FILE'],'renderEngine':sc.render.engine},indent=2)+'\n')
print('Saved source controls',len(records))
