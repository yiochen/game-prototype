"""Read-only saved-native audit; compare actual collar triangle/shader fields."""
import sys
sys.dont_write_bytecode=True
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent;O=B.parent;C=O/'candidates/round-01';R=B/'resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return [plain(x) for x in v]
    except:return str(v)
def graph(t):
    ns=[]
    for n in t.nodes:
        row={'name':n.name,'type':n.type,'inputs':[{'name':s.name,'identifier':s.identifier,'value':plain(s.default_value)} for s in n.inputs if hasattr(s,'default_value')]}
        for k in ['operation','blend_type']:
            if hasattr(n,k):row[k]=getattr(n,k)
        if hasattr(n,'color_ramp'):row['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[[e.position,list(e.color)] for e in n.color_ramp.elements]}
        ns.append(row)
    return {'nodes':ns,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in t.links]}
def inspect(file,asset):
    bpy.ops.wm.open_mainfile(filepath=str(file));sc=bpy.context.scene;root=bpy.data.objects[asset+'__root'];root.location=(0,0,0);root.rotation_euler.z=0;sc.frame_set(1);bpy.context.view_layer.update()
    col=bpy.data.collections[asset];core=bpy.data.objects[asset+'__continuous_core'];dg=bpy.context.evaluated_depsgraph_get();ev=core.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();tr=root.matrix_world.inverted()@ev.matrix_world;nt=tr.to_3x3().inverted().transposed();points=[tr@v.co for v in me.vertices]
    triangles=[]
    for t in me.loop_triangles:
        ps=[list(points[i]) for i in t.vertices]
        if all(-.500001<=p[0]<=-.419999 for p in ps):triangles.append({'vertices':ps,'cornerNormals':[list((nt@me.corner_normals[i].vector).normalized()) for i in t.loops],'material':me.materials[me.polygons[t.polygon_index].material_index].name})
    incidence={}
    for p in me.polygons:
        for a,b in zip(list(p.vertices),list(p.vertices[1:])+[p.vertices[0]]):key=tuple(sorted((a,b)));incidence[key]=incidence.get(key,0)+1
    result={'sourceSHA256':sha(file),'collar':triangles,'coreEdgeIncidence':{str(k):list(incidence.values()).count(k) for k in sorted(set(incidence.values()))},'materials':{m.name:graph(m.node_tree) for m in me.materials},'world':graph(sc.world.node_tree),'lights':[{'name':ob.name,'matrix':[list(r) for r in ob.matrix_world],'energy':ob.data.energy,'size':ob.data.size,'color':list(ob.data.color)} for ob in sc.objects if ob.type=='LIGHT' and not ob.hide_render]}
    ev.to_mesh_clear();return result
before=sha(B/'round-01.blend');original=inspect(R/'canonical-middle02.blend','reef-middle');candidate=inspect(B/'round-01.blend','reef-end')
def key(t):return tuple(sorted(tuple(round(x,7) for x in p) for p in t['vertices']))
canonical={key(t):t for t in original['collar']};actual={key(t):t for t in candidate['collar']};samples=[];maximum=0
for k,t in canonical.items():
    if k not in actual:continue
    a=actual[k];by_vertex={tuple(round(x,7) for x in p):n for p,n in zip(a['vertices'],a['cornerNormals'])}
    ns=[Vector(by_vertex[tuple(round(x,7) for x in p)]) for p in t['vertices']]
    for bary in [(1,0,0),(0,1,0),(0,0,1),(.5,.5,0),(0,.5,.5),(.5,0,.5),(1/3,1/3,1/3)]:
        n=sum((Vector(v)*w for v,w in zip(t['cornerNormals'],bary)),Vector()).normalized();q=sum((v*w for v,w in zip(ns,bary)),Vector()).normalized();error=(n-q).length;maximum=max(maximum,error)
        samples.append({'triangle':list(canonical).index(k),'barycentric':bary,'normalizedPostInterpolationCanonical':list(n),'normalizedPostInterpolationCandidate':list(q),'maximumComponentDifference':max(abs(n[i]-q[i]) for i in range(3))})
audit=json.loads((C/'geometry-audit.json').read_text());captures=json.loads((C/'capture-measurements.json').read_text());bounds=audit['bounds'];checks={
    'sourceUnchangedByAudit':before==sha(B/'round-01.blend'),
    'exactCollarTrianglePositions':set(canonical)==set(actual),
    'sameTriangleMaterialAssignment':all(k in actual and t['material']==actual[k]['material'] for k,t in canonical.items()),
    'sameActualMaterialGraphs':original['materials']==candidate['materials'],
    'sameNormalizedPostInterpolationNormalField':maximum<1e-7 and len(canonical)==len(actual),
    'sameActualCanonicalWorldGraph':original['world']==candidate['world'],
    'sameActualCanonicalLights':original['lights']==candidate['lights'],
    'coreClosedEveryEdgeTwice':set(candidate['coreEdgeIncidence'])=={'2'},
    'finiteGroundArea':abs(audit['groundArea']-.6384)<1e-5,
    'finiteEnvelope':all(bounds[0][i]>=[-.5,-.38,0][i]-1e-5 and bounds[1][i]<=[.34,.38,.68][i]+1e-5 for i in range(3)),
    'privateMeshes':all(p['privateMeshUsers']==1 for p in audit['parts']),
    'staticNativeNoActionsOrExternalImages':not audit['actions'] and not audit['images'] and not audit['linkedLibraries'] and all(not p['animation'] for p in audit['parts']),
    'all4ActualRootRotations':all(abs(math.atan2(math.sin(r['rootRotationZ']-{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[r['direction']]),math.cos(r['rootRotationZ']-{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[r['direction']])))<1e-5 for r in captures['captureRecords']),
    'all8MandatoryNativeContexts':len(captures['contexts'])==8 and {r['kind'] for r in captures['contexts']}=={'direct-canonical-to-end','full-family-L'},
}
result={'asset':'reef-end','round':'round-01','sourceSHA256':before,'canonicalSHA256':original['sourceSHA256'],'checks':checks,'allChecksPassed':all(checks.values()),'collarTriangleCount':len(canonical),'actualCollarTriangleCount':len(actual),'actualCoreEdgeIncidence':candidate['coreEdgeIncidence'],'maxNormalizedPostInterpolationNormalError':maximum,'barycentricSamples':samples,'fieldProof':'Every full .08 collar triangle is position-identical and has identical actual flat corner normals and material graph. Normalized interpolated normals are sampled at corners, edge midpoints and centroid; identical flat triangle fields also establish every interior barycentric location. The same actual material graph and world/light rig are preserved. No ring-ID-only or point-normal-only equivalence claim.','canonical':original,'candidate':candidate,'limits':'Technical native contract only; native combined/independent consumer, local visible continuity, broad finite-light/source-extent residuals and aesthetic approval remain separate evidence.'}
(C/'native-contract-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':checks,'collarTriangleCount':len(canonical),'normalError':maximum,'sourceSHA256':before}))
if not all(checks.values()):raise RuntimeError('Native contract audit failed')
