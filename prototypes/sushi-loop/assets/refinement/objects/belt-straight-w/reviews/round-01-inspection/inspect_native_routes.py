import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;EXP=OUT.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(EXP/'source/round-01.blend'));s=bpy.context.scene
refs={}
for ident,asset,path in [('W','belt-straight-w',None),('N','belt-straight-n',EXP.parent/'belt-straight-n/source/round-09.blend'),('E','belt-straight-e',EXP.parent/'belt-straight-e/source/round-01.blend'),('S','belt-straight-s',EXP.parent/'belt-straight-s/source/round-01.blend')]:
    cname='S33_FB_'+asset+'.001'
    if path:
        with bpy.data.libraries.load(str(path),link=False) as (a,b):b.collections=[cname]
        col=b.collections[0];s.collection.children.link(col)
    else:col=bpy.data.collections[cname]
    col.hide_viewport=False;col.hide_render=False
    objects=list(col.all_objects);root=next(o for o in objects if o.name.startswith(asset+'__root.'));deck=next(o for o in objects if 'connected_straight_deck' in o.name)
    for o in objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False
    groups=[]
    for pos in (-1,0,1):
        if pos==0:groups.append((root,objects,deck));continue
        copies={}
        for o in objects:q=o.copy();col.objects.link(q);copies[o]=q
        for o,q in copies.items():q.parent=copies.get(o.parent,o.parent)
        groups.append((copies[root],list(copies.values()),copies[deck]))
    refs[ident]=groups
rot={'S':0,'E':90,'N':180,'W':-90}
mapping={'W':{d:d for d in rot},'N':{'S':'E','E':'N','N':'W','W':'S'},'E':{'S':'N','E':'W','N':'S','W':'E'},'S':{'S':'W','E':'S','N':'E','W':'N'}}
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
records=[]
for pat,direction,frame in [('WWW','N',0),('WWW','E',23),('WWW','W',24),('WNW','E',0),('WNW','S',12),('NWN','N',23),('NWN','W',0),('SWS','E',12),('EWE','N',24)]:
    modules=[]
    for ident,groups in refs.items():
        for i,(root,objects,deck) in enumerate(groups):
            root.rotation_euler.z=math.radians(rot[mapping[ident][direction]])
            j=i-1;root.location=(j,0,0) if direction in ('N','S') else (0,-j,0)
            for o in objects:o.hide_render=pat[i]!=ident
    s.frame_set(frame+1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
    for i,ident in enumerate(pat):
        root,objects,deck=refs[ident][i];uv=deck.data.uv_layers.active;ends={}
        for label,x in [('incoming',0),('outgoing',1)]:
            pts=[deck.matrix_world@deck.data.vertices[lo.vertex_index].co for ix,lo in enumerate(deck.data.loops) if abs(uv.data[ix].uv.x-x)<1e-6];ends[label]=sum(pts,Vector())/len(pts)
        modules.append({'identity':ident,'publisherFacing':mapping[ident][direction],'root':[list(x) for x in root.matrix_world],'phase':deck.data.materials[0].node_tree.nodes['Value'].outputs[0].default_value,'ports':{k:list(v) for k,v in ends.items()}})
    dist=[]
    for a,b in zip(modules,modules[1:]):
        dist.append(min((Vector(a['ports']['outgoing'])-Vector(b['ports']['incoming'])).length,(Vector(b['ports']['outgoing'])-Vector(a['ports']['incoming'])).length))
    dest=OUT/f'judge-native-{pat}-{direction}-{frame:02d}.png';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    records.append({'pattern':pat,'direction':direction,'frame':frame,'render':str(dest),'modules':modules,'directedPortNearestDistances':dist})
(OUT/'independent-native-routes.json').write_text(json.dumps(records,indent=2)+'\n')
