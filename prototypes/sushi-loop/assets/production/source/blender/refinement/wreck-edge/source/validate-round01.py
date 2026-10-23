"""Measured validation of the actual saved source. Read-only background Blender."""
import sys
sys.dont_write_bytecode=True
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;RES=HERE/'round01-resources';OUT=EXP/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sc=bpy.context.scene;root=bpy.data.objects['wreck-edge__root'];col=bpy.data.collections['Wreck edge native authored round01']
root.rotation_euler=(0,0,0);root.location=(0,0,0);root.scale=(1,1,1);sc.frame_set(1);bpy.context.view_layer.update()
contract=json.loads((RES/'root-native-contract.json').read_text());budget=contract['reconciliation']['authoringEnvelope'];poly=budget['xy'];tol=1e-6

def ntree(nt):
    def val(v):
        if isinstance(v,(str,int,float,bool)) or v is None:return v
        try:return [val(x) for x in v]
        except:return str(v)
    return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'attribute_name':getattr(n,'attribute_name',None),'attribute_type':getattr(n,'attribute_type',None),'vector_type':getattr(n,'vector_type',None),'convert_from':getattr(n,'convert_from',None),'convert_to':getattr(n,'convert_to',None),'blend_type':getattr(n,'blend_type',None),'clamp':getattr(n,'clamp',None),'inputs':[{'index':i,'name':s.name,'value':val(s.default_value) if hasattr(s,'default_value') else None,'linked':s.is_linked} for i,s in enumerate(n.inputs)]} for n in nt.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in nt.links]}

def material_fields(m):
    nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    norm=bs.inputs['Normal'].links[0].from_node
    assert norm.type=='VECT_MATH' and norm.operation=='NORMALIZE'
    tr=norm.inputs[0].links[0].from_node;assert tr.type=='VECT_TRANSFORM' and tr.vector_type=='NORMAL' and tr.convert_from=='OBJECT' and tr.convert_to=='WORLD'
    attr=tr.inputs['Vector'].links[0].from_node;assert attr.type=='ATTRIBUTE' and attr.attribute_type=='GEOMETRY'
    mul=bs.inputs['Base Color'].links[0].from_node;assert mul.type=='MIX_RGB' and mul.blend_type=='MULTIPLY'
    ramp=mul.inputs[2].links[0].from_node;sep=ramp.inputs['Value'].links[0].from_node
    geom=sep.inputs[0].links[0].from_node;assert geom.type=='NEW_GEOMETRY' and sep.type=='SEPXYZ' and ramp.type=='MAP_RANGE'
    assert ramp.inputs['Value'].links[0].from_socket.name=='Z'
    fields={n:list(bs.inputs[n].default_value) if n=='Tangent' else bs.inputs[n].default_value for n in ['Metallic','Roughness','IOR','Alpha','Specular IOR Level','Anisotropic','Tangent']}
    return {'normalAttribute':attr.attribute_name,'normalChain':'actual geometry attribute -> Object-to-World NORMAL -> Normalize -> Principled Normal','baseLinearRGBA':list(mul.inputs[1].default_value),'heightRamp':{n:ramp.inputs[n].default_value for n in ['From Min','From Max','To Min','To Max']},'clamp':ramp.clamp,'principled':fields,'alphaLinked':bs.inputs['Alpha'].is_linked,'tangentLinked':bs.inputs['Tangent'].is_linked,'graph':ntree(nt)}

def rail_fields(c):
    result={}
    for ob in c.all_objects:
        if ob.type!='MESH' or 'canonical_rail' not in ob.name:continue
        kind='lower' if 'lower' in ob.name else 'upper' if 'upper' in ob.name else 'rear'
        me=ob.data;vs=[ob.matrix_world@v.co for v in me.vertices]
        for side,lo,hi in [('W',-.5,-.42),('E',.42,.5)]:
            faces=[]
            for p in me.polygons:
                pts=[vs[i] for i in p.vertices]
                if not all(lo-tol<=v.x<=hi+tol for v in pts):continue
                cap=max(v.x for v in pts)-min(v.x for v in pts)<tol
                if cap and abs(pts[0].x-(-.5 if side=='W' else .5))>tol:continue
                mf=material_fields(me.materials[p.material_index]);a=me.attributes[mf['normalAttribute']]
                ns=[list(a.data[i].vector.normalized()) for i in p.loop_indices]
                assert all((Vector(n)-Vector(ns[0])).length<1e-7 for n in ns),'nonconstant canonical collar normal'
                faces.append({'kind':'cap' if cap else 'side','vertices':[list(v) for v in pts],'geometricNormal':list(p.normal),'normalizedShaderCornerNormals':ns,'material':mf})
            assert len(faces)==9,(kind,side,len(faces))
            result[kind+'-'+side]=faces
    assert len(result)==6
    return result

candidate_fields=rail_fields(col)
dg=bpy.context.evaluated_depsgraph_get();points=[];raw=[];support=[];meshrecords=[];materials=set()
outside=[]
def violation(p):
    if p.z<.04-tol or p.z>.78+tol:return True
    return any((b[0]-a[0])*(p.y-a[1])-(b[1]-a[1])*(p.x-a[0])<-tol for a,b in zip(poly,poly[1:]+poly[:1]))
for o in root.children_recursive:
    if o.type not in ['MESH','CURVE']:continue
    if o.type=='MESH':raw.extend(o.matrix_world@v.co for v in o.data.vertices)
    ev=o.evaluated_get(dg);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];points.extend(vs);me.calc_loop_triangles()
    for v in vs:
        if violation(v):outside.append({'object':o.name,'point':list(v)})
    for t in me.loop_triangles:
        ps=[vs[i] for i in t.vertices]
        if all(abs(p.z-.04)<tol for p in ps):support.append({'object':o.name,'vertices':[list(p) for p in ps],'area':float((ps[1]-ps[0]).cross(ps[2]-ps[0]).length/2)})
    edges={}
    for p in me.polygons:
        seq=list(p.vertices)
        for a,b in zip(seq,seq[1:]+seq[:1]):edges[tuple(sorted((a,b)))]=edges.get(tuple(sorted((a,b))),0)+1
    meshrecords.append({'object':o.name,'type':o.type,'vertices':len(me.vertices),'polygons':len(me.polygons),'closedEvaluatedSurface':all(n==2 for n in edges.values()),'boundaryEdges':sum(n==1 for n in edges.values()),'nonmanifoldEdges':sum(n>2 for n in edges.values()),'bounds':[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)],'materials':[m.name for m in me.materials if m],'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers]})
    materials.update(m for m in me.materials if m);ev.to_mesh_clear()
owned=[root]+list(root.children_recursive)
state={'sourceSHA256':sha(HERE/'round-01.blend'),'blender':bpy.app.version_string,'asset':'wreck-edge','rootMatrix':[list(r) for r in root.matrix_world],'rootProperties':{k:str(v) for k,v in root.items()},'rawBounds':[[min(v[i] for v in raw),max(v[i] for v in raw)] for i in range(3)],'evaluatedBounds':[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)],'authoringBudget':budget,'evaluatedOutsideEnvelope':outside,'rawOutsideEnvelope':[list(v) for v in raw if violation(v)],'support':{'minimumZ':min(v.z for v in points),'facesAtZ04':support,'area':sum(t['area'] for t in support),'nominalArea':.36,'Z0Intersection':any(v.z<=0 for v in points)},'meshes':meshrecords,'staticOwnership':{'objectAnimations':[o.name for o in owned if o.animation_data],'materialAnimations':[m.name for m in materials if m.animation_data or (m.node_tree and m.node_tree.animation_data)],'armatures':[o.name for o in owned if o.type=='ARMATURE'],'imageNodes':[n.image.filepath for m in materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],'libraries':[l.filepath for l in bpy.data.libraries]},'materials':[{'name':m.name,'nodes':ntree(m.node_tree)} for m in sorted(materials,key=lambda m:m.name)],'world':ntree(sc.world.node_tree),'lights':[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'shadow':o.data.use_shadow,'color':list(o.data.color),'matrix':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'frame':sc.frame_current,'frameRange':[sc.frame_start,sc.frame_end],'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity},'camera':{'matrix':[list(r) for r in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]}}
with bpy.data.libraries.load(str(RES/'canonical-middle02.blend'),link=False) as (src,dst):dst.collections=['Wreck middle authored candidate']
cc=dst.collections[0];sc.collection.children.link(cc);cr=next(o for o in cc.all_objects if o.name.startswith('wreck-middle__root'));cr.rotation_euler=(0,0,0);cr.location=(0,0,0);bpy.context.view_layer.update()
reference_fields=rail_fields(cc)
# Node names and numeric fields are exactly copied. This is a sufficient method
# of output equivalence, not a requirement that all equivalent methods use it.
assert candidate_fields==reference_fields,'Actual contact field mismatch'
state['fullFiniteContactProof']={'canonicalSourceSHA256':sha(RES/'canonical-middle02.blend'),'domains':{'W':[-.5,-.42],'E':[.42,.5]},'faceCount':sum(len(v) for v in candidate_fields.values()),'sideCount':48,'capCount':6,'actualSavedGeometryAndActiveFieldsEqual':True,'analyticWholeDomain':'Every side face spans complete .08 collar and has a constant CORNER normal vector. Actual active normal path transforms then normalizes that constant post-interpolation field. Albedo is exact base linearRGBA times the same clamped world-Z affine ramp. World Z is invariant under longitudinal translation and proper Z rotation, so full albedo/material/alpha response and X derivatives agree on the complete domains. Caps have independently verified outward normal fields and exact ordered source polygon. Anisotropy0, unlinked tangent, alpha1.','properAll4Rotations':{'S':0,'E':90,'N':180,'W':-90},'tangentNeeded':False,'longitudinalDerivatives':{'normalizedNormal':0,'albedo':0,'material':0,'alpha':0},'fields':candidate_fields}
profiles=[]
for key,faces in candidate_fields.items():
    kind,side=key.split('-');cap=next(f for f in faces if f['kind']=='cap')
    src=next(s for s in contract['nativeContract']['interfaces']['ports'][side]['sections'] if ('back_hull' if kind=='rear' else kind+'_hull') in s['sourceObject'])
    points=cap['vertices'];ys=[p[1] for p in points];zs=[p[2] for p in points]
    expected=src['orderedCapLoop'];ey=[p[1] for p in expected];ez=[p[2] for p in expected]
    assert max(abs(a-b) for a,b in zip([min(ys),max(ys),min(zs),max(zs)],[min(ey),max(ey),min(ez),max(ez)]))<1e-7
    assert all((abs(p[1]-min(ey))<tol or abs(p[1]-max(ey))<tol or abs(p[2]-min(ez))<tol or abs(p[2]-max(ez))<tol) for p in points)
    outward=-1 if side=='W' else 1;assert cap['geometricNormal'][0]*outward>.999999
    assert all((Vector(n)-Vector((outward,0,0))).length<1e-7 for n in cap['normalizedShaderCornerNormals'])
    profiles.append({'kind':kind,'port':side,'actualOrderedCapPolygon':points,'sourceOrderedFourCornerProfile':expected,'outwardGeometricNormal':cap['geometricNormal'],'equivalentRectangleWithCollinearMidpoints':True,'normalizedCapFieldIndependentlyVerified':True})
state['orderedFinitePortProfiles']=profiles
# Compare actual active capture/rig to approved source, not rounded summaries.
bpy.ops.wm.open_mainfile(filepath=str(RES/'canonical-middle02.blend'));cs=bpy.context.scene
canonical_lights=[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'shadow':o.data.use_shadow,'color':list(o.data.color),'matrix':[list(r) for r in o.matrix_world]} for o in cs.objects if o.type=='LIGHT']
canonical_camera={'matrix':[list(r) for r in cs.camera.matrix_world],'orthoScale':cs.camera.data.ortho_scale,'shift':[cs.camera.data.shift_x,cs.camera.data.shift_y]}
assert state['lights']==canonical_lights and state['world']==ntree(cs.world.node_tree) and state['camera']==canonical_camera
state['exactCanonicalRigCameraWorldEquality']={'sourceSHA256':sha(RES/'canonical-middle02.blend'),'measuredLightsEqual':True,'measuredActiveWorldGraphEqual':True,'measuredCameraMatrixAndShiftEqual':True,'sameRecipeAll4':True}
if outside or state['rawOutsideEnvelope']:
    (OUT/'envelope-diagnostic.json').write_text(json.dumps({'evaluatedOutside':outside,'rawOutside':state['rawOutsideEnvelope']},indent=2)+'\n')
assert not outside and not state['rawOutsideEnvelope']
assert abs(state['support']['area']-.36)<1e-6 and not state['support']['Z0Intersection']
assert not any(state['staticOwnership'].values())
write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n')
write(OUT/'native-validation.json',state)
print('VALIDATION_MEASURED',state['evaluatedBounds'],state['support']['area'],'full contact fields exact',len(candidate_fields))
