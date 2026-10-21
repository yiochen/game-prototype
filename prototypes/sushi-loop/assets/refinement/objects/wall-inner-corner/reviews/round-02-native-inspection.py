import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];R=B/'candidates/round-02';q=json.loads((R/'packet.json').read_text());family=json.loads((R/'family-settings.json').read_text())
source=(R/q['files']['originalProject']['path']).resolve();candidate=(R/q['files']['candidateProject']['path']).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parts():
 c=next(c for c in bpy.data.collections if 'wall-inner-corner' in c.name)
 root=next(o for o in c.all_objects if o.type=='EMPTY' and '__root' in o.name)
 root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
 out={}
 for o in c.all_objects:
  if o.type=='MESH' and '__cut_' not in o.name:
   name=o.name.split('__',1)[1].split('.')[0]
   out[name]=[list(root.matrix_world.inverted()@o.matrix_world@v.co)for v in o.data.vertices]
 return c,root,out
bpy.ops.wm.open_mainfile(filepath=str(source));c,root,src=parts()
bpy.ops.wm.open_mainfile(filepath=str(candidate));c,root,cur=parts();s=bpy.context.scene
profiles=[]
for name,pts in src.items():
 for port,axis,plane in [('W',0,-.5),('N',1,.5)]:
  old=[p for p in pts if abs(p[axis]-plane)<1e-7];new=[p for p in cur[name]if abs(p[axis]-plane)<1e-7]
  dist=lambda a,b:max(min(sum((x-y)**2 for x,y in zip(p,q))for q in b)**.5 for p in a)
  # Compare geometric cross-section segments, allowing added collinear sampling vertices.
  axes=[i for i in range(3)if i!=axis]
  old2=sorted(set(tuple(p[i]for i in axes)for p in old))
  cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  def hull(points):
   lo=[];hi=[]
   for v in points:
    while len(lo)>1 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
    lo.append(v)
   for v in reversed(points):
    while len(hi)>1 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
    hi.append(v)
   return lo[:-1]+hi[:-1]
  poly=hull(old2)
  def segmentdist(p,a,b):
   ab=[b[i]-a[i]for i in range(2)];t=max(0,min(1,sum((p[i]-a[i])*ab[i]for i in range(2))/sum(v*v for v in ab)))
   return sum((p[i]-a[i]-t*ab[i])**2 for i in range(2))**.5
  boundarydist=max(min(segmentdist(tuple(p[i]for i in axes),poly[k],poly[(k+1)%len(poly)])for k in range(len(poly)))for p in new)
  profiles.append({'part':name,'port':port,'sourceCount':len(old),'candidateCount':len(new),'sourceVerticesRetainedMaxDistance':dist(old,new),'candidateToSourceProfileSegmentsMaxDistance':boundarydist,'subdivisionAllowed':True})
allpts=[p for pts in cur.values()for p in pts];bounds=[[min(p[i]for p in allpts),max(p[i]for p in allpts)]for i in range(3)]
lights=[]
for o in s.objects:
 if o.type=='LIGHT':
  ref=next(i for i in family['lighting']['lights']if i['name']==o.name)
  lights.append({'name':o.name,'matrixMaxError':max(abs(o.matrix_world[i][j]-ref['matrix'][i][j])for i in range(4)for j in range(4)),'energyMatch':o.data.energy==ref['energy'],'sizeMatch':o.data.size==ref['size'],'typeMatch':o.data.type==ref['type'],'colorMatch':list(o.data.color)==ref['color']})
p=world_to_camera_view(s,s.camera,Vector((0,0,0)))
fc=family['capture']['camera'];cam=s.camera
result={'candidateSha256':sha(candidate),'packetSha256':sha(R/'packet.json'),'sourceSha256':sha(source),'candidateScene':s.name,'meshes':sum(o.type=='MESH'for o in c.all_objects),'otherRenderObjects':[{ 'name':o.name,'type':o.type}for o in s.objects if o.name not in c.all_objects and o.type not in ('LIGHT','CAMERA')],'sourceParts':list(src),'candidateParts':list(cur),'profiles':profiles,'bounds':bounds,'noVerticesInConcaveClearance':not any(p[0]<-.180001 and p[1]>.180001 for p in allpts),'noZeroAreaFaces':not any(p.area<1e-12 for o in c.all_objects if o.type=='MESH' for p in o.data.polygons),'camera':{'matrixMaximumErrorToApprovedFamily':max(abs(cam.matrix_world[i][j]-fc['worldMatrix'][i][j])for i in range(4)for j in range(4)),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelRoot':[p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y],'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},'lights':lights,'render':{'engine':s.render.engine,'samples':s.cycles.samples,'denoise':s.cycles.use_denoising,'transparent':s.render.film_transparent,'fps':s.render.fps,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure},'resources':{'externalUnpackedImages':[i.filepath for i in bpy.data.images if i.source=='FILE'and not i.packed_file],'linkedLibraries':[l.filepath for l in bpy.data.libraries]},'savedProjectUnchanged':sha(candidate)==q['files']['candidateProject']['sha256']}
(B/'reviews/round-02-native-inspection.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k]for k in ('candidateSha256','meshes','bounds','noVerticesInConcaveClearance','noZeroAreaFaces','camera','savedProjectUnchanged')}));print('Profiles max error',max(max(p['sourceVerticesRetainedMaxDistance'],p['candidateToSourceProfileSegmentsMaxDistance'])for p in profiles))
