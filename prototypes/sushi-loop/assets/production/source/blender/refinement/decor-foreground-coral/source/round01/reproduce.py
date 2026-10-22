"""Editable native coral: /opt/homebrew/bin/blender -b --python reproduce.py -- --build
Then render exact saved source: blender -b round-01.blend --python reproduce.py -- --capture
All geometry, normals, material color and sway are native. No raster art inputs.
"""
import bpy,sys,json,math,hashlib,argparse
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; OBJ=HERE.parent.parent
R=HERE/'resources'; C=OBJ/'candidates/round-01'; PROJECT=HERE/'round-01.blend'
DIRECTIONS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
ASSET='decor-foreground-coral'; ROOT_NAME='Coral ground root'; COLLECTION='Coral warm soft native'
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def color(h):return tuple(linear(int(h[i:i+2],16)/255) for i in (1,3,5))+(1,)
def mix(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def material(name,rough=.62,spec=.18,coat=.045):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');v=n.new('ShaderNodeVertexColor');v.layer_name='CoralColor';m.node_tree.links.new(v.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(v.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.045;p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.34;m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);return m

def mesh_object(name,verts,faces,colors,mat,col,root,smooth=True):
 me=bpy.data.meshes.new(name+' mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;me.materials.append(mat)
 attr=me.color_attributes.new(name='CoralColor',type='FLOAT_COLOR',domain='POINT')
 for i,c in enumerate(colors):attr.data[i].color=c
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=smooth
 return o

# Sparse pores are actual shallow mesh depressions, each with a smooth depth/color shoulder.
def tube(name,base,h,r,bend,purple,phase,col,root,mat,mini=False):
 n=64; steps=48 if not mini else 20; verts=[]; cols=[]; faces=[];z0=.105 if not mini else base[2]
 basex,basey=base[:2];body=color('#E94483' if not purple else '#8050D4');top=color('#FF6F9B' if not purple else '#A778EE');rim=color('#FF9D9A' if not purple else '#BE90F5');inside=color('#A32058' if not purple else '#46228F');deep=color('#761944' if not purple else '#321C70')
 pores=[] if mini else [(a%(2*math.pi),zz,ww,hh) for a,zz,ww,hh in [(phase+.2,.33,.25,.075),(phase+2.1,.56,.22,.09),(phase+4.2,.73,.25,.06),(phase+3.5,.26,.17,.05),(phase+5.8,.49,.17,.055),(phase+1.2,.84,.16,.045)]]
 def center(t):return (basex+bend[0]*(t*t*(3-2*t)),basey+bend[1]*(t*t*(3-2*t)))
 def rad(t):return r*(.63+.37*math.sin(min(1,t)*math.pi/2))*(1+.10*math.sin(t*math.pi))
 def ring(z,t,rr,co,outer=False):
  cx,cy=center(t)
  for j in range(n):
   a=2*math.pi*j/n;irreg=1+.016*math.cos(3*a+phase)+.009*math.cos(5*a-phase);rrr=rr*irreg;dep=0
   if outer:
    for pa,pz,pw,ph in pores:
     da=math.atan2(math.sin(a-pa),math.cos(a-pa));dd=(da/pw)**2+((t-pz)/ph)**2
     if dd<1:dep=max(dep,(.5+.5*math.cos(math.pi*math.sqrt(dd)))**1.15)
    rrr-=r*.12*dep
   verts.append((cx+rrr*math.cos(a),cy+rrr*math.sin(a),z));cols.append(mix(co,inside,.44*dep))
 for k in range(steps+1):
  t=k/steps;ring(z0+(h-z0-.027)*t,t,rad(t),mix(body,top,.25+.65*t),True)
 # rolled half-circle outer lip to inner lip: substantial geometry rather than shader bevel
 thick=r*.25;mid=r-thick/2
 for k in range(1,13):
  a=math.pi*k/12;ring(h-.027+math.sin(a)*.027,1,mid+math.cos(a)*thick/2,mix(top,rim,math.sin(a)**.75*.88))
 depth=min(.34,(h-z0)*.54)
 for k in range(1,17):
  t=k/16;z=h-.027-depth*t;bt=max(0,(z-z0)/(h-z0-.027));ring(z,bt,(rad(bt)-thick)*(1-.12*t),mix(inside,deep,t*.72))
 # Curved cavity floor transitions to center with no plug face at the mouth.
 for k in range(1,9):
  t=k/9;z=h-.027-depth-.025*math.sin(t*math.pi/2);bt=max(0,(z-z0)/(h-z0-.027));ring(z,bt,(rad(bt)-thick)*.88*math.cos(t*math.pi/2),mix(inside,deep,.72+.28*t))
 rings=len(verts)//n
 for k in range(rings-1):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 faces.append(tuple(reversed(range(n))));faces.append(tuple((rings-1)*n+j for j in range(n)))
 o=mesh_object(name,verts,faces,cols,mat,col,root)
 o['role']='coral-tube' if not mini else 'button-coral';o['baseCenter']=[basex,basey,z0];o['baseRingVertexCount']=n;o['swayPhase']=phase
 if not mini:
  o.shape_key_add(name='Basis');sx=o.shape_key_add(name='Rooted sway X');sy=o.shape_key_add(name='Rooted sway Y');sx.slider_min=-1;sy.slider_min=-1
  for i,v in enumerate(o.data.vertices):
   w=max(0,min(1,(v.co.z-.22)/(h-.22)))**1.65
   sx.data[i].co.x+=.014*w;sy.data[i].co.y+=.009*w
  keys=o.data.shape_keys
  for frame in range(1,14):
   a=2*math.pi*((frame-1)%12)/12
   sx.value=math.sin(a+phase);sy.value=.8*math.sin(a+phase+.7)
   sx.keyframe_insert(data_path='value',frame=frame);sy.keyframe_insert(data_path='value',frame=frame)
  action=keys.animation_data.action;action.name='CORAL_NATIVE__idle__'+name;action.use_fake_user=True;o['idleAction']=action.name
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for p in fc.keyframe_points:p.interpolation='LINEAR'
  keys.animation_data_clear();sx.value=0;sy.value=0
 return o

def rock(name,x,y,rx,ry,h,phase,col,root,mat):
 n=10;verts=[];cols=[];faces=[];base=color('#164B82');edge=color('#2775AC');top=color('#388BBC')
 for k,(z,r) in enumerate([(0,.84),(.025,.99),(h-.032,1),(h,.84)]):
  for j in range(n):
   a=j*2*math.pi/n;ir=1+.035*math.sin(a*3+phase);verts.append((x+math.cos(a)*rx*r*ir,y+math.sin(a)*ry*r*ir,z));cols.append(mix(base,top,k/3*.75+.07*math.sin(a*2+phase)))
 for k in range(3):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 faces.append(tuple(reversed(range(n))));faces.append(tuple(3*n+j for j in range(n)))
 o=mesh_object(name,verts,faces,cols,mat,col,root,False);be=o.modifiers.new('Soft rock edges','BEVEL');be.width=.018;be.segments=3
 no=o.modifiers.new('Stable broad rock normals','WEIGHTED_NORMAL');no.keep_sharp=True;no.weight=40;o['role']='rock';return o

def frond(name,x,y,z,angle,h,width,bend,col,root,mat):
 verts=[];cols=[];faces=[];n=12;steps=12
 for k in range(steps+1):
  t=k/steps;rr=max(.006,width*math.sin(math.pi*(.12+.88*t))**.65);cx=x+math.cos(angle)*bend*t*t;cy=y+math.sin(angle)*bend*t*t
  for j in range(n):
   a=j*2*math.pi/n;verts.append((cx+math.cos(a)*rr,cy+math.sin(a)*rr*.5,z+h*t));cols.append(mix(color('#39994F'),color('#94CF59'),t*.65+.13*math.cos(a)))
 for k in range(steps):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 faces.extend([tuple(reversed(range(n))),tuple(steps*n+j for j in range(n))]);o=mesh_object(name,verts,faces,cols,mat,col,root);o['role']='rooted-frond';return o

def camera_record(sc):
 cam=sc.camera
 def px(v):p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 p=px((0,0,0))
 return {'projection':'top-down-oblique-square-grid','frame':[192,384],'anchor':[96,288],'cellSize':128,'captureScale':4,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1536,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134},'calibration':{'root':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p)}}

def build():
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name='Coral warm soft native capture';sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.cycles.device='CPU';sc.render.resolution_x=768;sc.render.resolution_y=1536;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;sc.render.fps=12;sc.frame_start=1;sc.frame_end=12;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=60;sc.render.dither_intensity=0;sc.render.filter_size=1.5;sc.eevee.taa_render_samples=64;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.use_nodes=False
 world=bpy.data.worlds.new('Neutral soft ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28;sc.world=world
 col=bpy.data.collections.new(COLLECTION);sc.collection.children.link(col);root=bpy.data.objects.new(ROOT_NAME,None);col.objects.link(root);root['assetId']=ASSET;root['groundRoot']=True
 mat=material('Coral satin organic');stone=material('Cobalt soft stone',.75,.18,.035);green=material('Frond matte',.7,.2,.05)
 rock('Central rooted reef',0,0,.35,.35,.20,.5,col,root,stone)
 for name,x,y,rx,ry,h,ph in [('Front left rock',-.22,-.23,.27,.26,.19,.2),('Front right rock',.22,-.23,.27,.26,.175,1.2),('Back left rock',-.23,.23,.26,.26,.185,2.3),('Back right rock',.23,.23,.26,.26,.18,3.4)]:rock(name,x,y,rx,ry,h,ph,col,root,stone)
 specs=[('Central pink',(.0,.17),1.35,.135,(.015,.05),False,.1),('Left pink',(-.22,.04),1.13,.13,(-.065,.035),False,1.1),('Right pink',(.22,.04),1.07,.127,(.07,.025),False,2.3),('Front left pink',(-.21,-.23),.77,.118,(-.035,-.055),False,3.3),('Front right pink',(.21,-.23),.84,.12,(.035,-.045),False,4.2),('Front violet',(.0,-.28),.64,.105,(.005,-.055),True,5.0),('Rear violet',(-.15,.30),.98,.095,(-.025,.03),True,5.9)]
 for n,b,h,r,be,p,ph in specs:tube(n,b,h,r,be,p,ph,col,root,mat)
 for i,(x,y,ang) in enumerate([(-.36,-.30,3.8),(.36,-.30,-.4),(.31,.30,.7),(-.30,.31,2.4)]):
  for j in range(3):frond(f'Reef frond {i}-{j}',x,y,.145,ang+(j-1)*.65,.17+(j%2)*.09,.027 if j!=1 else .035,.045,col,root,green)
 for i,(x,y) in enumerate([(-.12,-.405),(.11,-.41),(.39,.16),(-.39,.16)]):tube(f'Violet button {i}',(x,y,.13),.22,.044,(0,0),True,i*1.8,col,root,mat,True)
 cam=bpy.data.objects.new('Registered 55 degree camera',bpy.data.cameras.new('Registered camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.matrix_world=Matrix(json.loads((R/'source-camera.json').read_text())['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def py():p=world_to_camera_view(sc,cam,Vector((0,0,0)));return (1-p.y)*1536
 base=py();cam.data.shift_y=1;bpy.context.view_layer.update();dy=py()-base;cam.data.shift_y=(1152-base)/dy;bpy.context.view_layer.update()
 def area(name,pos,power,size):
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;ob=bpy.data.objects.new(name,data);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.45))-ob.location).to_track_quat('-Z','Y').to_euler()
 area('Symmetric overhead',(0,0,4.5),120,4)
 for i in range(4):a=i*math.pi/2;area('Equal cardinal soft fill '+str(i),(3*math.cos(a),3*math.sin(a),2),45,4)
 sc['recipe']='source/round01/reproduce.py';sc['lighting']='Centered120W4mdisk+4equal45W4mdisks radius3 z2; neutralworld.28. No ground plane.';sc['publication']='Wholeframe LANCZOS4x to2x, unmodified RGBA.'
 apply_clip('static','S',1);bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT),compress=True)
 write(C/'native-camera.json',camera_record(sc));print('SAVED',PROJECT)

def apply_clip(clip,direction,frame):
 sc=bpy.context.scene;root=bpy.data.objects[ROOT_NAME];root.rotation_euler.z=DIRECTIONS[direction]
 for o in bpy.data.collections[COLLECTION].all_objects:
  if not o.get('idleAction'):continue
  keys=o.data.shape_keys
  if clip=='idle':
   keys.animation_data_create();a=bpy.data.actions[o['idleAction']];keys.animation_data.action=a;keys.animation_data.action_slot=a.slots[0]
  else:
   keys.animation_data_clear()
   for k in keys.key_blocks[1:]:k.value=0
 sc.frame_set(frame);bpy.context.view_layer.update()

def evaluated():
 dg=bpy.context.evaluated_depsgraph_get();ret={}
 for o in bpy.data.collections[COLLECTION].all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);me=e.to_mesh();ret[o.name]=[tuple(e.matrix_world@v.co) for v in me.vertices];e.to_mesh_clear()
 return ret

def bounds(points):return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
def capture(quick=False,measure=False):
 sc=bpy.context.scene;records=[];georecs=[];closures=[];source=sha(PROJECT);camrec=camera_record(sc);write(C/'native-camera.json',camrec)
 # Full swept mesh and native ray contact proof is measured from the saved candidate.
 from mathutils.bvhtree import BVHTree
 rocks=[o for o in bpy.data.collections[COLLECTION].all_objects if o.get('role')=='rock']
 for d in DIRECTIONS:
  for clip,count in [('static',1),('idle',13)]:
   first=None
   for f in range(1,count+1):
    apply_clip(clip,d,f);ev=evaluated();points=[p for ps in ev.values() for p in ps];measured=bounds(points)
    if f==1:first=ev
    delta=max((Vector(p)-Vector(q)).length for n in ev for p,q in zip(ev[n],first[n]))
    # actual ray probes at all 64 outer basal-ring vertices on every animated tube
    dg=bpy.context.evaluated_depsgraph_get();trees=[(o,BVHTree.FromObject(o,dg)) for o in rocks];contact=[]
    for o in bpy.data.collections[COLLECTION].all_objects:
     if o.get('role')!='coral-tube':continue
     basal=ev[o.name][:64];hits=[]
     for p in basal:
      top=None
      for ro,tree in trees:
       origin=ro.matrix_world.inverted()@Vector((p[0],p[1],.6));hit=tree.ray_cast(origin,ro.matrix_world.inverted().to_3x3()@Vector((0,0,-1)),1)
       if hit[0] is not None:
        z=(ro.matrix_world@hit[0]).z
        if top is None or z>top:top=z
      hits.append({'z':p[2],'rockSurfaceZ':top,'embedded':top is not None and p[2]<=top+1e-5 and p[2]>=0})
     contact.append({'tube':o.name,'probes':len(hits),'embedded':all(h['embedded'] for h in hits),'minimumEmbedDepth':min((h['rockSurfaceZ']-h['z'] for h in hits if h['rockSurfaceZ'] is not None),default=None),'probeEvidence':hits})
    root=bpy.data.objects[ROOT_NAME];record={'clip':clip,'direction':d,'frame':f,'index':f-1,'bounds':measured,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'maxVertexDeltaFromFirst':delta,'allTubeBasesEmbedded':all(c['embedded'] for c in contact),'contacts':contact,'objects':[{'name':n,'bounds':bounds(ps)} for n,ps in ev.items()]};georecs.append(record)
    if f==13:closures.append({'direction':d,'frame1vs13MaxVertexDelta':delta})
    if measure or (quick and (clip!='static')):continue
    path=C/'native'/clip/d/f'{f-1:03}.png';path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    records.append({**{k:record[k] for k in ['clip','direction','frame','index','bounds','rootRotationZ','rootRotationDegrees','rootMatrix','allTubeBasesEmbedded']},'path':str(path.relative_to(OBJ)),'sourceSHA256':source,'camera':camrec,'filterSize':sc.render.filter_size,'samples':sc.cycles.samples})
 if not quick:
  # Static geometry hold through frame13, sampled with genuine native evaluation.
  holds=[]
  for d in DIRECTIONS:
   apply_clip('static',d,1);first=evaluated();apply_clip('static',d,13);last=evaluated();holds.append({'direction':d,'frame1vs13MaxVertexDelta':max((Vector(p)-Vector(q)).length for n in first for p,q in zip(first[n],last[n]))})
  write(C/'native-validation.json',{'asset':ASSET,'sourceSHA256':source,'blender':bpy.app.version_string,'captureRecords':records,'geometryMeasurements':georecs,'closure':closures,'staticHolds':holds,'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size,'type':o.data.type} for o in sc.objects if o.type=='LIGHT'],'nativeScene':{'collection':COLLECTION,'root':ROOT_NAME,'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'role':o.get('role'),'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'faces':len(o.data.polygons) if o.type=='MESH' else 0,'shapeKeys':[k.name for k in o.data.shape_keys.key_blocks] if o.type=='MESH' and o.data.shape_keys else [],'idleAction':o.get('idleAction')} for o in bpy.data.collections[COLLECTION].all_objects]},'externalLibraries':[l.filepath for l in bpy.data.libraries],'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'groundPlaneObjects':[],'camera':camrec,'filter':'native1.5;32Cycles samples with native denoising; completeframe LANCZOS4xto2x; no pixel edits','notes':'Native4x captures include frame13 closure for all4 facings. Static geometry sampled through frame13. Measured records reflect actual evaluated geometry while rendering exact saved blend.'})
 print('CAPTURED',len(records))

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if '--build' in args:build()
 if '--capture' in args or '--quick' in args or '--measure' in args:capture('--quick' in args,'--measure' in args)
