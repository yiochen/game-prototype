"""Read saved native sources, measure fields, topology and exact source replay."""
import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib,collections
from pathlib import Path
from mathutils import Vector,Matrix
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-01'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(v):return tuple(round(float(x),6) for x in v)
def material(m):
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    ramp=next((n for n in m.node_tree.nodes if n.type=='VALTORGB'),None)
    links=[(l.from_node.bl_idname,l.from_socket.identifier,l.to_node.bl_idname,l.to_socket.identifier) for l in m.node_tree.links]
    return {'roughness':bs.inputs['Roughness'].default_value,'specularIORLevel':bs.inputs['Specular IOR Level'].default_value,'ramp':{'interpolation':ramp.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in ramp.color_ramp.elements]} if ramp else None,'links':links,'base':list(bs.inputs['Base Color'].default_value)}
def albedo(m,z):
    es=m['ramp']['elements'];a,b=es[0],es[-1];t=max(0,min(1,(z-a['position'])/(b['position']-a['position'])));return [a['color'][j]*(1-t)+b['color'][j]*t for j in range(4)]
def triangles(o,rot=None):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();me.calc_loop_triangles();out=[];rot=rot or Matrix.Identity(3)
    for t in me.loop_triangles:out.append({'positions':[list(rot@me.vertices[i].co) for i in t.vertices],'normals':[list(rot@me.corner_normals[i].vector) for i in t.loops],'material':material(me.materials[t.material_index]),'sourceTriangle':t.index})
    e.to_mesh_clear();return out
def rig():
    sc=bpy.context.scene
    return {'lights':[{'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'type':o.data.type,'shape':o.data.shape,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'world':[{'type':n.bl_idname,'inputs':{s.identifier:list(s.default_value) if hasattr(s.default_value,'__iter__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and (isinstance(s.default_value,(int,float)) or hasattr(s.default_value,'__iter__'))}} for n in sc.world.node_tree.nodes],'color':{'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'samples':sc.eevee.taa_render_samples,'filter':sc.render.filter_size}}
bpy.ops.wm.open_mainfile(filepath=str(BASE/'resources/canonical-middle.blend'));crig=rig();ct=[]
for side in ['W','N']:
    for t in triangles(bpy.data.objects['reef-middle__continuous_core'],Matrix.Rotation(0 if side=='W' else math.pi/2,3,'Z')):
        ps=t['positions'];localx=[p[0] for p in ps] if side=='W' else [p[1] for p in ps]
        valid=all(-.500001<=x<=-.419999 for x in localx) if side=='W' else all(.419999<=x<=.500001 for x in localx)
        if valid and max(localx)-min(localx)>1e-7:t['side']=side;ct.append(t)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-01.blend'));arig=rig();o=bpy.data.objects['reef-corner__continuous_core'];ts=triangles(o);lookup={tuple(sorted(key(p) for p in t['positions'])):t for t in ts}
records=[];samples=[]
weights=[(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]
for canonical in ct:
    t=lookup.get(tuple(sorted(key(p) for p in canonical['positions'])))
    if t is None:raise ValueError('Missing full canonical triangle')
    order=[next(i for i,p in enumerate(t['positions']) if key(p)==key(q)) for q in canonical['positions']]
    records.append({'side':canonical['side'],'canonical':canonical,'candidate':t,'positionOrder':order,'materialFieldsEqual':canonical['material']==t['material']})
    for w in weights:
        pc=sum((Vector(p)*v for p,v in zip(canonical['positions'],w)),Vector());pa=sum((Vector(t['positions'][i])*v for i,v in zip(order,w)),Vector())
        nc=sum((Vector(n)*v for n,v in zip(canonical['normals'],w)),Vector()).normalized();na=sum((Vector(t['normals'][i])*v for i,v in zip(order,w)),Vector()).normalized()
        ac=albedo(canonical['material'],pc.z);aa=albedo(t['material'],pa.z)
        samples.append({'side':canonical['side'],'weights':w,'canonicalPosition':list(pc),'candidatePosition':list(pa),'positionError':(pc-pa).length,'canonicalNormalizedPostInterpolationNormal':list(nc),'candidateNormalizedPostInterpolationNormal':list(na),'normalError':(nc-na).length,'canonicalAlbedo':ac,'candidateAlbedo':aa,'albedoError':max(abs(a-b) for a,b in zip(ac,aa))})
me=o.data;me.calc_loop_triangles();edgeusers=collections.Counter(tuple(sorted(e)) for p in me.polygons for e in p.edge_keys)
bottom=[]
for t in me.loop_triangles:
    ps=[me.vertices[i].co for i in t.vertices]
    if all(abs(p.z)<1e-7 for p in ps):bottom.append({'positions':[list(p) for p in ps],'normal':list(t.normal),'area':t.area})
write(OUT/'native-field-proof.json',{'sourceSHA256':sha(BASE/'round-01.blend'),'canonicalSHA256':sha(BASE/'resources/canonical-middle.blend'),'method':'Actual evaluated saved mesh loop triangles and corner normals; full canonical uncut native triangles, actual linked Z-ramp graph evaluated at native barycentric positions. Normals normalized only after interpolation.','triangleRecords':records,'samples':samples,'sampleCount':len(samples),'maxPositionError':max(s['positionError'] for s in samples),'maxNormalizedNormalError':max(s['normalError'] for s in samples),'maxAlbedoError':max(s['albedoError'] for s in samples),'actualMaterialResponseEqual':all(t['materialFieldsEqual'] for t in records),'actualRigEqual':crig==arig,'canonicalRig':crig,'candidateRig':arig})
ground=[(-.38,.38),(-.5,.38),(-.5,-.38),(-.25,-.38),(.26870057,-.26870057),(.38,.25),(.38,.5),(-.38,.5)]
def inside(p):
    x,y=p;value=False
    for a,b in zip(ground,ground[1:]+ground[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:value=not value
    return value
def distance(p):
    ds=[]
    for a,b in zip(ground,ground[1:]+ground[:1]):
        aa=Vector(a);bb=Vector(b);pp=Vector(p);t=max(0,min(1,(pp-aa).dot(bb-aa)/(bb-aa).length_squared));ds.append((pp-(aa+(bb-aa)*t)).length)
    return min(ds)
outside=[];evaluatedVertexCount=0;dg=bpy.context.evaluated_depsgraph_get()
for part in bpy.data.collections['reef-corner'].objects:
    if part.type!='MESH':continue
    e=part.evaluated_get(dg);em=e.to_mesh()
    for v in em.vertices:
        p=part.matrix_world@v.co;evaluatedVertexCount+=1
        if not inside((p.x,p.y)) and distance((p.x,p.y))>1e-5:outside.append({'part':part.name,'position':list(p),'outsideDistance':distance((p.x,p.y))})
    e.to_mesh_clear()
be=collections.Counter()
for t in bottom:
    points=[key(p) for p in t['positions']]
    for a,b in zip(points,points[1:]+points[:1]):be[tuple(sorted([a,b]))]+=1
boundary=[list(e) for e,count in be.items() if count==1]
write(OUT/'native-topology.json',{'sourceSHA256':sha(BASE/'round-01.blend'),'coreVertices':len(me.vertices),'coreEdges':len(edgeusers),'corePolygons':len(me.polygons),'coreEulerCharacteristic':len(me.vertices)-len(edgeusers)+len(me.polygons),'edgeFaceIncidenceHistogram':dict(collections.Counter(edgeusers.values())),'nonTwoFaceEdges':[{'vertices':list(e),'uses':n,'positions':[list(me.vertices[i].co) for i in e]} for e,n in edgeusers.items() if n!=2],'actualZ0Triangles':bottom,'actualBottomBoundarySegments':boundary,'actualBottomAreaSum':sum(t['area'] for t in bottom),'upwardBottomTriangles':sum(t['normal'][2]>0 for t in bottom),'finiteExteriorContainment':{'evaluatedVertices':evaluatedVertexCount,'tolerance':1e-5,'verticesOutsideFiniteExterior':outside,'count':len(outside)},'libraries':[x.filepath for x in bpy.data.libraries],'images':list(bpy.data.images.keys())})
print('NATIVE_FIELD_AND_TOPOLOGY_MEASURED')
