"""Independent source-only audit of saved .blend, no scene or art mutation saved."""
import bpy,json,pathlib,hashlib,math
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parent;OBJ=P.parent;OUT=OBJ/'candidates/round-02';source=P/'round-02.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;root=bpy.data.objects['garbage-sofa__root'];coll=next(c for c in bpy.data.collections if root in list(c.objects));rig=json.loads((P/'resources/original-rig.json').read_text());ref=json.loads((P/'resources/source-motion-reference.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(m):return [[float(v) for v in r] for r in m]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:yield curve
result={'source':str(source.relative_to(OBJ)),'sourceSHA256':sha(source),'blender':bpy.app.version_string,'actionComparison':[],'topology':[],'contacts':[],'materialRecords':[],'objects':[]}
for clip,rr in rig['clips'].items():
 for t,original in zip(rr['actions'],ref['actions'][clip]):
  a=bpy.data.actions[t['action']];cs=[{'path':fc.data_path,'index':fc.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation} for k in fc.keyframe_points]} for fc in curves(a)]
  result['actionComparison'].append({'clip':clip,'owner':t['ownerName'],'action':a.name,'sourceCurveSHA256':original['sha256'],'actualCurveSHA256':digest(cs),'identical':digest(cs)==original['sha256']})
# The saved .blend is in its assembled idle/S pose.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
for o in coll.all_objects:
 result['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':rows(o.matrix_world),'materialNames':[m.name for m in o.data.materials] if o.type in ['MESH','CURVE'] else [],'semanticCarrier':o.get('semantic_carrier',o.get('semantic_source_role'))})
 if o.type in ['MESH','CURVE']:
  ev=o.evaluated_get(dg);me=ev.to_mesh();edges={tuple(sorted(e.vertices)):0 for e in me.edges}
  for p in me.polygons:
   for pair in p.edge_keys:edges[tuple(sorted(pair))]=edges.get(tuple(sorted(pair)),0)+1
  result['topology'].append({'name':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'boundaryEdges':sum(v==1 for v in edges.values()),'nonmanifoldEdges':sum(v!=2 for v in edges.values()),'zeroAreaFaces':sum(p.area<1e-10 for p in me.polygons)})
  if o.name.startswith('foot_') or o.name.endswith('__grounded_rubbish'):
   ps=[ev.matrix_world@v.co for v in me.vertices];floorpoints=[list(p) for p in ps if abs(p.z)<=.002];result['contacts'].append({'name':o.name,'minZ':min(p.z for p in ps),'groundPointsWithin002':floorpoints,'bounds':{'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}})
  ev.to_mesh_clear()
for m in bpy.data.materials:
 if not m.use_nodes:continue
 result['materialRecords'].append({'name':m.name,'nodes':[{'type':n.bl_idname,'name':n.name,'object':n.object.name if n.type=='TEX_COORD' and n.object else None,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'values':{s.name:list(s.default_value) if not isinstance(s.default_value,(int,float,str,bool)) else s.default_value for s in n.inputs if hasattr(s,'default_value') and not isinstance(s.default_value,bpy.types.ID)}} for n in m.node_tree.nodes],'animated':bool(m.animation_data or m.node_tree.animation_data),'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links]})
result['resources']={'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'externalObjectData':[o.name for o in coll.all_objects if o.library or (o.data and o.data.library)],'fonts':[f.filepath for f in bpy.data.fonts]}
result['lightRecords']=[{'name':o.name,'matrixWorld':rows(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in sc.objects if o.type=='LIGHT'];result['allSourceActionCurvesIdentical']=all(a['identical'] for a in result['actionComparison']);result['sourceUnchangedAfterAudit']=sha(source)==result['sourceSHA256']
(OUT/'source-only-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('SOURCE_AUDIT',result['allSourceActionCurvesIdentical'],len(result['objects']),len(result['contacts']))
