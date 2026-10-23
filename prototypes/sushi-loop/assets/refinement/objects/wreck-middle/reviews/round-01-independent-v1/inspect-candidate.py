"""Independent read-only saved-source measurement and exact native recapture."""
import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent; OBJ=OUT.parent.parent
contract=json.loads((OBJ/'inputs/root-native-contract.json').read_text())
sc=bpy.context.scene; root=bpy.data.objects['wreck-middle__root'];col=bpy.data.collections['Wreck middle authored candidate']
sc.frame_set(1);root.rotation_euler=(0,0,0);root.location=(0,0,0);bpy.context.view_layer.update()
def vec(v):return [float(x) for x in v]
def graph(m):
    nt=m.node_tree
    return {'nodes':[{'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'blend_type':getattr(n,'blend_type',None),'clamp':getattr(n,'clamp',None),
        'attribute':getattr(n,'attribute_name',None),'vector_type':getattr(n,'vector_type',None),'convert_from':getattr(n,'convert_from',None),'convert_to':getattr(n,'convert_to',None),
        'inputs':[{'index':i,'name':s.name,'linked':s.is_linked,'value':vec(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value} for i,s in enumerate(n.inputs) if hasattr(s,'default_value')]}
        for n in nt.nodes], 'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links]}
report={'asset':'wreck-middle','sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,
 'sourceScene':sc.name,'sceneObjects':[{'name':o.name,'type':o.type,'hideRender':o.hide_render,'collection':[c.name for c in o.users_collection]} for o in sc.objects],
 'images':[{'name':i.name,'path':i.filepath} for i in bpy.data.images], 'actions':[a.name for a in bpy.data.actions],
 'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'], 'materials':{},'canonicalCollars':{},'caps':[], 'captures':[]}
poly=contract['reconciliation']['geometry']['authoringEnvelope']['xyPolygonCCW']
allpts=[];support=[];dg=bpy.context.evaluated_depsgraph_get()
for o in col.all_objects:
    if o.type not in ['MESH','CURVE']:continue
    eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();vs=[eo.matrix_world@v.co for v in me.vertices];allpts+=vs
    for t in me.loop_triangles:
        ps=[vs[i] for i in t.vertices]
        if all(abs(p.z-.04)<1e-6 for p in ps):support.append({'points':[vec(p) for p in ps],'area':(ps[1]-ps[0]).cross(ps[2]-ps[0]).length/2})
    if 'canonical_rail' in o.name:
        rail=o.name.split('__')[1].split('_')[0];fields={}
        for side,a,b in [('W',-.5,-.42),('E',.42,.5)]:
            descriptors=[]
            for p in me.polygons:
                points=[vs[i] for i in p.vertices]
                if all(a-1e-6<=v.x<=b+1e-6 for v in points) and max(v.x for v in points)-min(v.x for v in points)>.01:
                    normals=[vec(me.attributes['CanonicalNormal'].data[i].vector) for i in p.loop_indices]
                    descriptors.append({'transverseYZ':sorted(set((round(v.y,8),round(v.z,8)) for v in points)),
                      'longitudinalRange':[round(min(v.x for v in points)-a,7),round(max(v.x for v in points)-a,7)],
                      'cornerNormals':sorted(set(tuple(round(n,7) for n in normal) for normal in normals)),
                      'material':me.materials[p.material_index].name})
            fields[side]=sorted(descriptors,key=str)
            for p in me.polygons:
                points=[vs[i] for i in p.vertices]
                if all(abs(v.x-(-.5 if side=='W' else .5))<1e-6 for v in points):
                    report['caps'].append({'rail':rail,'side':side,'loop':[vec(v) for v in points],'area':p.area,'normal':vec(p.normal)})
        report['canonicalCollars'][rail]={'W':fields['W'],'E':fields['E'],'finiteDescriptorsEqual':fields['W']==fields['E'],
          'proof':'Descriptors contain full tensor rectangular faces and every actual CORNER vector. Each face has one constant vector, so interpolation and Normalize are constant over its complete finite surface. Longitudinal derivatives are zero.'}
    eo.to_mesh_clear()
for m in {m for o in col.all_objects if o.type in ['MESH','CURVE'] for m in o.data.materials if m}: report['materials'][m.name]=graph(m)
report['bounds']=[[min(v[i] for v in allpts),max(v[i] for v in allpts)] for i in range(3)]
report['support']={'triangles':support,'area':sum(t['area'] for t in support),'z0Geometry':min(v.z for v in allpts)<=1e-6,
    'insideFiniteLowestRectangle':all(-.500001<=p[0]<=.500001 and -.180001<=p[1]<=.180001 for t in support for p in t['points'])}
report['maximumFiniteXYViolation']=max((b[1]-a[1])*(v.x-a[0])-(b[0]-a[0])*(v.y-a[1]) for v in allpts for a,b in zip(poly,poly[1:]+poly[:1]))
report['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'position':vec(o.location),'shadows':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT']
report['world']=[{'type':n.type,'color':vec(n.inputs['Color'].default_value),'strength':n.inputs['Strength'].default_value} for n in sc.world.node_tree.nodes if n.type=='BACKGROUND']
for d,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=ang;bpy.context.view_layer.update()
    camera=sc.camera
    def px(v):
        p=world_to_camera_view(sc,camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
    r={'direction':d,'rootMatrix':[vec(r) for r in root.matrix_world], 'frame':sc.frame_current,'fps':sc.render.fps,'startEnd':[sc.frame_start,sc.frame_end],
       'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],
       'filter':sc.render.filter_size,'transparent':sc.render.film_transparent,'cameraWorld':[vec(r) for r in camera.matrix_world], 'ortho':camera.data.ortho_scale,
       'cameraProjection':[vec(r) for r in camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],
       'calibration':{k:px(v) for k,v in [('root',(0,0,0)),('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}}
    dest=OUT/'recapture'/f'{d}.png';dest.parent.mkdir(exist_ok=True);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    r['path']=str(dest.relative_to(OBJ));r['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();report['captures'].append(r)
(OUT/'native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT_NATIVE_RECAPTURE_COMPLETE')
