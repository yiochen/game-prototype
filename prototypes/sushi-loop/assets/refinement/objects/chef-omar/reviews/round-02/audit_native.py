"""Judge-only fresh reopening and source render; no saved native edits."""
import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib,importlib.util
from pathlib import Path
import numpy as np
from mathutils import Vector
B=Path(__file__).resolve().parents[2]; S=B/'candidates/round-02/portable-replay/source'; R=Path(__file__).resolve().parent
sys.path.insert(0,str(S));from food_common_round02 import *
spec=importlib.util.spec_from_file_location('judge_semantics',B/'source/semantic_food_round02.py');sem=importlib.util.module_from_spec(spec);spec.loader.exec_module(sem)
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def sample(project,c,is_candidate=False):
 bpy.ops.wm.open_mainfile(filepath=str(S/project));sc,coll,root,arm,rig,asset,plane=setup(c)
 static=sem.static_scene(sc,coll,plane,rig,native);static.pop('foodDrivers');frame_rows=[];visibleknife=[];foodrows=[]
 width=float(plane.data.vertices[1].co.x-plane.data.vertices[0].co.x);height=width*c['canonicalSize'][1]/c['canonicalSize'][0]
 canonical=[Vector(v) for v in [(-width/2,0,0),(width/2,0,0),(width/2,height,0),(-width/2,height,0)]]
 im=image_node(plane).image
 details={'projectSHA256':sha(S/project),'scene':sc.name,'camera':sc.camera.name,'cameraType':sc.camera.data.type,'cameraMatrix':[list(r) for r in sc.camera.matrix_world],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'resolutionPercent':sc.render.resolution_percentage,'rootScale':list(root.scale),'imageSize':list(im.size),'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest(),'imageAlpha':im.alpha_mode,'colorspace':im.colorspace_settings.name,'vertices':[list(v.co) for v in plane.data.vertices],'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'foodDrivers':sem.drivers(plane),'libraryPaths':[l.filepath for l in bpy.data.libraries]}
 for cl in rig['clips']:
  for d in ['N','E','S','W']:
   for i in range(12):
    native.apply_clip(asset,rig,cl,i+1,d,sc);dg=bpy.context.evaluated_depsgraph_get();meshes={};palms={}
    for o in coll.all_objects:
     if o.type!='MESH' or o==plane:continue
     if '__knife_' in o.name:
      ar,m=sem.rigid_geometry_from_evaluated_parent(o,dg)
      if not(o.hide_viewport or o.hide_get()):
       actual=sem.evaluated(o,dg);visibleknife.append(max(float(np.max(np.abs(a-b))) for a,b in zip(ar,actual)))
     else:
      assert not(o.hide_viewport or o.hide_get()),o.name
      ar=sem.evaluated(o,dg)
     meshes[o.name]={'vertices':len(ar[0]),'corners':len(ar[2]),'positions':h(ar[0]),'vertexNormals':h(ar[1]),'cornerNormals':h(ar[2])}
     if '__palm_' in o.name or '__minimal_foot_' in o.name:palms[o.name]=h(ar[0])
    ae=arm.evaluated_get(dg);poses=np.array([np.array(ae.matrix_world@b.matrix,dtype=np.float64) for b in ae.pose.bones]);parents={o.name:h(np.array(o.evaluated_get(dg).matrix_world)) for o in coll.all_objects if o.type=='EMPTY'}
    vis={o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in coll.all_objects}
    frame_rows.append({'clip':cl,'direction':d,'index':i,'meshes':meshes,'poseHash':h(poses),'parentHashes':parents,'contactHashes':palms,'visibility':vis,'rootYawDegrees':math.degrees(root.rotation_euler.z)})
    flags=(plane.hide_viewport,plane.hide_get());plane.hide_viewport=False;plane.hide_set(False);bpy.context.view_layer.update();e=plane.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.matrix_world.copy();ps=[m@v for v in (canonical if not is_candidate else [v.co for v in plane.data.vertices])]
    parent=plane.parent.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world@plane.matrix_parent_inverse;offset=m.translation-parent.translation;rv=ray(sc);depth=offset.dot(rv);perp=(offset-rv*depth).length
    foodrows.append({'clip':cl,'direction':d,'index':i,'quad':[px(sc,v).tolist() for v in ps],'bottom':px(sc,(ps[0]+ps[1])*.5).tolist(),'origin':list(m.translation),'depth':depth,'perpendicular':perp,'parentHash':h(np.array(parent))})
    plane.hide_viewport=flags[0];plane.hide_set(flags[1]);bpy.context.view_layer.update()
 intermediates=[]
 if is_candidate:
  angles=sorted(set([-180,-135,-45,0,45,135,180]+[s*(90+e) for s in [-1,1] for e in [-.1,-.02,-.015,-.0146,-.0145,-.014,-.01,-.001,0,.001,.01,.014,.0145,.0146,.015,.02,.1]]))
  hold='hold-cucumber' if c['variant']=='cucumber' else 'hold'
  for a in angles:
   native.apply_clip(asset,rig,hold,6,'S',sc);root.rotation_euler.z=math.radians(a);root.update_tag();bpy.context.view_layer.update();e=plane.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.matrix_world.copy();parent=plane.parent.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world@plane.matrix_parent_inverse;offset=m.translation-parent.translation;rv=ray(sc);depth=offset.dot(rv);f=math.cos(root.rotation_euler.z);want=.5999999971247001-(.5999999971247001-.4)*max(0,-f)**2
   intermediates.append({'angle':a,'actualYaw':math.degrees(root.rotation_euler.z),'f':f,'depth':depth,'expected':want,'error':abs(depth-want),'perpendicular':(offset-rv*depth).length,'XYZ':list(plane.location)})
 return {'details':details,'static':static,'frames':frame_rows,'food':foodrows,'intermediates':intermediates,'visibleKnifeChecks':len(visibleknife),'maxVisibleKnifeReconstructionError':max(visibleknife,default=0)}
results={}
for runtime in [False,True]:
 c=config(runtime);old=sample(c['basis'],c);new=sample(c['candidate'],c,True)
 # Remove food mapping and image pointer only; nonfood static scene and shader remain exact.
 static_equal=old['static']==new['static'];diffs=[];proj=bottom=perp=law=0
 for a,b in zip(old['frames'],new['frames']):
  if a!=b:diffs.append({'clip':b['clip'],'direction':b['direction'],'index':b['index'],'differentKeys':[k for k in a if a[k]!=b[k]]})
 for a,b in zip(old['food'],new['food']):
  proj=max(proj,float(np.max(np.abs(np.array(a['quad'])-b['quad']))));bottom=max(bottom,float(np.max(np.abs(np.array(a['bottom'])-b['bottom']))));delta=Vector(b['origin'])-Vector(a['origin']);rv=None
  # This source's camera is registered along(0,-cos35,sin35).
  rv=Vector((0,-math.cos(math.radians(35)),math.sin(math.radians(35))));perp=max(perp,(delta-rv*delta.dot(rv)).length);want=.4 if b['direction']=='N' else .5999999971247001;law=max(law,abs(b['depth']-want))
 result={'source':old['details'],'candidate':new['details'],'staticEqual':static_equal,'staticDifferentKeys':[k for k in old['static'] if old['static'][k]!=new['static'][k]],'allFrameBodyPoseContactsVisibilityExactHashEqual':not diffs,'frameDifferences':diffs,'sourceFrames':len(old['frames']),'candidateFrames':len(new['frames']),'meshCount':len(new['frames'][0]['meshes']),'shippingMaximum':{'quadNativePx':proj,'bottomNativePx':bottom,'rayDisplacementPerpendicularWorld':perp,'depthLawErrorWorld':law},'visibleKnifeCrosscheckCountSourceAndCandidate':old['visibleKnifeChecks']+new['visibleKnifeChecks'],'visibleKnifeCrosscheckMaximum':max(old['maxVisibleKnifeReconstructionError'],new['maxVisibleKnifeReconstructionError']),'intermediateCount':len(new['intermediates']),'intermediateMaximum':{'depthErrorWorld':max(x['error'] for x in new['intermediates']),'perpendicularWorld':max(x['perpendicular'] for x in new['intermediates'])},'intermediates':new['intermediates'],'compactFrames':new['frames']}
 results[c['variant']]=result;write(R/'native-audit.json',results);print('JUDGE AUDIT',c['variant'],static_equal,len(diffs),result['shippingMaximum'],flush=True)
 # Read-only fresh source capture from exact saved projects, same renderer/settings/camera.
 for mode,project in [('candidate',c['candidate']),('approved',c['basis'])]:
  bpy.ops.wm.open_mainfile(filepath=str(S/project));sc,coll,root,arm,rig,asset,plane=setup(c);enable_saved_device(sc)
  hold='hold-cucumber' if runtime else 'hold';load='load-cucumber' if runtime else 'load'
  cases=[(hold,d,5,None) for d in ['N','E','S','W']]+[(load,'N',5,None),(load,'S',5,None),(load,'W',11,None)]
  if not runtime:cases += [('work','S',5,None)]
  if mode=='candidate':cases += [(hold,'S',5,a) for a in [-135,-90.1,90.1,135]]
  else:cases=[(hold,'N',5,None),(hold,'S',5,None)]+([] if runtime else [('work','S',5,None)])
  rr=[]
  for cl,d,i,angle in cases:
   native.apply_clip(asset,rig,cl,i+1,d,sc)
   if angle is not None:root.rotation_euler.z=math.radians(angle);root.update_tag();bpy.context.view_layer.update()
   name=f'{cl}-{d}-{i:03d}'+('' if angle is None else f'-turn{angle:+07.2f}');path=R/'fresh'/c['variant']/mode/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);rr.append({'path':str(path.relative_to(R)),'sha256':sha(path),'clip':cl,'direction':d,'index':i,'angle':angle,'projectSHA256':sha(S/project),'scene':sc.name,'camera':sc.camera.name,'resolution':[sc.render.resolution_x,sc.render.resolution_y]});write(R/f'fresh-{c["variant"]}-{mode}.json',rr)
print('JUDGE COMPLETE',flush=True)
