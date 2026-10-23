"""Read-only saved-source supplemental ownership and raw/evaluated support inspection."""
import bpy,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-01';P=H/'round-01.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def matrix(m):return [list(r) for r in m]
def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return [plain(x) for x in v]
    except:return str(v)
assert Path(bpy.data.filepath).resolve()==P.resolve()
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=bpy.data.collections['S33_PROP_portal_rim.003'];root=bpy.data.objects['portal_rim__root.003']
def enable(l):
    l.exclude=False;l.hide_viewport=False
    for c in l.children:enable(c)
enable(sc.view_layers[0].layer_collection);col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update()
supports=json.loads((H/'round-01-recipe.json').read_text())['supports'];records=[]
def section(vs,edges):
    pts=[]
    for ed in edges:
        a,b=[vs[v] for v in ed.vertices]
        if (a.z<0<=b.z) or (b.z<0<=a.z):pts.append(list(a+(b-a)*(-a.z/(b.z-a.z))))
    return {'planeZ':0,'edgeIntersections':pts,'finiteSection':len(pts)>=3}
for d,deg in [('N',180),('E',90),('S',0),('W',-90)]:
    for i in range(12):
        root.rotation_euler.z=math.radians(deg);sc.frame_set(i+1);sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
        rr=[]
        for name in supports:
            o=bpy.data.objects[name];ev=o.evaluated_get(dg);me=ev.to_mesh()
            raw=[o.matrix_world@v.co for v in o.data.vertices];evaluated=[ev.matrix_world@v.co for v in me.vertices]
            rr.append({'object':name,'rootRelativeMatrix':matrix(root.matrix_world.inverted()@o.matrix_world),'matrixWorld':matrix(o.matrix_world),'rawAuthoredSection':section(raw,o.data.edges),'evaluatedSection':section(evaluated,me.edges),'nativeActionAssigned':bool(o.animation_data and o.animation_data.action)})
            ev.to_mesh_clear()
        records.append({'direction':d,'index':i,'nativeFrame':i+1,'rootRotationDegrees':deg,'rootMatrix':matrix(root.matrix_world),'supports':rr})
materials=[]
for m in sorted({s.material for o in col.all_objects for s in o.material_slots if s.material},key=lambda m:m.name):
    materials.append({'name':m.name,'users':m.users,'library':m.library.filepath if m.library else None,'diffuseColor':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':[{'name':s.name,'identifier':s.identifier,'defaultValue':plain(s.default_value),'linked':s.is_linked} for s in n.inputs if hasattr(s,'default_value')]} for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links]})
own=[]
for o in sorted(col.all_objects,key=lambda x:x.name):
    r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection],'library':o.library.filepath if o.library else None,'dataLibrary':o.data.library.filepath if o.data and o.data.library else None,'dataUsers':o.data.users if o.data else None,'assignedAction':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers]}
    if o.type=='MESH':r['rawTopology']={'vertices':len(o.data.vertices),'edges':len(o.data.edges),'faces':len(o.data.polygons),'zeroAreaFaces':sum(p.area<1e-12 for p in o.data.polygons),'materialNames':[s.material.name if s.material else None for s in o.material_slots],'shapeKeys':o.data.shape_keys.name if o.data.shape_keys else None}
    own.append(r)
report={'asset':'portal-entry','round':'round-01','sourceProject':'source/round-01.blend','sourceSHA256':sha(P),'scene':sc.name,'collection':col.name,'rootObject':root.name,'ownership':own,'materials':materials,'supportSectionsAll48':records,'allAuthoredAndEvaluatedSupportSectionsFinite':all(s['rawAuthoredSection']['finiteSection'] and s['evaluatedSection']['finiteSection'] for r in records for s in r['supports']),'externalImagesUsed':[],'linkedLibrariesUsed':[],'nativeActionsAssigned':sum(bool(o['assignedAction']) for o in own),'method':'Separate saved-source read-only inspection, no render or save. All48phase raw authored mesh and evaluated modifier mesh sections at Z0, real parent/action/native ownership and materials.'}
assert report['allAuthoredAndEvaluatedSupportSectionsFinite']
out=C/'source-ownership-support-audit.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print('PORTAL_SOURCE_AUDIT',len(own),'objects',report['nativeActionsAssigned'],'assigned actions','source',sha(P),flush=True)
