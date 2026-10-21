import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'reviews'
brief=json.loads((BASE/'brief.json').read_text())
record=json.loads((BASE/'inputs/source-camera.json').read_text())
def matrix(m): return [list(row) for row in m]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
reports={}
for label,path,needle in [('source',(BASE/brief['source']['project']).resolve(),'S33_PROP_rock-wall-edge.001'),('approvedMiddle',BASE/'inputs/approved-middle/project.blend','rock-wall-middle__asset')]:
 bpy.ops.wm.open_mainfile(filepath=str(path))
 coll=bpy.data.collections.get(needle)
 coll.hide_viewport=False
 for lc in bpy.context.view_layer.layer_collection.children:
  if lc.collection==coll: lc.exclude=False; lc.hide_viewport=False
 bpy.context.view_layer.update()
 obs=list(coll.all_objects)
 meshes=[o for o in obs if o.type=='MESH']
 verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 ports=[]
 for x in [-.5,.5]:
  pts=[]
  for o in meshes:
   local=[]
   for v in o.data.vertices:
    p=o.matrix_world@v.co
    if abs(p.x-x)<1e-6: local.append([round(p.y,8),round(p.z,8)])
   if local: pts.append({'mesh':o.name,'count':len(local),'uniqueYZ':sorted({tuple(p) for p in local}) if len(local)<50 else None})
  ports.append({'x':x,'meshes':pts})
 cameras=[]
 for o in bpy.data.objects:
  if o.type=='CAMERA':
   delta=max(abs(o.matrix_world[r][c]-record['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4))
   if delta<1e-5:
    cameras.append({'name':o.name,'worldMatrixMaxDelta':delta,'type':o.data.type,'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],'sensorFit':o.data.sensor_fit})
 reports[label]={'project':str(path),'sha256':sha(path),'scene':bpy.context.scene.name,'collection':coll.name,'roots':[{'name':o.name,'matrix':matrix(o.matrix_world),'properties':dict(o.items())} for o in obs if o.type=='EMPTY'],'bounds':{'min':[min(p[i] for p in verts) for i in range(3)],'max':[max(p[i] for p in verts) for i in range(3)]},'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'materials':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]} for o in meshes],'exactPlaneSamples':ports,'matchingRegisteredCameras':cameras,'sceneCamera':{'name':bpy.context.scene.camera.name,'matrix':matrix(bpy.context.scene.camera.matrix_world),'orthoScale':bpy.context.scene.camera.data.ortho_scale,'shift':[bpy.context.scene.camera.data.shift_x,bpy.context.scene.camera.data.shift_y]} if bpy.context.scene.camera else None,'sceneRender':{'resolution':[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y],'pixelAspect':[bpy.context.scene.render.pixel_aspect_x,bpy.context.scene.render.pixel_aspect_y]},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'shadow':o.data.use_shadow,'matrix':matrix(o.matrix_world)} for o in bpy.context.scene.objects if o.type=='LIGHT'],'images':[{'name':im.name,'source':im.source,'path':im.filepath} for im in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]}
 if label=='approvedMiddle':
  ob=next(o for o in meshes if 'continuous_carved' in o.name); me=ob.data
  ends=[sorted([v for v in me.vertices if abs(v.co.x-x)<1e-6],key=lambda v:(round(v.co.y,7),round(v.co.z,7))) for x in [-.5,.5]]
  ca=me.color_attributes['stone_albedo']
  reports[label]['independentlyMeasuredPairedBoundary']={'countEach':list(map(len,ends)),'maxYZDelta':max(max(abs(a.co[i]-b.co[i]) for i in [1,2]) for a,b in zip(*ends)),'maxPointAlbedoDelta':max(max(abs(ca.data[a.index].color[i]-ca.data[b.index].color[i]) for i in range(4)) for a,b in zip(*ends)),'maxVertexNormalDelta':max((a.normal-b.normal).length for a,b in zip(*ends)),'maxAbsoluteXNormalAtBoundary':max(abs(v.normal.x) for end in ends for v in end)}
  mat=me.materials[0]; bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  reports[label]['independentlyInspectedMaterial']={'name':mat.name,'nodes':[n.type for n in mat.node_tree.nodes],'roughness':bs.inputs['Roughness'].default_value,'specularIORLevel':bs.inputs['Specular IOR Level'].default_value,'emissionStrength':bs.inputs['Emission Strength'].default_value}
(OUT/'initial-source-audit.json').write_text(json.dumps(reports,indent=2,default=str))
print(json.dumps({label:{'sha256':r['sha256'],'bounds':r['bounds'],'meshCount':len(r['meshes']),'registeredCameraCount':len(r['matchingRegisteredCameras']),'exactPlaneSamples':r['exactPlaneSamples']} for label,r in reports.items()},default=str))
