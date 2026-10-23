import bpy,json,math,pathlib,hashlib,sys,argparse
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[2];root=P.parent
parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--asset',action='append');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);OUTPUT=pathlib.Path(args.out).resolve();assert not OUTPUT.exists(),'Audit destination is immutable; choose a new path';OUTPUT.parent.mkdir(parents=True,exist_ok=True)
ids=['belt-corner-n-w','belt-corner-w-n','belt-corner-s-e','belt-corner-e-s','belt-corner-s-w','belt-corner-w-s','belt-start-n','belt-start-e','belt-start-s','belt-start-w','belt-end-n','belt-end-e','belt-end-s','belt-end-w']
if args.asset:ids=args.asset
rows=[]
def authored_matrix(o):
 return authored_matrix(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy()
for asset in ids:
 c=bpy.data.collections['S33_FB_'+asset+'.001'];r=next(o for o in c.all_objects if '__root.' in o.name);ori=next(o for o in c.all_objects if '__orientation.' in o.name);deck=next(o for o in c.all_objects if 'connected_' in o.name);bpy.context.view_layer.update();mat=deck.data.materials[0];uv=deck.data.uv_layers.active;verts=[list(v.co) for v in deck.data.vertices];W=[list(authored_matrix(deck)@v.co) for v in deck.data.vertices];actions=[a for a in bpy.data.actions if a.name.startswith('S33_NATIVE__'+asset+'__running__')];curves=[]
 for a in actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:curves.append({'action':a.name,'slot':a.slots[0].identifier,'path':f.data_path,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points]})
 endpoints={}
 for u in [0,1]:
  vset=sorted(set(me.vertices[me.loops[li].vertex_index].index for me in [deck.data] for li,x in enumerate(uv.data) if abs(x.uv.x-u)<1e-5));points=[Vector(W[i]) for i in vset]
  endpoints[str(u)]={'vertexIndices':vset,'points':[list(x) for x in points],'center':[sum(x[i] for x in points)/len(points) for i in range(3)] if points else None}
 obj=[]
 for o in c.all_objects:
  if o.type=='MESH':obj.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'bounds':[[min((authored_matrix(o)@v.co)[i] for v in o.data.vertices) for i in range(3)],[max((authored_matrix(o)@v.co)[i] for v in o.data.vertices) for i in range(3)]],'materials':[m.name for m in o.data.materials]})
 catalog=json.loads((root/asset/'inputs/catalog-object.json').read_text());rows.append({'asset':asset,'collection':c.name,'rootMatrix':[list(x) for x in r.matrix_world],'intrinsicRotationRadians':list(ori.rotation_euler),'deck':deck.name,'deckAuthoredMatrix':[list(x) for x in authored_matrix(deck)],'storedWorldMatrix':[list(x) for x in deck.matrix_world], 'matrixMethod':'Exact authored parent basis chain incl parent inverse; saved hidden collection world matrices may be stale, never use as evaluated truth.','deckVertices':len(verts),'deckLocalBounds':[[min(x[i] for x in verts) for i in range(3)],[max(x[i] for x in verts) for i in range(3)]],'deckWorldBounds':[[min(x[i] for x in W) for i in range(3)],[max(x[i] for x in W) for i in range(3)]],'deckUVEndpoints':endpoints,'uvValues':[list(x.uv) for x in uv.data],'nativeActionBound':bool(mat.node_tree.animation_data and mat.node_tree.animation_data.action),'authoredPhaseCurves':curves,'geometry':obj,'catalogCapture':{k:catalog[k] for k in ['frameSize','root','sourceScale']},'clip':{k:catalog['clips'][0][k] for k in ['id','frames','fps','loop']}})
OUTPUT.write_text(json.dumps({'sourceSHA256':hashlib.sha256((P/'source/resources/original-library.blend').read_bytes()).hexdigest(),'rows':rows},indent=2))
for x in rows:print(x['asset'],'intrinsic',x['intrinsicRotationRadians'][2],'deckVertices',x['deckVertices'],'U0',x['deckUVEndpoints']['0']['center'],'U1',x['deckUVEndpoints']['1']['center'],'nativeBound',x['nativeActionBound'],'phaseCurves',len(x['authoredPhaseCurves']),'geometry',[(o['name'].split('__')[-1],o['vertices']) for o in x['geometry']])
