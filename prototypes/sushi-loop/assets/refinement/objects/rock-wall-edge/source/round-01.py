import bpy,math,json,hashlib,random,struct,shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01';O.mkdir(parents=True,exist_ok=True)
PROFILE=[(-.5,0),(.5,0),(.5,.67),(.45,1.04),(.31,1.15),(-.31,1.15),(-.45,1.04),(-.5,.67)]
DIR={'S':0,'E':90,'N':180,'W':-90}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'brief.json')=='c2ee6eed672b221415a154debf477cdf1f731042cb4813f48c4661068c2e8911'
assert sha(B/'reviews/proposedcriteria.json')=='43d883bf96be19bf842287660846bccccb0b72c81015eb304ca4650260d66bba'
bpy.ops.wm.open_mainfile(filepath=str(B/'inputs/approved-middle/project.blend'))
sc=bpy.context.scene;sc.name='Rock wall edge native round 01';root=bpy.data.objects['rock-wall-middle__root'];coll=root.users_collection[0]
side=bpy.data.objects['rock-wall-middle__continuous_carved_stone'];caps=[bpy.data.objects['rock-wall-middle__W_connector_stone'],bpy.data.objects['rock-wall-middle__E_connector_stone']]
bpy.context.view_layer.update()
# Preserve exact approved endpoint geometry, vertex albedo, and actual corner normals.
referenceSide=side.data.copy();referenceCaps=[o.data.copy() for o in caps]
root.name='rock-wall-edge__root';root['assetId']='rock-wall-edge';root['ports']=json.dumps([{'direction':'W','position':[-.5,0,0],'profile':'rock-wall-full-cell-v2'},{'direction':'E','position':[.5,0,0],'profile':'rock-wall-full-cell-v2'}]);root['visual_height']=1.17
coll.name='rock-wall-edge__asset'
for ob in [side]+caps:ob.name=ob.name.replace('rock-wall-middle','rock-wall-edge')
def clamp(v,a=0,b=1):return min(b,max(a,v))
def smooth(v):v=clamp(v);return v*v*(3-2*v)
def mix(a,b,t):return a*(1-t)+b*t
def srgb(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
lengths=[math.dist(PROFILE[i],PROFILE[(i+1)%8]) for i in range(8)];starts=[0]
for le in lengths:starts.append(starts[-1]+le)
PER=sum(lengths);rng=random.Random(73187)
# A larger irregular worn stone language on the free faces, preserving the exact family cut bands.
sites=[]
for row in range(10):
 for col in range(3):sites.append(((col+.5+.37*rng.uniform(-1,1))/3-.5,(row+.5+.30*rng.uniform(-1,1))/10*PER,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
capSites=[]
for row in range(4):
 for col in range(3):capSites.append(((col+.5+.29*rng.uniform(-1,1))/3-.5,(row+.5+.28*rng.uniform(-1,1))/4*1.15,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
def field(x,q,cap=False):
 near=[]
 for i,(sx,sy,c,sl,st) in enumerate(capSites if cap else sites):
  dx=x-sx;dy=q-sy
  if not cap:dy=(dy+PER/2)%PER-PER/2
  dx+=.025*math.sin(q*7.3+sx*2);dy+=.017*math.sin(2*math.pi*x+sy*3)
  near.append((dx*dx+dy*dy*.91,i,dx,dy))
 near.sort();a,b=near[:2];site=(capSites if cap else sites)[a[1]]
 gap=(b[0]-a[0])/(2*math.sqrt(max(b[0],1e-8)));worn=smooth(gap/.049)
 # Real worn shoulders and low crown facets, all inside the contact envelope.
 rel=min(-.001,-.069*(1-worn)+(.12*site[3]*a[2]+.10*site[4]*a[3]-.009)*worn)
 return rel,1-worn,site[2]
def color(z,cav,tone):
 h=smooth(z/1.15);low=(.14,.34,.59);mid=(.12,.47,.74);top=(.24,.67,.87)
 base=[mix(low[i],mid[i],smooth(h/.72)) for i in range(3)];base=[mix(base[i],top[i],smooth((h-.60)/.40)*.65) for i in range(3)]
 f=(1-.34*cav)*(1+.055*tone)
 return tuple(srgb(clamp(c*f)) for c in base)+(1,)
qs=[]
for e,n in enumerate([1,58,34,18,58,18,34,58]):
 for j in range(n):qs.append((e,j/n,starts[e]+lengths[e]*j/n))
NX=128;NQ=len(qs);assert len(side.data.vertices)==(NX+1)*NQ
ca=side.data.color_attributes['stone_albedo'];oldcol=[tuple(v.color) for v in ca.data]
for ix in range(NX+1):
 x=-.5+ix/NX;edgeDistance=.5-abs(x);blend=smooth((edgeDistance-.0625)/.15)
 for j,(e,t,q) in enumerate(qs):
  n=ix*NQ+j
  if blend==0 or e==0:continue
  ay,az=PROFILE[e];by,bz=PROFILE[(e+1)%8];y=mix(ay,by,t);z=mix(az,bz,t);dy,dz=by-ay,bz-az;le=math.hypot(dy,dz);ny,nz=dz/le,-dy/le
  rel,cav,tone=field(x,q);fade=math.sin(math.pi*(x+.5))**2
  v=Vector((x,y+ny*rel*fade,max(0,z+nz*rel*fade)))
  side.data.vertices[n].co=side.data.vertices[n].co.lerp(v,blend)
  c=color(v.z,cav*fade,tone);ca.data[n].color=tuple(mix(oldcol[n][i],c[i],blend) for i in range(4))
side.data.update();norms=[v.normal.copy() for v in side.data.vertices]
# Exact source custom-normal endpoint values, using actual native corner normals.
refNormals={}
for loop in referenceSide.loops:
 if loop.vertex_index not in refNormals:refNormals[loop.vertex_index]=referenceSide.corner_normals[loop.index].vector.copy()
for ix in [0,NX]:
 for j in range(NQ):norms[ix*NQ+j]=refNormals[ix*NQ+j]
side.data.normals_split_custom_set_from_vertices(norms)
# Preserve native INT16 custom-normal encoding in the unchanged connector strip. Re-encoding
# equal float vectors otherwise introduces a small avoidable quantization difference.
for loop in side.data.loops:
 ix=loop.vertex_index//NQ
 if ix<=7 or ix>=NX-7:side.data.attributes['custom_normal'].data[loop.index].value=referenceSide.attributes['custom_normal'].data[loop.index].value
side.data.update()
# Both end caps retain exact outline and boundary color. E end receives a broad irregular stepped course inside plane.
for k,cap in enumerate(caps):
 NY=100;NZ=110;ca=cap.data.color_attributes['stone_albedo'];old=[tuple(c.color) for c in ca.data];sign=-1 if k==0 else 1
 for iz in range(NZ+1):
  t=iz/NZ
  for iy in range(NY+1):
   n=iz*(NY+1)+iy;y=-.5+iy/NY;z=cap.data.vertices[n].co.z
   fade=math.sin(math.pi*iy/NY)**2*math.sin(math.pi*t)**2
   if fade<1e-12:continue
   rel,cav,tone=field(y,z,True)
   if k==1:
    course=.467+.033*math.sin(y*7.4)+.018*math.sin(y*17)
    crevice=(1-smooth(abs(z-course)/.040))*.040
    rel-=crevice;cav=max(cav,crevice/.04)
   cap.data.vertices[n].co.x=sign*(.5+min(0,rel)*fade)
   c=color(z,cav*fade,tone);blend=smooth(fade/.30);ca.data[n].color=tuple(mix(old[n][i],c[i],blend) for i in range(4))
 cap.data.update();cap.data.normals_split_custom_set_from_vertices([v.normal for v in cap.data.vertices])
# Complete the full-cell underside without changing the carved family side or custom-normal fan.
# The approved carved side's lowest +Y point retreats slightly; flush native quads close only
# that missing part of the Z=0 contact plane, with zero width at both locked cut planes.
cv=[];cc=[];cf=[];rings=[]
for ix in range(NX+1):
 n=ix*NQ+1;v=side.data.vertices[n].co;c=tuple(side.data.color_attributes['stone_albedo'].data[n].color)
 if ix in [0,NX]:
  a=len(cv);cv.append((v.x,.5,0));cc.append(c);rings.append((a,a))
 else:
  a=len(cv);cv.extend([(v.x,v.y,0),(v.x,.5,0)]);cc.extend([c,c]);rings.append((a,a+1))
for ix in range(NX):
 a,b=rings[ix];c,d=rings[ix+1];face=list(dict.fromkeys([a,b,d,c]));cf.append(face)
me=bpy.data.meshes.new('rock-wall-edge__full_cell_contact_completion');me.from_pydata(cv,[],cf);me.update();me.materials.append(side.data.materials[0]);ca=me.color_attributes.new(name='stone_albedo',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(cc):ca.data[i].color=c
contact=bpy.data.objects.new(me.name,me);coll.objects.link(contact);contact.parent=root
# Native family material, lighting, camera and sample configuration remain exact from approved project.
root.rotation_euler=(0,0,0);sc.render.resolution_x=768;sc.render.resolution_y=1408;bpy.context.view_layer.update()
cam=sc.camera
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
sc.render.filepath='';bpy.ops.wm.save_as_mainfile(filepath=str(B/'source/round-01.blend'),compress=True)
views={}
for d,z in DIR.items():
 root.rotation_euler.z=math.radians(z);bpy.context.view_layer.update();sc.render.filepath=str(O/f'native-static-{d}.png');bpy.ops.render.render(write_still=True)
 views[d]={'clip':'static','direction':d,'index':0,'actualRootMatrix':[list(v) for v in root.matrix_world],'rootPixel':px((0,0,0))}
root.rotation_euler.z=0;bpy.context.view_layer.update()
# Audit both exact shared side boundaries against native approved middle: positions, albedo and actual corner normals.
checks={}
for label,ix in [('W',0),('E',NX)]:
 idx=set(range(ix*NQ,(ix+1)*NQ));pd=cd=nd=0
 for n in idx:
  pd=max(pd,(side.data.vertices[n].co-referenceSide.vertices[n].co).length)
  cd=max(cd,max(abs(side.data.color_attributes['stone_albedo'].data[n].color[i]-referenceSide.color_attributes['stone_albedo'].data[n].color[i]) for i in range(4)))
 for l in side.data.loops:
  if l.vertex_index in idx:nd=max(nd,(side.data.corner_normals[l.index].vector-referenceSide.corner_normals[l.index].vector).length)
 checks[label]={'positionMax':pd,'albedoMax':cd,'actualCornerNormalMax':nd,'sampledBoundaryVertices':NQ}
allvs=[o.matrix_world@v.co for o in coll.objects if o.type=='MESH' for v in o.data.vertices]
audit={'asset':'rock-wall-edge','round':1,'sourceSHA256':json.loads((B/'brief.json').read_text())['source']['projectSHA256'],'approvedMiddleSHA256':sha(B/'inputs/approved-middle/project.blend'),'frozenBriefSHA256':sha(B/'brief.json'),'criteriaSHA256':sha(B/'reviews/proposedcriteria.json'),'scene':sc.name,'root':root.name,'collection':coll.name,'intrinsicRootMatrix':[list(v) for v in root.matrix_world],'views':views,'bounds':{'min':[min(v[i] for v in allvs) for i in range(3)],'max':[max(v[i] for v in allvs) for i in range(3)]},'nominalHeight':1.17,'fullCellGroundContact':{'x':[-.5,.5],'y':[-.5,.5],'z':0},'connectors':checks,'camera':{'worldMatrix':[list(v) for v in cam.matrix_world],'projectionMatrix':[list(v) for v in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'calibration':{'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in range(2)],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in range(2)],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in range(2)]}},'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'coordinateSHA256':hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in o.data.vertices)).hexdigest()} for o in coll.objects if o.type=='MESH'],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'shadow':o.data.use_shadow,'rotation':list(o.rotation_euler)} for o in sc.objects if o.type=='LIGHT'],'resourceClosure':{'images':[i.filepath for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]},'nativeGeometry':True,'paintedCard':False,'processing':'whole-frame BOX reduction from4 to2; no other pixel edits'}
(O/'native-audit.json').write_text(json.dumps(audit,indent=2))
# One connected mixed native stone surface. Middle(-1), candidate edge(0), middle(+1), exact shared rings welded.
ar=bpy.data.objects.new('mixed-connected__root',None);sc.collection.objects.link(ar)
vs=[];cs=[];fs=[];ns=[]
for ix in range(3*NX+1):
 module=min(2,ix//NX);si=ix-module*NX;me=side.data if module==1 else referenceSide
 if ix==3*NX:si=NX
 for j in range(NQ):
  n=si*NQ+j;v=me.vertices[n].co;vs.append((v.x+module-1,v.y,v.z));cs.append(tuple(me.color_attributes['stone_albedo'].data[n].color))
  ns.append((refNormals[n] if module!=1 else norms[n]).copy())
for ix in range(3*NX):
 for j in range(NQ):
  a=ix*NQ+j;b=ix*NQ+(j+1)%NQ;c=(ix+1)*NQ+(j+1)%NQ;d=(ix+1)*NQ+j;fs.append((a,b,c,d))
me=bpy.data.meshes.new('mixed-connected__welded');me.from_pydata(vs,[],fs);me.update();ca=me.color_attributes.new(name='stone_albedo',type='FLOAT_COLOR',domain='POINT')
for n,c in enumerate(cs):ca.data[n].color=c
for f in me.polygons:f.use_smooth=True
me.normals_split_custom_set_from_vertices(ns);me.materials.append(side.data.materials[0]);ob=bpy.data.objects.new(me.name,me);sc.collection.objects.link(ob);ob.parent=ar
assembly=[ob]
for k,x in [(0,-1),(1,1)]:
 cp=bpy.data.objects.new('mixed-connected__external-cap',referenceCaps[k]);sc.collection.objects.link(cp);cp.data.materials.clear();cp.data.materials.append(side.data.materials[0]);cp.parent=ar;cp.location.x=x;assembly.append(cp)
cp=bpy.data.objects.new('mixed-connected__edge_contact_completion',contact.data.copy());sc.collection.objects.link(cp);cp.parent=ar;assembly.append(cp)
coll.hide_render=True;sc.render.resolution_x=1792;sc.render.resolution_y=2432;cam.data.ortho_scale=3.5
for _ in range(2):
 base=px((0,0,0));prev=cam.data.shift_y;cam.data.shift_y=prev+1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-base[1];cam.data.shift_y=prev+(1536-base[1])/delta;bpy.context.view_layer.update()
for d,z in DIR.items():
 ar.rotation_euler.z=math.radians(z);bpy.context.view_layer.update();sc.render.filepath=str(O/f'connected-native-{d}.png');bpy.ops.render.render(write_still=True)
# Source stays a standalone editable asset; mixed reference is reproducible from this recipe and dependency.
for o in assembly+[ar]:bpy.data.objects.remove(o,do_unlink=True)
coll.hide_render=False;sc.render.resolution_x=768;sc.render.resolution_y=1408;cam.data.ortho_scale=1.5;cam.data.shift_y=audit['camera']['shift'][1];root.rotation_euler.z=0;sc.render.filepath='';bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(B/'source/round-01.blend'),compress=True)
settings={'asset':'rock-wall-edge','round':1,'base':'inputs/approved-middle/project.blend','modeling':'Native volumetric worn rock field, carved inward E-end strata, and flush full-cell underside completion; exact protected family boundary bands.','lockedProfile':PROFILE,'fieldSeed':73187,'nativeCaptureScale':4,'nativeFrame':[768,1408],'publishedScale':2,'publishedFrame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'publishedSampling':'Pillow BOX whole-canvas50%','frozenBriefSHA256':sha(B/'brief.json'),'criteriaSHA256':sha(B/'reviews/proposedcriteria.json'),'nativeAudit':'candidates/round-01/native-audit.json'}
(B/'source/round-01-settings.json').write_text(json.dumps(settings,indent=2));print('ROUND_DONE',str(O))
