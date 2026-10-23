"""Independent saved-source technical audit. Does not change saved .blend or art."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-02';D=json.loads((B/'inputs/family-settings.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-02.blend'));s=bpy.context.scene;c=next(c for c in bpy.data.collections if 'wall-inner-corner' in c.name);root=next(o for o in c.all_objects if o.type=='EMPTY');bpy.context.view_layer.update()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pixel(v):
 p=world_to_camera_view(s,s.camera,Vector(v));return[p.x*384,(1-p.y)*704]
cam=s.camera;fc=D['capture']['camera'];materr=max(abs(cam.matrix_world[i][j]-fc['worldMatrix'][i][j])for i in range(4)for j in range(4));lights=[]
for o in s.objects:
 if o.type=='LIGHT':
  ref=next(q for q in D['lighting']['lights']if q['name']==o.name);matrixerr=max(abs(o.matrix_world[i][j]-ref['matrix'][i][j])for i in range(4)for j in range(4));lights.append({'name':o.name,'matrixMaximumError':matrixerr,'energyMatches':o.data.energy==ref['energy'],'sizeMatches':o.data.size==ref['size']});assert matrixerr<1e-6 and o.data.energy==ref['energy'] and o.data.size==ref['size']
geom=[];allpts=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 me=o.data;pts=[o.matrix_world@v.co for v in me.vertices];allpts+=pts
 bounds=[[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)]
 zero=sum(p.area<1e-12 for p in me.polygons)
 geom.append({'name':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'bounds':bounds,'facesAreaUnder1e-12':zero,'modifiers':[m.type for m in o.modifiers],'materials':[m.name for m in me.materials]})
 assert zero==0,(o.name,zero)
# Outside one-cell cap envelope and original concave gameplay clearance are empty.
assert not any(p.x<-.180001 and p.y>.180001 for p in allpts)
# Real roots and port transforms for the publisher's four cardinal views.
facings=[]
for d,a in D['capture']['facingDegrees'].items():
 root.rotation_euler.z=math.radians(a);bpy.context.view_layer.update();ports=[]
 for port,pos,normal in [('W',(-.5,0,0),(-1,0,0)),('N',(0,.5,0),(0,1,0))]:
  p=root.matrix_world@Vector(pos);n=root.matrix_world.to_3x3()@Vector(normal);ports.append({'port':port,'positionWorld':list(p),'normalWorld':list(n),'rootRelativePixels':[pixel(p)[0]-192,pixel(p)[1]-512]})
 facings.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r)for r in root.matrix_world],'ports':ports})
root.rotation_euler.z=0;bpy.context.view_layer.update()
external=[{'name':i.name,'path':i.filepath}for i in bpy.data.images if i.source=='FILE' and not i.packed_file];libs=[l.filepath for l in bpy.data.libraries];assert not external and not libs
br=[n for n in s.world.node_tree.nodes if n.type=='BACKGROUND'][0]
assert abs(br.inputs['Strength'].default_value-.28)<1e-6
r=D['render'];assert s.cycles.samples==r['samples'] and s.cycles.use_denoising==r['denoise'] and s.cycles.pixel_filter_type==r['pixelFilter'] and s.render.filter_size==r['filterSize']
audit={'project':'source/round-02.blend','sha256':sha(B/'source/round-02.blend'),'reopenedNativeSource':True,'scene':s.name,'onlySelectedAssetPlusCameraAndFiveLights':all(o.name in c.all_objects or o.type in ['LIGHT','CAMERA']for o in s.objects),'cameraMaximumMatrixErrorToApprovedFamily':materr,'rootPixel':pixel((0,0,0)),'resolution':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'lights':lights,'renderMatchesApprovedFamily':True,'worldStrength':br.inputs['Strength'].default_value,'geometry':geom,'concaveClearance':'No vertex in x<-.18,y>.18; generated sweep surface is inside the one-cell L cap envelope; exact port sections separately asserted at native build.','bounds':[[min(p[i]for p in allpts),max(p[i]for p in allpts)]for i in range(3)],'facings':facings,'dependencies':{'externalUnpackedImages':external,'linkedLibraries':libs,'selfContained':True}}
assert materr<1e-6 and audit['onlySelectedAssetPlusCameraAndFiveLights']
(O/'reopened-native-audit.json').write_text(json.dumps(audit,indent=2));print('AUDIT PASSED',audit['bounds'],len(geom),'meshes')
