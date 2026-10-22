import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
kind=sys.argv[sys.argv.index('--')+1]
root=bpy.data.objects['wreck-edge__root']
sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc
for c in bpy.data.collections:
    if root.name in c.all_objects:c.hide_viewport=False;c.hide_render=False
def unexclude(l):
    l.exclude=False;l.hide_viewport=False
    for c in l.children:unexclude(c)
unexclude(sc.view_layers[0].layer_collection)
root.rotation_euler=(0,0,0);root.location=(0,0,0);sc.frame_set(1);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted()
def safe(x):
    if isinstance(x,(str,int,float,bool)) or x is None:return x
    try:return [safe(v) for v in x]
    except:return str(x)
def ntree(nt):
    return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'index':i,'name':s.name,'value':safe(s.default_value) if hasattr(s,'default_value') else None,'linked':s.is_linked} for i,s in enumerate(n.inputs)],'operation':getattr(n,'operation',None),'clamp':getattr(n,'clamp',None),'blend_type':getattr(n,'blend_type',None),'attribute_name':getattr(n,'attribute_name',None),'vector_type':getattr(n,'vector_type',None),'convert_from':getattr(n,'convert_from',None),'convert_to':getattr(n,'convert_to',None)} for n in nt.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in nt.links]}
allv=[];support=[];meshes=[];caps={s:[] for s in ['W','E']};fields=[];mats=set()
for ob in root.children_recursive:
    if ob.type not in ['MESH','CURVE','SURFACE','FONT','META']:continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh();mat=inv@ev.matrix_world;vs=[mat@v.co for v in me.vertices];allv.extend(vs);me.calc_loop_triangles()
    for t in me.loop_triangles:
        points=[vs[i] for i in t.vertices]
        if all(abs(p.z-.04)<1e-6 for p in points):support.append({'object':ob.name,'vertices':[list(p) for p in points],'area':float((points[1]-points[0]).cross(points[2]-points[0]).length/2)})
    for side,x in [('W',-.5),('E',.5)]:
        for p in me.polygons:
            points=[vs[i] for i in p.vertices]
            if all(abs(v.x-x)<1e-6 for v in points):caps[side].append({'object':ob.name,'vertices':[list(v) for v in points],'outwardNormal':list((mat.to_3x3().inverted().transposed()@p.normal).normalized()),'area':p.area,'material':me.materials[p.material_index].name if me.materials else None})
    bounds=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
    meshes.append({'name':ob.name,'type':ob.type,'bounds':bounds,'materials':[m.name for m in me.materials if m],'modifiers':[{'name':m.name,'type':m.type} for m in ob.modifiers]})
    mats.update(m for m in me.materials if m)
    if 'canonical_rail' in ob.name:
        a=me.attributes.get('CanonicalNormal');assert a and a.domain=='CORNER' and a.data_type=='FLOAT_VECTOR'
        for side,xrange in [('W',[-.5,-.42]),('E',[.42,.5])]:
            for p in me.polygons:
                pts=[vs[i] for i in p.vertices]
                if all(xrange[0]-1e-6<=v.x<=xrange[1]+1e-6 for v in pts) and max(v.x for v in pts)-min(v.x for v in pts)>.079:
                    vals=[list(a.data[i].vector.normalized()) for i in p.loop_indices]
                    fields.append({'object':ob.name,'side':side,'vertices':[list(v) for v in pts],'normalizedShaderInputCornerNormals':vals,'constantAfterInterpolation':all(Vector(n).almost_equal if False else (Vector(n)-Vector(vals[0])).length<1e-7 for n in vals),'material':me.materials[p.material_index].name})
    ev.to_mesh_clear()
def hull(points):
    p=sorted(set(tuple(v[:2]) for v in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for v in p:
        while len(lo)>=2 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
        lo.append(v)
    hi=[]
    for v in reversed(p):
        while len(hi)>=2 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
        hi.append(v)
    return lo[:-1]+hi[:-1]
result={'asset':'wreck-edge-round01','sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'rootProperties':{k:safe(root[k]) for k in root.keys()},'ownedObjects':[o.name for o in root.children_recursive],'evaluatedMeshes':meshes,'bounds':[[min(v[i] for v in allv),max(v[i] for v in allv)] for i in range(3)],'finiteXYConvexHullCCW':hull([list(v) for v in allv]),'support':{'z':min(v.z for v in allv),'facesAtZ04':support,'totalArea':sum(t['area'] for t in support),'geometricZ0Intersection':any(v.z<=0 for v in allv)},'caps':caps,'evaluatedVertices':[list(v) for v in allv],'canonicalCollarFields':fields,'materials':[{'name':m.name,'users':m.users,'tree':ntree(m.node_tree)} for m in sorted(mats,key=lambda m:m.name)],'lights':[{'name':o.name,'energy':o.data.energy,'shape':o.data.shape,'size':o.data.size,'color':list(o.data.color),'location':list(o.location),'matrix':[list(r) for r in o.matrix_world],'shadow':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT'],'world':ntree(sc.world.node_tree),'camera':{'matrix':[list(r) for r in sc.camera.matrix_world],'ortho':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]},'render':{'frame':sc.frame_current,'fps':sc.render.fps,'range':[sc.frame_start,sc.frame_end],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'ownedActions':any(o.animation_data for o in [root]+list(root.children_recursive)),'armatures':[o.name for o in root.children_recursive if o.type=='ARMATURE'],'externalLibraries':[l.filepath for l in bpy.data.libraries],'ownedImageNodes':[n.image.filepath for m in mats for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]}
(BASE.parent/(kind+'-native-audit.json')).write_text(json.dumps(result,indent=2)+'\n')
print('AUDIT_COMPLETE',kind,result['bounds'],result['support']['totalArea'])

from bpy_extras.object_utils import world_to_camera_view
captures=[]
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle;bpy.context.view_layer.update();cam=sc.camera
    def px(v):
        q=world_to_camera_view(sc,cam,Vector(v));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
    origin=px((0,0,0));p=BASE.parent/'recapture'/d/'000.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    captures.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'cameraMatrix':[list(r) for r in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'sourceSHA256':result['sourceSHA256'],'path':str(p.relative_to(BASE.parent)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(BASE.parent/'own-capture-records.json').write_text(json.dumps(captures,indent=2)+'\n')
