import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parents[1];OUT=O/'candidates/round-02';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(H/'cover.blend'));sc=bpy.context.scene;col=bpy.data.collections['WarmSoft_dock-cover'];root=bpy.data.objects['dock-cover__root'];cloth=bpy.data.objects['dock-cover__attached_canvas_hems_and_stitches'];rig=json.loads((H/'rig.json').read_text());sk=cloth.data.shape_keys
assert sc.render.filter_size==.5
DIRS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def pose(clip,frame,d):
 sk.animation_data.action=None
 for k in sk.key_blocks:k.value=0
 sk.animation_data.action=bpy.data.actions[rig['clips'][clip]['action']]
 if sk.animation_data.action.slots:sk.animation_data.action_slot=sk.animation_data.action.slots[0]
 root.rotation_euler.z=DIRS[d];root.location=(0,0,0);sc.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
def sample():
 dg=bpy.context.evaluated_depsgraph_get();vs=[];rows=[]
 for ob in col.all_objects:
  if ob.type!='MESH':continue
  e=ob.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@q.co for q in m.vertices];vs+=v;rows.append({'name':ob.name,'vertices':len(v),'evaluatedWorldVertexSHA256':hashlib.sha256(json.dumps([[round(x,7)for x in p]for p in v]).encode()).hexdigest(),'bounds':[[min(p[i]for p in v)for i in range(3)],[max(p[i]for p in v)for i in range(3)]]});e.to_mesh_clear()
 return {'bounds':[[min(p[i]for p in vs)for i in range(3)],[max(p[i]for p in vs)for i in range(3)]],'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r)for r in root.matrix_world],'objects':rows}
audit={'stage':'standalone candidate captures; independent review pending','sourceSHA256':sha(H/'cover.blend'),'blender':bpy.app.version_string,'nativeFrame':[1472,1408],'filter_size':sc.render.filter_size,'camera':json.loads((H/'camera.json').read_text()),'renders':[],'inbetweens':[],'materials':[{'name':m.name,'alpha':[n.inputs['Alpha'].default_value for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'],'imageTextureNodes':[n.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE']}for m in bpy.data.materials if m.use_nodes],'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size}for o in sc.objects if o.type=='LIGHT']}
for clip in ['covered','uncover']:
 for d in DIRS:
  for i in range(12):
   pose(clip,i+1,d);r=sample();r.update(clip=clip,direction=d,index=i,frame=i+1);p=OUT/'frames'/f'{clip}-{d}'/f'{i:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);r.update(path=str(p.relative_to(O)),sha256=sha(p));audit['renders'].append(r)
  for frame in [1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13,16]:
   pose(clip,frame,d);r=sample();r.update(clip=clip,direction=d,frame=frame);audit['inbetweens'].append(r)
   if d in ['E','S']and frame in [1.5,6.5,11.5]:
    p=OUT/'inbetweens'/f'{clip}-{d}-{frame}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);r.update(path=str(p.relative_to(O)),sha256=sha(p))
# Equality of native key states, not filenames.
audit['closure']={}
for clip,a,b in [('covered',1,13),('uncover',12,16)]:
 pose(clip,a,'S');x=sample();pose(clip,b,'S');y=sample();audit['closure'][clip]={'frames':[a,b],'actualEvaluatedVertexHashesEqual':[o['evaluatedWorldVertexSHA256']for o in x['objects']]==[o['evaluatedWorldVertexSHA256']for o in y['objects']]}
pts=[p for r in audit['renders']+audit['inbetweens']for p in r['bounds']];audit['maximumEvaluatedEnvelope']=[[min(p[i]for p in pts)for i in range(3)],[max(p[i]for p in pts)for i in range(3)]]
(OUT/'native-phase-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('COMPLETE STANDALONE',len(audit['renders']))
