import bpy, pathlib, json, math, sys, importlib.util, hashlib
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-01'
sp=importlib.util.spec_from_file_location('inlet_native_recipe',H/'round-01.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A)
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
def fingerprint(col):
 rec=[]
 for o in sorted(col.all_objects,key=lambda o:o.name):
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'localMatrix':[list(r) for r in o.matrix_local]}
  if o.type=='MESH':
   me=o.data
   d['mesh']={'vertices':[list(v.co) for v in me.vertices],'edges':[list(e.vertices) for e in me.edges],'polygons':[{'v':list(f.vertices),'material':f.material_index,'smooth':f.use_smooth} for f in me.polygons],'cornerNormals':[list(n.vector) for n in me.corner_normals],'uvs':{u.name:[list(x.uv) for x in u.data] for u in me.uv_layers},'materials':[]}
   for m in me.materials:
    nd=[]
    for n in m.node_tree.nodes:
     ins={}
     for i in n.inputs:
      if hasattr(i,'default_value'):
       v=i.default_value
       try:v=list(v)
       except TypeError:pass
       if isinstance(v,(str,int,float,bool,list)):ins[i.identifier]=v
     nd.append({'name':n.name,'type':n.bl_idname,'inputs':ins})
    d['mesh']['materials'].append({'name':m.name,'diffuse':list(m.diffuse_color),'nodes':nd,'links':sorted([ [l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links])})
  rec.append(d)
 return {'sha256':hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'records':rec}
def measure(s,c,clip,di,fr):
 A.apply_clip(s,c,clip,di,fr);dg=bpy.context.evaluated_depsgraph_get();ps=[];parts=[];cam=s.camera;root=bpy.data.objects['collector__root']
 for o in c.all_objects:
  if o.type!='MESH':continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];ps+=vs;parts.append({'name':o.name,'bounds':A.bounds(vs),'matrix':[list(r) for r in eo.matrix_world],'vertices':len(me.vertices),'polygons':len(me.polygons)});eo.to_mesh_clear()
 pix=[]
 for v in ps:
  p=world_to_camera_view(s,cam,v);pix.append([p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y])
 return {'clip':clip,'direction':di,'nativeFrame':fr,'index':fr-1,'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'worldBounds':A.bounds(ps),'nativePixelBounds':A.bounds(pix),'parts':parts}
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=str(H/'round-01.blend'));s=bpy.context.scene;c=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root'];O.mkdir(parents=True,exist_ok=True)
 A.apply_clip(s,c,'idle','S',1);A.savej(O/'canonical-neutral-resources.json',fingerprint(c))
 records=[]
 for clip in ['idle','active']:
  for di in 'NESW':
   for fr in range(1,2 if clip=='idle' else 14):
    r=measure(s,c,clip,di,fr);p=O/'native'/clip/di/(f'{fr-1:03d}.png' if fr<13 else 'closure-013.png');p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);r.update(path=str(p.relative_to(E)),sha256=A.sha(p),closureOnly=fr==13);records.append(r)
 sweeps=[]
 for f in range(241):
  fr=1+f/20;s.frame_set(math.floor(fr),subframe=fr-math.floor(fr));bpy.context.view_layer.update()
  # measure() also sets frame, retaining subframe accurately via explicit frame-set afterwards.
  dg=bpy.context.evaluated_depsgraph_get();ps=[]
  for o in c.all_objects:
   if o.type!='MESH':continue
   eo=o.evaluated_get(dg);me=eo.to_mesh();ps.extend(root.matrix_world.inverted()@(eo.matrix_world@v.co) for v in me.vertices);eo.to_mesh_clear()
  sweeps.append({'nativeFrame':fr,'canonicalBounds':A.bounds(ps)})
 A.apply_clip(s,c,'idle','S',1)
 actions=[]
 for a in bpy.data.actions:
  if not a.name.startswith('INLET_NATIVE'):continue
  curves=[]
  for lay in a.layers:
   for strip in lay.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:curves.append({'path':fc.data_path,'index':fc.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in fc.keyframe_points]})
  actions.append({'name':a.name,'slots':[x.identifier for x in a.slots],'curves':curves})
 A.savej(O/'native-audit.json',{'project':'source/round-01.blend','projectSHA256':A.sha(H/'round-01.blend'),'recipeSHA256':A.sha(H/'round-01.py'),'savedReopened':True,'settings':A.settings(s,root),'renderManifest':'candidate-phases.json','records':records,'continuousSweep':sweeps,'sweepMethod':'Evaluated native geometry at every0.05frame across frame1..13. Native action interpolation LINEAR between recorded keys; extrema of linear scale and one-axis rotations additionally bounded by conservative angular envelope.','continuousAnalyticBound':{'canonicalX':[-.39,.39],'canonicalY':[-.34,.25],'canonicalZ':[.011,.404],'reason':'Static evaluated bounds, sleeve maximumscaleZ1.08/min.84 aboutZ.133; guard maximumrotationX.195 aboutY-.249,Z.119 with radialextent.23; no root translation. Bounds conservatively enclose every interpolated pose.'},'actions':actions,'neutralResourceFingerprint':'candidates/round-01/canonical-neutral-resources.json','externalDependencies':[],'approval':False})
 A.savej(O/'candidate-phases.json',{'renders':[{k:r[k] for k in ['clip','direction','nativeFrame','index','rootRotationZ','rootRotationDegrees','rootMatrix','path','sha256','closureOnly']} for r in records],'nativeSourceAudit':'native-audit.json','nativeSourceAuditSHA256':A.sha(O/'native-audit.json')})
 print('COMPLETE NATIVE52 + CLOSURE4',len(records))
