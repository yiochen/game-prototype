import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
OUT=BASE/'candidates/round-01'
RES=HERE/'round01-resources'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
vec=lambda v:[float(x) for x in v]
mat=lambda m:[vec(row) for row in m]
def val(v):
    if isinstance(v,str):return v
    try:return [float(x) for x in v]
    except TypeError:return v
def graph(nt):
    if not nt:return None
    return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'attribute':getattr(n,'attribute_name',None),'vectorType':getattr(n,'vector_type',None),'convertFrom':getattr(n,'convert_from',None),'convertTo':getattr(n,'convert_to',None),'inputs':[{'index':i,'identifier':s.identifier,'name':s.name,'value':val(s.default_value)} for i,s in enumerate(n.inputs) if hasattr(s,'default_value') and s.type not in {'SHADER','CUSTOM'}]} for n in nt.nodes], 'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in nt.links]}
def enable():
    def en(lc):
        lc.exclude=False;lc.hide_viewport=False
        for c in lc.children:en(c)
    en(bpy.context.view_layer.layer_collection)
    for c in bpy.data.collections:c.hide_viewport=False
    for o in bpy.context.scene.objects:o.hide_viewport=False;o.hide_set(False)
    bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
sc=bpy.context.scene
col=bpy.data.collections['S33_PROP_wreck-end.001']
root=bpy.data.objects['wreck-end__root.001']
enable();root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1);enable()
def measure(c,r):
    enable();dg=bpy.context.evaluated_depsgraph_get();inv=r.matrix_world.inverted()
    result={'collection':c.name,'root':r.name,'rootMatrix':mat(r.matrix_world),'objects':[],'materials':{},'supportFaces':[],'Wcaps':[],'WcollarSides':[]}
    for o in c.all_objects:
        ent={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':mat(o.matrix_world),'localMatrix':mat(o.matrix_local),'scale':vec(o.scale),'constraints':[cc.type for cc in o.constraints],'animation':bool(o.animation_data),'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers],'visible':o.visible_get()}
        if o.type in {'MESH','CURVE'}:
            raw=[inv@o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
            eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[inv@eo.matrix_world@v.co for v in me.vertices]
            ent['rawVertices']=list(map(vec,raw));ent['evaluatedVertices']=list(map(vec,pts));ent['polygons']=len(me.polygons)
            attr=me.attributes.get('CanonicalNormal')
            for p in me.polygons:
                vs=[pts[i] for i in p.vertices]
                if max(abs(v.z-.04) for v in vs)<1e-6:
                    result['supportFaces'].append({'object':o.name,'vertices':list(map(vec,vs)),'normal':vec(p.normal)})
                iscap=all(abs(v.x+.5)<1e-6 for v in vs)
                iscollar=min(v.x for v in vs)>=-.500001 and max(v.x for v in vs)<=-.419999
                if iscap or iscollar:
                    fields={'object':o.name,'vertices':list(map(vec,vs)),'geometricNormal':vec(p.normal),'cornerNormals':[vec(me.corner_normals[i].vector) for i in p.loop_indices],'material':me.materials[p.material_index].name}
                    if attr:fields['activeNormalAttribute']=[vec(attr.data[i].vector) for i in p.loop_indices]
                    (result['Wcaps'] if iscap else result['WcollarSides']).append(fields)
            for m in me.materials:
                if m:result['materials'][m.name]=graph(m.node_tree)
            eo.to_mesh_clear()
        result['objects'].append(ent)
    return result
own=measure(col,root)
source_external_dependencies={'linkedLibraries':[l.filepath for l in bpy.data.libraries],'fileImages':[{'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE']}
own['actualRig']={'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'filter':sc.render.filter_size,'world':graph(sc.world.node_tree),'camera':{'name':sc.camera.name,'matrixWorld':mat(sc.camera.matrix_world),'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'lights':[{'name':o.name,'matrixWorld':mat(o.matrix_world),'energy':o.data.energy,'color':vec(o.data.color),'shape':o.data.shape,'size':o.data.size,'useShadow':o.data.use_shadow,'nodeGraph':graph(o.data.node_tree) if o.data.use_nodes else None} for o in sc.objects if o.type=='LIGHT']}
rotations={}
for d,deg in [('N',180),('E',90),('S',0),('W',-90)]:
    root.rotation_euler=(0,0,math.radians(deg));enable();dg=bpy.context.evaluated_depsgraph_get()
    pts=[]
    for o in col.all_objects:
        if o.type not in {'MESH','CURVE'}:continue
        eo=o.evaluated_get(dg);me=eo.to_mesh();pts += [eo.matrix_world@v.co for v in me.vertices];eo.to_mesh_clear()
    rotations[d]={'direction':d,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':mat(root.matrix_world),'determinant':root.matrix_world.to_3x3().determinant(),'worldEvaluatedVertices':list(map(vec,pts))}
root.rotation_euler=(0,0,0);enable()
with bpy.data.libraries.load(str(RES/'canonical/wreck-middle/native.blend'),link=False) as (a,b):
    b.collections=[n for n in a.collections if 'wreck' in n.lower()]
midcol=b.collections[0];sc.collection.children.link(midcol)
midroot=next(o for o in midcol.all_objects if o.type=='EMPTY' and o.parent is None)
midroot.rotation_euler=(0,0,0);midroot.location=(0,0,0);enable()
canonical=measure(midcol,midroot)
def facekey(f):
    return tuple(sorted(tuple(round(c,7) for c in v) for v in f['vertices']))
def normal(f):
    ns=f['activeNormalAttribute']
    assert all((Vector(n)-Vector(ns[0])).length<1e-7 for n in ns)
    return Vector(ns[0]).normalized()
proof=[]
for f in own['WcollarSides']+own['Wcaps']:
    reference=canonical['Wcaps'] if f in own['Wcaps'] else canonical['WcollarSides']
    matches=[g for g in reference if facekey(g)==facekey(f)]
    assert len(matches)==1,(f['object'],facekey(f),len(matches))
    g=matches[0];m=own['materials'][f['material']];cm=canonical['materials'][g['material']]
    # Material names/storage need not coincide. Actual graph function must.
    assert m==cm,(f['material'],g['material'])
    n=normal(f);cn=normal(g);assert (n-cn).length<1e-7
    proof.append({'kind':'outwardWcap' if f in own['Wcaps'] else 'finiteWside','candidate':f,'canonical':g,'graphExactlyEqual':True,'normalizedNormal':vec(n),'fullFieldResult':'same geometric domain, constant CORNER field, identical actual active OBJECT->WORLD NORMAL->NORMALIZE->Principled path and entire albedo/material/alpha graph; every barycentric point matches, independent of triangulation','longitudinalDerivative':0,'tangentRequired':False})
assert len(own['Wcaps'])==3 and len(own['WcollarSides'])==24
with bpy.data.libraries.load(str(RES/'canonical/wreck-middle/native.blend'),link=False) as (a,b):
    b.objects=[n for n in a.objects if n in {'overhead','cardinal0','cardinal1','cardinal2','cardinal3'}]
canonical_light_graphs={o.name.split('.')[0]:graph(o.data.node_tree) for o in b.objects}
result={'asset':'wreck-end','sourceSHA256':sha(HERE/'round-01.blend'),'blender':bpy.app.version_string,'own':own,'all4MeasuredPoses':rotations,'fullFiniteWFieldProof':proof,'canonicalLightGraphs':canonical_light_graphs,'canonicalSourceSHA256':sha(RES/'canonical/wreck-middle/native.blend'),'canonicalFieldsMeasurement':canonical,'externalDependencies':source_external_dependencies,'scope':'Measured native source/fields only; no art verdict; no blend save'}
(OUT/'native-measurements.json').write_text(json.dumps(result,indent=2)+'\n')
print('MEASURED_NATIVE_AND_FULL_W_FIELDS',len(proof))
