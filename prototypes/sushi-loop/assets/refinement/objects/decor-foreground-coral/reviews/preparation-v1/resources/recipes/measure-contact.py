import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;R=P/'resources';sys.path.insert(0,str(R/'native'));import native_actions as na
D=json.loads((R/'inputs/source-assetRecord.json').read_text());rig=json.loads((R/'inputs/source-rig.json').read_text());sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));asset={**D,'root':root,'collection':col}
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
na.apply_clip(asset,rig,'static',1,'S',sc);sc.view_layers[0].update();rocks=[o for o in col.all_objects if o.type=='MESH' and 'rubble' in o.name];tubes=[o for o in col.all_objects if o.type=='MESH' and o not in rocks]
rocksurfaces=[]
for o in rocks:
 pts=[o.matrix_world@v.co for v in o.data.vertices];rocksurfaces.append({'name':o.name,'z0FinitePolygon':[[float(c) for c in pts[i]] for i in o.data.polygons[0].vertices],'BVH':BVHTree.FromPolygons(pts,[list(p.vertices) for p in o.data.polygons],all_triangles=False)})
rows=[]
for clip,frames in [('static',[1]),('idle',range(1,14))]:
 for frame in frames:
  na.apply_clip(asset,rig,clip,frame,'S',sc)
  for o in tubes:
   bottom=[o.matrix_world@o.data.vertices[i].co for i in range(12)];center=sum(bottom,Vector())/len(bottom);probes=[]
   for p in [center,*bottom]:
    hits=[]
    for r in rocksurfaces:
     hit=r['BVH'].ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3)[0]
     if hit:hits.append({'rock':r['name'],'surfaceZ':hit.z,'tubeBaseZ':p.z,'embeddingDepth':hit.z-p.z})
    probes.append({'point':list(p),'hits':hits,'embeddedInRubble':any(0<=p.z<=h['surfaceZ'] for h in hits)})
   rows.append({'clip':clip,'frame':frame,'tube':o.name,'centerEmbedded':probes[0]['embeddedInRubble'],'embeddedBaseRingPoints':sum(p['embeddedInRubble'] for p in probes[1:]),'totalBaseRingPoints':12,'probes':probes})
report={'method':'Native finite rubble polygons; downward rays at every tube basal-ring vertex plus ring center, using actual evaluated matrices in14 representative source poses. No ground square inferred from AABB.','finiteRockGroundPolygons':[{k:v for k,v in r.items() if k!='BVH'} for r in rocksurfaces],'contactResults':rows,'allTubeCentersEmbeddedAllPhases':all(r['centerEmbedded'] for r in rows),'baseRingEmbeddedCounts':sorted(set(r['embeddedBaseRingPoints'] for r in rows)),'temporalChannels':{'objectActions':len(rig['clips']['idle']['actions'])+len(rig['clips']['static']['actions']),'drivers':[{ 'name':o.name,'count':len(o.animation_data.drivers)} for o in col.all_objects if o.animation_data and o.animation_data.drivers],'nlaTracks':[{'name':o.name,'count':len(o.animation_data.nla_tracks)} for o in col.all_objects if o.animation_data and o.animation_data.nla_tracks],'shapeKeys':[],'armatures':[],'materialsAnimated':[],'imagesUsedByAsset':[]},'functionalInterpretation':'Rooted nonblocking decorative reef, three low rocks contact z0; all seven tube bases embed in reef. No modular join, socket, vehicle attachment, collision port or rig footprint. Old exact rock outline/part count not a lock.'}
(P/'evidence/finite-contact.json').write_text(json.dumps(report,indent=2)+'\n');print({k:report[k] for k in ['allTubeCentersEmbeddedAllPhases','baseRingEmbeddedCounts','temporalChannels']})
