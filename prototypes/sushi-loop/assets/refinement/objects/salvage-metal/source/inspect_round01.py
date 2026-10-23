import bpy,json,sys,hashlib,bmesh
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-01';sc=bpy.context.scene
def plain(v):
    if isinstance(v,(int,float,str,bool)) or v is None:return v
    try:return [plain(x) for x in v]
    except TypeError:return str(v)
d={'source':{'path':'source/round-01.blend','sha256':hashlib.sha256((BASE/'source/round-01.blend').read_bytes()).hexdigest()},'blender':{'version':bpy.app.version_string,'binary':bpy.app.binary_path},'scene':sc.name,'render':{k:plain(getattr(sc.render,k)) for k in ['engine','resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent','fps','filter_size','dither_intensity']},'samples':sc.eevee.taa_render_samples,'viewSettings':{k:plain(getattr(sc.view_settings,k)) for k in ['view_transform','look','exposure','gamma']},'lights':[],'materials':[],'meshes':[],'actions':[],'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries]}
for o in sc.objects:
    if o.type=='LIGHT':d['lights'].append({'name':o.name,'type':o.data.type,'energy':o.data.energy,'shape':o.data.shape,'size':o.data.size,'color':plain(o.data.color),'matrixWorld':plain(o.matrix_world)})
    if o.type=='MESH':
        bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);bm.free();assert bad==0,(o.name,bad)
        d['meshes'].append({'name':o.name,'parent':o.parent.name,'variantIndex':o['variantIndex'],'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'nonManifoldBaseEdges':bad,'modifiers':[{'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers]})
for m in bpy.data.materials:
    if not m.use_nodes:continue
    d['materials'].append({'name':m.name,'nodes':[{'type':n.type,'name':n.name,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in m.node_tree.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]})
for a in bpy.data.actions:
    d['actions'].append({'name':a.name,'frameRange':plain(a.frame_range),'curves':[{'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[[float(p.co.x),float(p.co.y),p.interpolation] for p in f.keyframe_points]} for l in a.layers for s in l.strips for bag in s.channelbags for f in bag.fcurves]})
d['world']=[{'type':n.type,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in sc.world.node_tree.nodes]
(OUT/'native-settings.json').write_text(json.dumps(d,indent=2)+'\n');print('SAVED_SOURCE_INSPECTED',len(d['meshes']),len(d['actions']))
