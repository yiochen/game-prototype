"""FINAL EXACT CONTEXT memory-only exact-fixture study. Never saves joined scenes."""
import bpy,json,math,hashlib,sys,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parents[1];OUT=O/'candidates/round-01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('cover_finite_geometry',H/'native_geometry.py');native=load('cover_rosa_native',H/'resources/native_actions.py')
bpy.ops.wm.open_mainfile(filepath=str(H/'cover.blend'));sc=bpy.context.scene;cover=bpy.data.collections['WarmSoft_dock-cover'];cr=bpy.data.objects['dock-cover__root'];cloth=bpy.data.objects['dock-cover__attached_canvas_hems_and_stitches'];sk=cloth.data.shape_keys;rig=json.loads((H/'rig.json').read_text());dirs={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
fixtures={};sourceHashes={}
def append(aid,path,colname,loc,actions=False):
 with bpy.data.libraries.load(str(path),link=False)as(src,dst):
  dst.collections=[colname]
  if actions:dst.actions=src.actions
 c=dst.collections[0];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;r=next(o for o in c.all_objects if o.type=='EMPTY'and o.parent is None);r.location=loc;r.rotation_euler=(0,0,0);fixtures[aid]={'collection':c,'root':r,'sourceRoot':loc};sourceHashes[aid]=sha(path);return c,r
fc,fr=append('floor',O/'inputs/approved-dock-family-v1/dock-floor/project.blend','WarmSoft_dock-floor',(0,0,0))
ec,er=append('entry',O/'inputs/approved-dock-family-v1/dock-entry/project.blend','S33_PROP_dock-entry',(0,-1.5,0))
hc,hr=append('hut',O/'inputs/approved-dock-family-v1/workshop-hut/project.blend','WarmSoft_workshop-hut',(.78,.35,.23))
subc,sr=append('sub',O/'inputs/approved-final-main-v1/project.blend','WarmSoft_submarine-yellow_stage1',(-.7,-.42,.23),True);subactions=json.loads(sr['nativeActions'])
RH=O/'inputs/shared-world-pose-v1/resources/source/resources/approved-human-v3';rrig=json.loads((RH/'rig.json').read_text());rp=RH/'customer-rosa-approved.blend'
with bpy.data.libraries.load(str(rp),link=False)as(src,dst):dst.collections=['S33_CHARACTER_customer_rosa.001'];dst.actions=sorted({t['action']for c in ['stand','walk']for t in rrig['clips'][c]['actions']})
rc=dst.collections[0];sc.collection.children.link(rc);rr=bpy.data.objects[rrig['groundRootObject']];sourceHashes['rosa']=sha(rp);plan=json.loads((O/'inputs/shared-world-pose-v1/plan.json').read_text())
assert all(abs(v-1.25)<1e-9 for v in rr.scale)
def coverpose(clip,f,d='S'):
 sk.animation_data.action=None
 for k in sk.key_blocks:k.value=0
 sk.animation_data.action=bpy.data.actions[rig['clips'][clip]['action']]
 if sk.animation_data.action.slots:sk.animation_data.action_slot=sk.animation_data.action.slots[0]
 R=Matrix.Rotation(dirs[d],3,'Z');cr.location=(0,0,.23);cr.rotation_euler.z=dirs[d]
 for a in fixtures.values():a['root'].location=R@Vector(a['sourceRoot']);a['root'].rotation_euler.z=dirs[d]
 sc.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
main_native=load('cover_final_main_native',H/'resources/main_native_common.py')
def subpose(clip):
 main_native.apply(clip,sc.frame_current+sc.frame_subframe,'S',(-.7,-.42,.23))
# Frozen exact authored1.25 human meshes for each of nine discrete approved source poses.
actorSnapshots={};materials={}
for case in plan['cases']:
 native.apply_clip({'root':rr,'collection':rc},rrig,case['actorClip'],case['nativeFrame'],'S',sc);rr.location=(*case['sourceFacingXY'],case['solvedRootZ']);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();c=bpy.data.collections.new('Rosa exact stance '+case['id']);sc.collection.children.link(c)
 for ob in rc.all_objects:
  if ob.type!='MESH'or ob.hide_render or not ob.visible_camera:continue
  ev=ob.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev,depsgraph=dg);sn=bpy.data.objects.new('stance__'+case['id']+'__'+ob.name,me);c.objects.link(sn);sn.matrix_world=ev.matrix_world.copy();sn['original_world_matrix']=[v for row in sn.matrix_world for v in row]
  for j,m in enumerate(sn.data.materials):
   if m:
    key=(case['id'],m.name)
    if key not in materials:
     mm=m.copy();mm.animation_data_clear()
     if mm.node_tree:mm.node_tree.animation_data_clear()
     materials[key]=mm
    sn.data.materials[j]=materials[key]
 c.hide_render=True;actorSnapshots[case['id']]=c
rc.hide_render=True
for ob in rc.all_objects:ob.hide_render=True
subpose('upgraded-dock-ready');coverpose('covered',1)
audit={'stage':'FINAL EXACT CONTEXT exact accepted dock + exact accepted final main + actual Rosa nine stances; canonical final family pending','coverSourceSHA256':sha(H/'cover.blend'),'fixtureSourceHashes':sourceHashes,'sharedPlanSHA256':sha(O/'inputs/shared-world-pose-v1/plan.json'),'pairedSourceNotSaved':True,'cameraProjectionDisclosure':'Physical environment55.0079798 degree reference only. Main consumer authored65 degrees and Rosa authored35 degrees remain separate; no cross-projection pixel identity claimed.','support':[],'clearance':[],'human':[],'nativeContexts':[],'unresolved':['Independent final review pending.','Actual independent authored-projection consumer evidence is supplied separately.']}
# Actual finite support surfaces at fixed root and .22world deck: each sole is a finite bottom polygon pair.
deck=g.surface(g.geometry(fc),True)
for row in g.geometry(cover):
 if 'bearing_sole'not in row['name']:continue
 lower=g.surface([row],False);rec=g.finite_gap(lower,deck,True);rec.update(support=row['name'],soleProjectedArea=sum(g.area(t['xy'])for t in lower));rec['finiteContactFraction']=rec['contactArea']/rec['soleProjectedArea'];audit['support'].append(rec)
# Finite canopy underside polygons vs real upper companion surfaces through every whole+half phase.
frames=[1+i*.5 for i in range(23)]+[12.5,13,16]
for clip in ['covered','uncover']:
 for f in frames:
  for mode in ['dock-ready','dock-charging','upgraded-dock-ready','upgraded-dock-charging']:
   subpose(mode);coverpose(clip,f);cg=g.geometry(cover);canopy=[r for r in cg if any(k in r['name']for k in ['attached_canvas','carrier','spindle','rounded_joint'])];lower=g.surface(canopy,False);cb,cn=g.bvh(cg);row={'clip':clip,'frame':f,'subMode':mode,'direction':'S','companions':{}}
   for aid,c in [('hut',hc),('sub',subc)]:
    gg=g.geometry(c);r=g.finite_gap(lower,g.surface(gg,True));tb,tn=g.bvh(gg);pairs=cb.overlap(tb);r['actualBVHTriangleIntersectionPairs']=len(pairs);r['intersectionOwners']=sorted(set((cn[a],tn[b])for a,b in pairs));row['companions'][aid]=r
   audit['clearance'].append(row)
  print('PHASE',clip,f,flush=True)
  (OUT/'family-audit-progress.json').write_text(json.dumps({'completedPhaseModes':len(audit['clearance'])})+'\n')
# Actual evaluated geometry under each required facing. Finite surface calculations are reused only after measured inverse-rigid parity.
canonicalPairs=[]
for clip in ['covered','uncover']:
 for f in frames:
  for mode in ['dock-ready','dock-charging','upgraded-dock-ready','upgraded-dock-charging']:
   subpose(mode);coverpose(clip,f,'S');base={aid:g.geometry(c)for aid,c in [('cover',cover),('floor',fc),('hut',hc),('sub',subc)]}
   baseBy={aid:{r['name']:r for r in rs}for aid,rs in base.items()}
   for d in ['N','E','S','W']:
    coverpose(clip,f,d);inv=Matrix.Rotation(-dirs[d],3,'Z');maximum=0.;meshes=0;verts=0;hashes={}
    for aid,c in [('cover',cover),('floor',fc),('hut',hc),('sub',subc)]:
     gg=g.geometry(c);assert {r['name']for r in gg}==set(baseBy[aid]),(aid,d,clip,f,mode)
     pts=[]
     for r in gg:
      old=baseBy[aid][r['name']];assert r['triangles']==old['triangles'];meshes+=1
      for v,w in zip(r['vertices'],old['vertices']):q=inv@v;maximum=max(maximum,(q-w).length);verts+=1;pts.append([round(z,5)for z in q])
     hashes[aid]=hashlib.sha256(json.dumps(pts).encode()).hexdigest()
    assert maximum<1e-5,(d,clip,f,mode,maximum)
    canonicalPairs.append({'clip':clip,'frame':f,'subMode':mode,'direction':d,'actualCoverRootMatrix':[list(r)for r in cr.matrix_world],'actualMainRootMatrix':[list(r)for r in sr.matrix_world],'inverseRigidMaximumVertexError':maximum,'visibleMeshes':meshes,'vertices':verts,'canonicalEvaluatedVertexHashes':hashes,'finiteEvidenceReference':{'sourceFacing':'S','clip':clip,'frame':f,'subMode':mode}})
 audit['actualAllFacingFiniteSurfaceCovariance']=canonicalPairs
 print('COVARIANCE',clip,flush=True)
# All nine exact human stances for covered, transition, terminal; actual finite surfaces and whole mesh intersections.
subpose('upgraded-dock-ready')
for clip,f in [(cl,fr)for cl in ['covered','uncover']for fr in frames]:
 coverpose(clip,f);cg=g.geometry(cover);cb,cn=g.bvh(cg);lower=g.surface([r for r in cg if any(k in r['name']for k in ['attached_canvas','carrier','spindle','rounded_joint'])],False)
 for case in plan['cases']:
  c=actorSnapshots[case['id']];c.hide_render=False;gg=g.geometry(c);tb,tn=g.bvh(gg);pairs=cb.overlap(tb);rec=g.finite_gap(lower,g.surface(gg,True));rec.update(clip=clip,frame=f,case=case['id'],authoredScale=1.25,rootS=[*case['sourceFacingXY'],case['solvedRootZ']],sourceNativeFrame=case['nativeFrame'],sourceNativeClip=case['actorClip'],actualBVHTriangleIntersectionPairs=len(pairs),intersectionOwners=sorted(set((cn[a],tn[b])for a,b in pairs)));audit['human'].append(rec);c.hide_render=True
# Capture fixed-frame full physical contexts plus exact single-camera depth diagnostics.
actor=actorSnapshots['exterior-stop'];actor.hide_render=False
for d in ['N','E','S','W']:
 R=Matrix.Rotation(dirs[d],4,'Z')
 for ob in actor.objects:
  a=ob['original_world_matrix'];ob.matrix_world=R@Matrix([a[i:i+4]for i in range(0,16,4)])
 for clip,f in [('covered',1),('uncover',6),('uncover',12)]:
  subpose('upgraded-dock-ready');coverpose(clip,f,d);p=OUT/'native-family'/f'{clip}-{d}-{f:02d}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);audit['nativeContexts'].append({'path':str(p.relative_to(O)),'sha256':sha(p),'clip':clip,'frame':f,'direction':d,'kind':'physical55degree technical reference, accepted final body/canonical equipment'})
  if f==12:
   cover.hide_render=True;p=OUT/'native-family'/f'family-without-cover-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);cover.hide_render=False
   for q in fixtures.values():q['collection'].hide_render=True
   actor.hide_render=True;p=OUT/'native-family'/f'cover-composition-root-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
   for q in fixtures.values():q['collection'].hide_render=False
   actor.hide_render=False
(OUT/'final-family-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('COMPLETE FINAL EXACT CONTEXT FAMILY',len(audit['clearance']),len(audit['human']))
