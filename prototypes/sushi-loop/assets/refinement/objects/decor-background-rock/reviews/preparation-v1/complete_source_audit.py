"""Independent extra source ownership/temporal audit, no saved source edits."""
import bpy,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent
sc=bpy.context.scene;col=bpy.data.collections['S33 production concept cobalt-shelf.001'];own=list(col.all_objects);root=next(o for o in own if o.get('production_id')=='decor-background-rock')
def ancestry(lc):
    hit=lc.collection==col
    for child in lc.children:hit=ancestry(child) or hit
    if hit:lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False;lc.collection.hide_render=False
    return hit
for vl in sc.view_layers:ancestry(vl.layer_collection)
for o in own:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
root.rotation_euler.z=0;bpy.context.view_layer.update()
owners={}
def add(o,label):
    if o is None:return
    owners[o.as_pointer()]=(o,label)
def tree(t,label):
    if t is None or t.as_pointer() in owners:return
    add(t,label)
    for n in t.nodes:
        if n.type=='GROUP':tree(n.node_tree,label+'/'+n.name)
for o in own:
    add(o,'object/'+o.name);add(o.data,'data/'+o.name)
    if o.type=='MESH':
        add(o.data.shape_keys,'shapeKeys/'+o.name)
        for m in o.data.materials:
            add(m,'material/'+m.name);tree(m.node_tree,'materialTree/'+m.name)
add(sc,'scene');add(sc.world,'world');tree(sc.world.node_tree,'worldTree');tree(sc.compositing_node_group,'compositor')
for o in sc.objects:
    if o.type in ['LIGHT','CAMERA']:add(o,o.type+'/'+o.name);add(o.data,o.type+'Data/'+o.name)
aud=[]
for owner,label in owners.values():
    ad=getattr(owner,'animation_data',None)
    aud.append({'label':label,'name':owner.name,'activeAction':ad.action.name if ad and ad.action else None,'nlaCount':len(ad.nla_tracks) if ad else 0,'drivers':[f.data_path for f in ad.drivers] if ad else []})
matowners={m.name:[o.name for o in bpy.data.objects if o.type=='MESH' and any(s.material==m for s in o.material_slots)] for o in own if o.type=='MESH' for m in o.data.materials}
samples=[]
for f in [1,2,12]:
    sc.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();data={}
    for o in own:
        rec={'worldMatrix':[list(row) for row in o.matrix_world],'hideRender':o.hide_render}
        if o.type=='MESH':
            ev=o.evaluated_get(dg);me=ev.to_mesh();rec['vertices']=[list(ev.matrix_world@v.co) for v in me.vertices];ev.to_mesh_clear()
        data[o.name]=rec
    digest=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest();samples.append({'nativeFrame':f,'evaluatedStateSHA256':digest})
result={'asset':'decor-background-rock','sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'owners':aud,'allDiscoveredRelevantChannelsEmpty':all(not r['activeAction'] and not r['nlaCount'] and not r['drivers'] for r in aud),'sampledStaticStates':samples,'evaluatedGeometryUnchangedAcrossSamples':len({s['evaluatedStateSHA256'] for s in samples})==1,
        'materialObjectOwners':matowners,'allMaterialObjectOwnersAreOwned':all(set(v)<=set(o.name for o in own) for v in matowners.values()),'meshDataUsers':{o.data.name:o.data.users for o in own if o.type=='MESH'},'linkedLibraries':[x.filepath for x in bpy.data.libraries],
        'note':'Frames2/12 are source-only invariance probes. Required original static clip remains frame1/one frame/fps12/nonlooping; no additional animation is invented.'}
(HERE/'source-temporal-ownership.json').write_text(json.dumps(result,indent=2)+'\n');print('OWNERS',len(aud),'TEMPORAL_EMPTY',result['allDiscoveredRelevantChannelsEmpty'],'STATIC_INVARIANT',result['evaluatedGeometryUnchangedAcrossSamples'])
