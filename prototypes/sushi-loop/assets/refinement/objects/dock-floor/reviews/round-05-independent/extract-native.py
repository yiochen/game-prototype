"""Independent review extraction; background Blender only; never save source."""
import bpy,json,math,hashlib,gzip
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parent;B=R.parents[1];plan=json.loads((R/'resources/plan.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths={'floor':B/'source/round-04.blend','entry':B/'inputs/paired-native/dock-entry-round-06.blend','human':B/'source/resources/approved-human-v3/customer-rosa-approved.blend','original':B/'source/resources/original-library.blend','approvedHut':B/'inputs/approved-hut-v1/project.blend'}
before={k:sha(v)for k,v in paths.items()};bpy.ops.wm.open_mainfile(filepath=str(paths['floor']));sc=bpy.context.scene
fc=bpy.data.collections['WarmSoft_dock-floor'];fr=bpy.data.objects['dock-floor__root'];fr.rotation_euler=(0,0,0)
def load(p,names,actions=None):
 with bpy.data.libraries.load(str(p),link=False)as(a,b):
  b.collections=names if names else [n for n in a.collections if n!='Collection'];b.actions=actions or []
 for c in b.collections:
  sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
  for ob in c.all_objects:ob.hide_viewport=False;ob.hide_set(False)
 return b.collections

def geo(col):
 dg=bpy.context.evaluated_depsgraph_get();out=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();v=[tuple(e.matrix_world@p.co)for p in m.vertices]
  out.append({'name':o.name,'vertices':v,'triangles':[tuple(t.vertices)for t in m.loop_triangles],'matrix':[list(r)for r in e.matrix_world],'materials':[{'name':mat.name,'diffuse':list(mat.diffuse_color),'nodes':[{'type':n.bl_idname,'name':n.name,'values':{s.name:list(s.default_value)if hasattr(s.default_value,'__len__')and not isinstance(s.default_value,str)else s.default_value for s in n.inputs if hasattr(s,'default_value') and isinstance(s.default_value,(int,float,bool,str))}}for n in mat.node_tree.nodes]if mat.use_nodes else []}for mat in m.materials if mat]});e.to_mesh_clear()
 return out

def assign(col,rig,clip,frame):
 for o in col.all_objects:
  for owner in [o,getattr(o.data,'shape_keys',None)]:
   if owner and owner.animation_data:
    owner.animation_data.action=None
    for t in owner.animation_data.nla_tracks:t.mute=True
 for target in rig['clips'][clip]['actions']:
  typ=target['ownerType'];name=target['ownerName']
  if typ=='Object':owner=bpy.data.objects[name]
  elif typ=='Key':owner=bpy.data.shape_keys[name]
  elif target.get('materialOwnerName'):owner=bpy.data.materials[target['materialOwnerName']].node_tree
  else:raise RuntimeError(('unknown action owner',target))
  owner.animation_data_create();owner.animation_data.action=bpy.data.actions[target['action']]
  if target.get('slotIdentifier'):
   owner.animation_data.action_slot=next(s for s in owner.animation_data.action.slots if s.identifier==target['slotIdentifier'])
 sc.frame_set(frame);bpy.context.view_layer.update()

ec=load(paths['entry'],['S33_PROP_dock-entry'])[0];er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0);er.rotation_euler=(0,0,0)
rigs={a:json.loads((B/'source/resources/family-rigs'/f'{a}.json').read_text())for a in ['submarine-yellow','dock-cover']}
cs=load(paths['original'],['S33_PROP_workshop-hut.001','S33_PROP_submarine_base.001','S33_PROP_dock-cover.001'],sorted({t['action']for a,r in rigs.items()for clip in [('dock-ready'if a=='submarine-yellow'else'uncover')]for t in r['clips'][clip]['actions']}))
comp={}
for aid,c,p in zip(['hut','sub','cover'],cs,[(.78,.35,.23),(-.7,-.42,.23),(0,0,.23)]):
 root=next(o for o in c.all_objects if o.type=='EMPTY'and o.parent is None);root.location=p;root.rotation_euler=(0,0,0);comp[aid]={'collection':c,'root':root,'Sroot':p}
assign(cs[1],rigs['submarine-yellow'],'dock-ready',12);assign(cs[2],rigs['dock-cover'],'uncover',12)
# Freeze exact evaluated companion meshes before independently selecting actor frame.
compS={a:geo(q['collection'])for a,q in comp.items()}
for q in comp.values():q['collection'].hide_render=True
ahcols=load(paths['approvedHut'],None);ah=next(c for c in ahcols if any(o.type=='MESH'for o in c.all_objects));ahr=next(o for o in ah.all_objects if o.type=='EMPTY'and o.parent is None);ahr.location=(.78,.35,.23);ahr.rotation_euler=(0,0,0);bpy.context.view_layer.update();compS['approvedHut']=geo(ah);ah.hide_render=True
H=B/'source/resources/approved-human-v3';rig=json.loads((H/'rig.json').read_text())
hcs=load(paths['human'],None,sorted({t['action']for clip in ['stand','walk']for t in rig['clips'][clip]['actions']}));hr=bpy.data.objects[rig['groundRootObject']];hc=next(c for c in hcs if hr in list(c.all_objects));records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 rot=Matrix.Rotation(a,3,'Z');fr.rotation_euler.z=a;er.rotation_euler.z=a;er.location=rot@Vector((0,-1.5,0))
 for case in plan['cases']:
  assign(hc,rig,case['actorClip'],case['nativeFrame']);hr.location=rot@Vector((*case['sourceFacingXY'],case['solvedRootZ']));hr.rotation_euler.z=a;bpy.context.view_layer.update()
  records.append({'direction':d,'case':case,'root':list(hr.location),'authoredScale':list(hr.scale),'actor':geo(hc),'floor':geo(fc),'entry':geo(ec)})
  print('EXTRACT',d,case['id'],flush=True)
report={'packetSHA256':'411bb31bdb772f94f7db68e7ae9d704dd6f376f090396a0af2c8cc97c8a0e65c','method':'Own explicit native cohort action assignment from exact rig/action resources; companions evaluated at12 before actor load and retained as actual world triangles/material state. No source resave. Full mesh extraction for36placed stances and true loadbearing solids.','sourcesBefore':before,'sourcesAfter':{k:sha(v)for k,v in paths.items()},'companionSourceFacingS':compS,'records':records,'camera':{'matrix':[list(r)for r in sc.camera.matrix_world],'filterSize':sc.render.filter_size,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'engine':sc.render.engine,'frame':sc.frame_current}}
assert report['sourcesBefore']==report['sourcesAfter']
with gzip.open(R/'own-native-geometry.json.gz','wt')as f:json.dump(report,f,separators=(',',':'))
print('DONE_NATIVE_EXTRACTION',len(records),flush=True)
