import bpy,json,math,hashlib,pathlib
from mathutils import Vector
out=pathlib.Path(__file__).parent
asset='belt-corner-n-e'
cols=[c for c in bpy.data.collections if c.name.startswith('S33_FB_'+asset)]
res={'blend':bpy.data.filepath,'scenes':[], 'collections':[c.name for c in cols]}
for s in bpy.data.scenes:
 if any(o.name.startswith(asset+'__root') for o in s.objects):
  cam=s.camera
  res['scenes'].append({'name':s.name,'camera':None if not cam else {'name':cam.name,'matrix':[[float(x) for x in row] for row in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'render':{'size':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'fps':s.render.fps}})
res['objects']=[]
for c in cols:
 for o in c.all_objects:
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'props':{k:str(v) for k,v in o.items()}}
  if o.type=='MESH':
   coords=[o.matrix_world@v.co for v in o.data.vertices]
   d.update(vertices=len(coords),faces=len(o.data.polygons),bounds=[[min(v[i] for v in coords) for i in range(3)],[max(v[i] for v in coords) for i in range(3)]],materials=[m.name for m in o.data.materials if m],modifiers=[{'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers])
   if 'deck' in o.name:
    uv=o.data.uv_layers.active
    if uv:
     unique={}
     for lp in o.data.loops:
      co=o.data.vertices[lp.vertex_index].co
      unique[lp.vertex_index]={'local':list(co),'world':list(o.matrix_world@co),'uv':list(uv.data[lp.index].uv)}
     d['uvVertices']=[unique[k] for k in sorted(unique)]
  res['objects'].append(d)
res['phaseChannels']=[]
for m in bpy.data.materials:
 if asset not in m.name or not m.use_nodes: continue
 nt=m.node_tree
 vals=[n for n in nt.nodes if n.type=='VALUE']
 phases=[]
 for f in [1,2,7,13,19,24,25]:
  for s in bpy.data.scenes:s.frame_set(f)
  phases.append({'frame':f,'values':{n.name:n.outputs[0].default_value for n in vals}})
 res['phaseChannels'].append({'material':m.name,'action':nt.animation_data.action.name if nt.animation_data and nt.animation_data.action else None,'samples':phases,'nodeTypes':sorted(set(n.type for n in nt.nodes))})
res['externalResources']={'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images if i.source!='GENERATED'],'libraries':[l.filepath for l in bpy.data.libraries]}
(out/'native-source-inspection.json').write_text(json.dumps(res,indent=2))
print('JUDGE_NATIVE_INSPECTION',json.dumps({'collections':res['collections'],'scenes':res['scenes'],'objects':[(o['name'],o['type'],o.get('bounds')) for o in res['objects']],'phase':res['phaseChannels'],'resources':res['externalResources']}))
