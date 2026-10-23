import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production')
SRC=BASE/'source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def props(o):return {k:str(o[k]) for k in o.keys()}
def bounds(v):return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]] if v else None
def rec_o(o,dg):
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':[list(x) for x in o.matrix_world],'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'properties':props(o),'materials':[s.material.name if s.material else None for s in o.material_slots]}
 if o.type=='MESH':
  e=o.evaluated_get(dg);m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];r.update(bounds=bounds(vs),vertices=[list(v) for v in vs],polygons=[{'vertices':list(f.vertices),'normal':list(f.normal),'materialIndex':f.material_index} for f in m.polygons],modifiers=[{'name':x.name,'type':x.type} for x in o.modifiers]);e.to_mesh_clear()
 return r
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for c in sc.collection.children:c.hide_render=False;c.hide_viewport=False
sc.frame_set(1);sc.view_layers[0].update()
report={'blenderVersion':bpy.app.version_string,'source':str(SRC),'sourceSHA256':sha(SRC),'scenes':[{'name':s.name,'properties':props(s),'camera':s.camera.name if s.camera else None} for s in bpy.data.scenes],'nativeScene':sc.name,'savedCamera':{'name':sc.camera.name,'matrixWorld':[list(x) for x in sc.camera.matrix_world],'type':sc.camera.data.type,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]},'savedRender':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'engine':sc.render.engine,'filmTransparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None},'assets':{},'images':[{'name':x.name,'filepath':x.filepath,'packed':bool(x.packed_file),'size':list(x.size),'source':x.source,'alphaMode':x.alpha_mode} for x in bpy.data.images]}
mat_names=set()
for aid in ['dock-floor','dock-entry','workshop-hut','submarine-yellow','dock-cover','dock-post-rope']:
 rig=json.loads((BASE/f'source/records/{aid}/rig.json').read_text());r=bpy.data.objects.get(rig['groundRootObject']);c=next(c for c in sc.collection.children if r in list(c.all_objects));before={'matrixWorld':[list(x) for x in r.matrix_world],'properties':props(r)}
 r.rotation_euler=(0,0,0);r.location=(0,0,0);sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get()
 objs=[rec_o(o,dg) for o in c.all_objects];[mat_names.update(o['materials']) for o in objs]
 report['assets'][aid]={'root':r.name,'collection':c.name,'collectionProperties':props(c),'savedRoot':before,'rootProperties':props(r),'objects':objs,'bounds':bounds([Vector(v) for o in objs for v in o.get('vertices',[])])}
report['materials']={}
for n in sorted(x for x in mat_names if x):
 m=bpy.data.materials[n];report['materials'][n]={'properties':props(m),'surfaceRenderMethod':m.surface_render_method,'useNodes':m.use_nodes,'nodes':[{'name':x.name,'type':x.type,'label':x.label,'image':x.image.name if hasattr(x,'image') and x.image else None,'inputs':{a.name:list(a.default_value) if hasattr(a.default_value,'__len__') and not isinstance(a.default_value,str) else a.default_value for a in x.inputs if hasattr(a,'default_value')},'links':{a.name:[{'node':p.from_node.name,'socket':p.from_socket.name} for p in a.links] for a in x.inputs if a.is_linked}} for x in m.node_tree.nodes] if m.node_tree else []}
report['lights']=[{'name':o.name,'position':list(o.matrix_world.translation),'energy':o.data.energy,'type':o.data.type,'useShadow':o.data.use_shadow,'size':o.data.size if hasattr(o.data,'size') else None} for o in sc.objects if o.type=='LIGHT']
(OUT/'native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'nativeScene':sc.name,'savedCamera':report['savedCamera'],'assets':{k:{'root':v['root'],'collection':v['collection'],'bounds':v['bounds'],'objectCount':len(v['objects'])} for k,v in report['assets'].items()},'images':report['images'],'lights':report['lights']},indent=2))
