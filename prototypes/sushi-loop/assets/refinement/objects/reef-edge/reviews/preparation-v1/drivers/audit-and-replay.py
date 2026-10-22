import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];E=B/'evidence';R=B/'resources'
ANGLES={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,default=str)+'\n')
def matrecord(m):
    nt=m.node_tree
    return {'diffuseColor':list(m.diffuse_color),'animation':bool(m.animation_data),'nodeAnimation':bool(nt.animation_data),'nodes':[{'name':n.name,'type':n.type,'inputs':[{'index':i,'name':s.name,'identifier':s.identifier,'value':list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value} for i,s in enumerate(n.inputs) if hasattr(s,'default_value') and s.type in ['RGBA','VALUE','VECTOR','BOOLEAN','INT']],'ramp':{'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]} if n.type=='VALTORGB' else None} for n in nt.nodes],'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in nt.links]}
def activate(path,aid):
    bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
    root=next(o for o in bpy.data.objects if o.name.startswith(aid+'__root'))
    col=next(c for c in s.collection.children if root in list(c.all_objects))
    for c in s.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
    for l in s.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
    col.hide_render=False;col.hide_viewport=False
    for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
    root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update()
    return s,root,col
def audit(s,root,col):
    dg=bpy.context.evaluated_depsgraph_get();out={'scene':s.name,'root':root.name,'rootProps':dict(root.items()),'collection':col.name,'objects':[],'materials':{},'ports':{},'ground':{},'libraries':[l.filepath for l in bpy.data.libraries],'assetImageNodes':[],'allActions':list(bpy.data.actions.keys()),'lighting':[]};allpts=[]
    for o in col.all_objects:
        if o.type!='MESH':continue
        ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();mat=root.matrix_world.inverted()@ev.matrix_world;nm=mat.to_3x3().inverted().transposed();pts=[mat@v.co for v in me.vertices];allpts+=pts
        rec={'name':o.name,'parent':o.parent.name if o.parent else None,'bounds':[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)],'vertices':len(pts),'triangles':len(me.loop_triangles),'meshUsers':o.data.users,'objectAnimation':bool(o.animation_data),'dataAnimation':bool(o.data.animation_data),'shapeKeys':bool(o.data.shape_keys),'modifiers':[m.type for m in o.modifiers]}
        if 'continuous_core' in o.name:
            rec['verticesRootLocal']=[list(v) for v in pts];ground=[];edgecounts={}
            for p in me.polygons:
                for a,b in p.edge_keys:edgecounts[(min(a,b),max(a,b))]=edgecounts.get((min(a,b),max(a,b)),0)+1
            for t in me.loop_triangles:
                vs=[pts[i] for i in t.vertices]
                if all(abs(v.z)<1e-6 for v in vs):ground.append({'vertices':[list(v) for v in vs],'area':(vs[1]-vs[0]).cross(vs[2]-vs[0]).length/2})
            out['ground']={'triangles':ground,'totalArea':sum(t['area'] for t in ground),'edgeIncidenceHistogram':{str(v):list(edgecounts.values()).count(v) for v in set(edgecounts.values())}}
            for side,x in [('W',-.5),('E',.5)]:
                ids=[i for i,v in enumerate(pts) if abs(v.x-x)<1e-6];trs=[]
                for t in me.loop_triangles:
                    if not any(i in ids for i in t.vertices):continue
                    vs=[pts[i] for i in t.vertices]
                    trs.append({'vertices':[list(v) for v in vs],'cap':all(abs(v.x-x)<1e-6 for v in vs),'normal':list((nm@t.normal).normalized()),'cornerNormals':[list((nm@me.corner_normals[i].vector).normalized()) for i in t.loops],'material':me.materials[t.material_index].name})
                out['ports'][side]={'planeX':x,'vertices':[list(pts[i]) for i in ids],'adjacentTrianglesIncludingCaps':trs}
        out['objects'].append(rec)
        for m in me.materials:
            if m.name not in out['materials']:out['materials'][m.name]=matrecord(m)
            out['assetImageNodes'] += [{'material':m.name,'image':n.image.name if n.image else None} for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
        ev.to_mesh_clear()
    out['bounds']=[[min(v[k] for v in allpts),max(v[k] for v in allpts)] for k in range(3)]
    out['elevatedGeometryBeyondNominalCell']=[list(v) for v in allpts if (abs(v.x)>.50001 or abs(v.y)>.50001) and v.z>1e-6]
    for o in s.objects:
        if o.type=='LIGHT':out['lighting'].append({'name':o.name,'position':list(o.matrix_world.translation),'rotation':list(o.rotation_euler),'energy':o.data.energy,'type':o.data.type,'shape':o.data.shape,'size':o.data.size,'color':list(o.data.color)})
    cam=s.camera;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND')
    out['savedCapture']={'resolution':[s.render.resolution_x,s.render.resolution_y],'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filterSize':s.render.filter_size,'samples':s.eevee.taa_render_samples,'cameraMatrix':[list(r) for r in cam.matrix_world],'cameraType':cam.data.type,'orthoScale':cam.data.ortho_scale,'cameraShift':[cam.data.shift_x,cam.data.shift_y],'worldColor':list(bg.inputs['Color'].default_value),'worldStrength':bg.inputs['Strength'].default_value,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'compositor':s.compositing_node_group.name if s.compositing_node_group else None,'fps':s.render.fps,'frameRange':[s.frame_start,s.frame_end],'frame':s.frame_current}
    out['rotatedPorts']={}
    for d,a in ANGLES.items():
        root.rotation_euler.z=a;bpy.context.view_layer.update()
        out['rotatedPorts'][d]={side:{'rootPosition':list(root.matrix_world@Vector((x,0,0))),'normal':list(root.matrix_world.to_3x3()@Vector((math.copysign(1,x),0,0))),'orderedProfile':[list(root.matrix_world@Vector(v)) for v in port['vertices']]} for side,x,port in [(side,p['planeX'],p) for side,p in out['ports'].items()]}
    root.rotation_euler.z=0;bpy.context.view_layer.update();return out

s,root,col=activate(R/'source/original.blend','reef-edge');original=audit(s,root,col);write(E/'derivative-native-audit.json',original)
spec=importlib.util.spec_from_file_location('reef_edge_frozen_capture_runtime',R/'native/capture_runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime);runtime.SCENE_NAME=s.name
ledger={'source':'resources/source/original.blend','policy':'historical registered native4x/filter1.5; downstream LANCZOS2x only in separate driver','records':[]}
for d,a in ANGLES.items():
    root.rotation_euler.z=a;s.frame_set(1);bpy.context.view_layer.update()
    rec=runtime.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
    s.render.filter_size=1.5;p=E/'historical-replay'/('native4x-'+d+'.png');p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    ledger['records'].append({'facing':d,'rootMatrix':[list(r) for r in root.matrix_world],'camera':rec,'filterSize':s.render.filter_size,'samples':s.eevee.taa_render_samples,'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});write(E/'historical-replay/capture-ledger.json',ledger)
s,root,col=activate(R/'canonical/round-02.blend','reef-middle');canonical=audit(s,root,col);write(E/'canonical-native-audit.json',canonical)
print('AUDIT_AND_BOUNDED_REPLAY_COMPLETE')
