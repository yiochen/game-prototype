"""Reef corner native authoring. Blender --background --python this-file.
Builds private native geometry from the hash-locked canonical middle, copies its
full uncut terminal triangles, retains its camera/light/material field, and
renders direct native2x PNGs. No image edits, fitting or pixel repairs.
"""
import sys
sys.dont_write_bytecode=True
import bpy,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import delaunay_2d_cdt,tessellate_polygon
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent
OUT=OBJ/'candidates/round-01'
PROFILE=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)]
TOP=[(-.38,.2),(-.30,.4),(-.14,.35),(.08,.44),(.25,.4),(.38,.2)]
GROUND=[(-.38,.38),(-.5,.38),(-.5,-.38),(-.25,-.38),(.26870057,-.26870057),(.38,.25),(.38,.5),(-.38,.5)]
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def inside(p,poly):
    x,y=p;v=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:v=not v
    return v
def profile(w):
    for a,b in zip(TOP,TOP[1:]):
        if w<=b[0]+1e-9:return a[1]+(b[1]-a[1])*(w-a[0])/(b[0]-a[0])
    return .2
def height(x,y):
    a=profile(max(-.38,min(.38,y)));b=profile(max(-.38,min(.38,-x)))
    dW=max(0,x+.42);dN=max(0,.42-y)
    fW=1-smooth(dW/.15);fN=1-smooth(dN/.15)
    if dW<1e-8:return a
    if dN<1e-8:return b
    wW=fW/max(1e-8,1-fW);wN=fN/max(1e-8,1-fN)
    h=(max(a,b)+wW*a+wN*b)/(1+wW+wN)
    h+=.024*math.exp(-((x+.03)/.23)**2-((y-.08)/.24)**2)*(1-fW)*(1-fN)
    return h
def mesh(name,vs,fs,mats,indices=None,smoothness=False):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=ROOT
    for m in mats:me.materials.append(m)
    for p in me.polygons:p.use_smooth=smoothness;p.material_index=indices[p.index] if indices else 0
    return o
def camera(frame=(192,352),anchor=(96,248)):
    sc=SC;cam=sc.camera;sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
    el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
    b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(anchor[1]*2-b.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update();root=px((0,0,0))
    return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'orthoScale':cam.data.ortho_scale,'elevationDegrees':math.degrees(el),'worldUnitsPerCell':1},'calibration':{'root':list(root),'unitX':list(px((1,0,0))-root),'unitDepth':list(px((0,-1,0))-root),'unitHeight':list(px((0,0,1))-root)},'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filterSize':sc.render.filter_size,'publication':'Exact native PNG bytes; no reduction'}
def tube(name,base,height,radius,lean,m,pad,inner):
    count=24;v=[];rings=[(0,.76),(height*.45,.88),(height-.018,1),(height-.005,1.02),(height,.88),(height-.009,.67),(height-.038,.62),(.037,.48)]
    for z,s in rings:
        frac=z/height;cx=base[0]+lean[0]*frac*frac;cy=base[1]+lean[1]*frac*frac
        for i in range(count):
            a=2*math.pi*i/count;organic=1+.027*math.sin(3*a+.6);v.append((cx+radius*s*math.cos(a)*organic,cy+radius*s*math.sin(a)*organic,base[2]+z))
    f=[];idx=[]
    for k in range(len(rings)-1):
        for i in range(count):f.append((k*count+i,k*count+(i+1)%count,(k+1)*count+(i+1)%count,(k+1)*count+i));idx.append(0 if k<2 else 1 if k<5 else 2)
    f.append(tuple(reversed(range((len(rings)-1)*count,len(rings)*count))));idx.append(2)
    return mesh(name,v,f,[m,pad,inner],idx,True)
def rock(name,loc,size,angle,material=None):
    ring=[(-.45,-.29),(-.16,-.5),(.33,-.44),(.5,-.12),(.44,.35),(.10,.5),(-.34,.43),(-.5,.12)];v=[]
    for z,r in [(-.5,.72),(-.18,1),(.26,.91),(.49,.55)]:
        for i,(x,y) in enumerate(ring):v.append((x*size[0]*r,y*size[1]*r,(z+.035*math.sin(i*2))*size[2]))
    f=[tuple(reversed(range(8))),tuple(range(24,32))];idx=[0,1]
    for k in range(3):
        for i in range(8):f.append((k*8+i,k*8+(i+1)%8,(k+1)*8+(i+1)%8,(k+1)*8+i));idx.append(1 if k==2 else 0)
    o=mesh(name,v,f,[material or M['selected boulder blue'],material or M['selected boulder lit planes']],idx,True);o.location=loc;o.rotation_euler.z=angle
    be=o.modifiers.new('soft stone shoulders','BEVEL');be.width=.012;be.segments=3;be.profile=.65
    no=o.modifiers.new('weighted stone planes','WEIGHTED_NORMAL');no.keep_sharp=True;no.weight=28
    return o
def build():
    global SC,COL,ROOT,M,FIELD
    source=BASE/'resources/canonical-middle.blend';assert digest(source)=='51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5'
    bpy.ops.wm.open_mainfile(filepath=str(source));SC=bpy.context.scene;COL=bpy.data.collections['reef-middle'];ROOT=bpy.data.objects['reef-middle__root'];ROOT.rotation_euler.z=0;ROOT.location=(0,0,0)
    core=bpy.data.objects['reef-middle__continuous_core'];cm=core.data;cm.calc_loop_triangles();M={m.name:m for m in bpy.data.materials}
    bands=[]
    for side in ['W','N']:
        rot=Matrix.Rotation(0 if side=='W' else math.pi/2,3,'Z')
        for t in cm.loop_triangles:
            ps=[cm.vertices[i].co.copy() for i in t.vertices]
            valid=all(-.500001<=p.x<=-.419999 for p in ps) if side=='W' else all(.419999<=p.x<=.500001 for p in ps)
            if valid and max(p.x for p in ps)-min(p.x for p in ps)>1e-7:
                bands.append({'side':side,'vs':[list(rot@p) for p in ps],'ns':[list(rot@cm.corner_normals[i].vector) for i in t.loops],'material':t.material_index,'canonicalTriangle':t.index})
    FIELD={'canonicalSHA256':digest(source),'adoptedFullUncutTriangles':bands}
    for o in list(COL.objects):
        if o!=ROOT:bpy.data.objects.remove(o,do_unlink=True)
    ROOT.name='reef-corner__root';COL.name='reef-corner';SC.name='reef-corner native round01'
    vs=[];fs=[];mi=[];normals=[];lookup={}
    def vertex(p):
        key=tuple(round(float(x),7) for x in p)
        if key not in lookup:lookup[key]=len(vs);vs.append(tuple(p))
        return lookup[key]
    def face(ps,mat=0,ns=None):fs.append(tuple(vertex(p) for p in ps));mi.append(mat);normals.append(ns)
    for b in bands:face(b['vs'],b['material'],b['ns'])
    # Central heightfield spans the finite polygon, with straight canonical
    # terminal continuation. 2D constrained triangulation makes a single clean
    # top; the bottom is one consistently oriented finite polygon, no folds.
    border=[(-.42,y) for y,z in reversed(TOP)]+[(-.25,-.38),(.26870057,-.26870057),(.38,.25)]+[(-y,.42) for y,z in TOP]+[(-.38,.38)]
    points=list(border)
    for ix in range(20):
        for iy in range(20):
            p=(-.40+ix*.04,-.36+iy*.04)
            if inside(p,border) and min(math.hypot(p[0]-q[0],p[1]-q[1]) for q in border)>.009:points.append(p)
    xy,ed,tri,*_=delaunay_2d_cdt([Vector(p) for p in points],[],[list(range(len(border)))],1,1e-8)
    for t in tri:
        ps=[(xy[i].x,xy[i].y,height(xy[i].x,xy[i].y)) for i in t]
        face(ps,1)
    # Outer sides only; exact original base exterior is retained.
    cground=[(-.42,.38),(-.42,-.38),(-.25,-.38),(.26870057,-.26870057),(.38,.25),(.38,.42),(-.38,.42),(-.38,.38)]
    for a,b in zip(cground,cground[1:]+cground[:1]):
        if abs(a[0]+.42)<1e-7 and abs(b[0]+.42)<1e-7:continue
        if abs(a[1]-.42)<1e-7 and abs(b[1]-.42)<1e-7:continue
        face([(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],height(*b)),(a[0],a[1],height(*a))],0)
    # Full original finite ground, including terminal collar bottoms already
    # present, uses a central finite polygon with downward winding.
    ground_vectors=[Vector((x,y,0)) for x,y in cground]
    for t in tessellate_polygon([ground_vectors]):face([list(ground_vectors[p]) if isinstance(p,int) else list(p) for p in reversed(t)],0)
    # Port caps are exact unmodified section geometry; no overlap or growth.
    face([(-.5,y,z) for y,z in reversed(PROFILE)],0)
    face([(-y,.5,z) for y,z in PROFILE],0)
    o=mesh('reef-corner__continuous_core',vs,fs,[M['reef blue stone'],M['reef cyan stone planes']],mi,False)
    # Canonical collar faces keep their native flat field without a quantized
    # custom-normal layer. Only central top faces use native smooth shading.
    for p,n in zip(o.data.polygons,normals):
        p.use_smooth=(n is None and p.material_index==1)
    o['canonicalCollarTriangles']=len(bands);o['finiteGroundExterior']=json.dumps(GROUND)
    rock('reef-corner__rear_shoulder',(-.10,.205,.397),(.32,.27,.20),-.12)
    rock('reef-corner__outer_stone',(.18,.02,.360),(.28,.29,.23),.22)
    rock('reef-corner__front_terrace',(-.085,-.215,.361),(.44,.26,.17),.12)
    rock('reef-corner__inner_shoulder',(-.29,.23,.370),(.19,.23,.15),-.20)
    t=M['teal tube coral'];tl=M['teal rounded rim'];ti=M['teal inner wall'];p=M['purple tube coral'];pl=M['purple rounded rim'];pi=M['purple inner wall']
    tube('reef-corner__teal_focal',(-.075,.18,.422),.25,.070,(.006,.008),t,tl,ti)
    tube('reef-corner__teal_left',(-.15,.17,.414),.171,.047,(-.044,.012),t,tl,ti)
    tube('reef-corner__teal_right',(.02,.18,.410),.195,.052,(.047,.018),t,tl,ti)
    tube('reef-corner__teal_front',(-.065,.08,.412),.123,.043,(.023,-.026),t,tl,ti)
    for label,x,y,z in [('front',-.22,-.23,.345),('outer',.22,-.10,.337)]:
        tube('reef-corner__purple_'+label,(x,y,z),.230,.056,(.006,-.006),p,pl,pi)
        bud=(x+.061,y+.015,z-.01) if label=='front' else (x+.040,y+.053,z-.01)
        tube('reef-corner__purple_'+label+'_bud',bud,.146,.034,(.018,.01) if label=='front' else (.002,.016),p,pl,pi)
        tube('reef-corner__purple_'+label+'_branch',(x-.054,y-.018,z-.01),.160,.036,(-.018,-.015),p,pl,pi)
    pink=M['purple rounded rim'].copy();pink.name='reef pink low accent';bs=next(n for n in pink.node_tree.nodes if n.type=='BSDF_PRINCIPLED');
    # Use a deliberate small pink accent with native volume and a private ramp.
    ramp=next(n for n in pink.node_tree.nodes if n.type=='VALTORGB')
    for e in ramp.color_ramp.elements:e.color=(.65*(.7+e.position*.6),.055,.19,1)
    rock('reef-corner__pink_front_accent',(.095,-.235,.409),(.15,.12,.09),-.18,pink)
    for i,(x,y,z,s) in enumerate([(-.12,-.20,.405,.046),(.12,-.12,.408,.04),(.19,.20,.367,.044),(-.27,.03,.389,.031),(.05,-.29,.325,.029)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z));ob=bpy.context.object
        for c in list(ob.users_collection):c.objects.unlink(ob)
        COL.objects.link(ob);ob.name='reef-corner__teal_pebble_'+str(i);ob.parent=ROOT;ob.scale=(s,s*.83,s*.57);ob.data.materials.append(t)
        for f in ob.data.polygons:f.use_smooth=True
    # Remove orphan native geometry and unused data without changing rig/material.
    for data in list(bpy.data.meshes):
        if data.users==0:bpy.data.meshes.remove(data)
    SC.render.filter_size=.01;SC.eevee.taa_render_samples=64;SC.render.dither_intensity=0;SC.frame_start=1;SC.frame_end=1;SC.frame_set(1);camera()
    write(OUT/'collar-construction.json',FIELD)
def geometry_audit():
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();parts=[];allp=[]
    for o in COL.objects:
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();ps=[ROOT.matrix_world.inverted()@o.matrix_world@v.co for v in me.vertices];allp.extend(ps)
        parts.append({'name':o.name,'vertices':len(me.vertices),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'bounds':[[min(p[a] for p in ps) for a in range(3)],[max(p[a] for p in ps) for a in range(3)]],'materials':[m.name for m in me.materials],'privateMeshUsers':o.data.users});e.to_mesh_clear()
    return {'blender':bpy.app.version_string,'parts':parts,'bounds':[[min(p[a] for p in allp) for a in range(3)],[max(p[a] for p in allp) for a in range(3)]],'groundExterior':GROUND,'groundArea':abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(GROUND,GROUND[1:]+GROUND[:1])))/2,'linkedLibraries':[l.filepath for l in bpy.data.libraries],'images':[i.name for i in bpy.data.images],'root':ROOT.name,'rootMatrix':[list(r) for r in ROOT.matrix_world],'lighting':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape} for o in SC.objects if o.type=='LIGHT'],'worldStrength':SC.world.node_tree.nodes.get('Background').inputs['Strength'].default_value,'render':{'engine':SC.render.engine,'samples':SC.eevee.taa_render_samples,'filterSize':SC.render.filter_size,'viewTransform':SC.view_settings.view_transform,'look':SC.view_settings.look,'exposure':SC.view_settings.exposure,'gamma':SC.view_settings.gamma,'dither':SC.render.dither_intensity}}
def render(p):p.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(p);bpy.ops.render.render(write_still=True)
if '--out' in sys.argv:OUT=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
if OUT.exists() and any(OUT.iterdir()):raise FileExistsError('Immutable output exists')
OUT.mkdir(parents=True,exist_ok=True)
if '--replay' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-01.blend'));SC=bpy.context.scene;COL=bpy.data.collections['reef-corner'];ROOT=bpy.data.objects['reef-corner__root']
else:
    if (BASE/'round-01.blend').exists():raise FileExistsError('Immutable source exists')
    build();ROOT.rotation_euler.z=0;camera();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'round-01.blend'),compress=True)
ROOT.rotation_euler.z=0;bpy.context.view_layer.update();write(OUT/'geometry-audit.json',geometry_audit())
log={'sourceProject':'source/round-01.blend','sourceSHA256':digest(BASE/'round-01.blend'),'captureRecords':[],'nativeAssemblies':[]}
for d,a in ANGLES.items():
    ROOT.rotation_euler.z=a;bpy.context.view_layer.update();rec=camera();p=OUT/f'native/static/{d}/000.png';render(p)
    for sub in ([] if '--replay' in sys.argv else [f'frames/static/{d}/000.png',f'atlases/static-{d}.png']):
        dest=OUT/sub;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    log['captureRecords'].append({'direction':d,'clip':'static','frame':1,'index':0,'rootRotationZ':ROOT.rotation_euler.z,'actualRootMatrix':[list(r) for r in ROOT.matrix_world],'camera':rec,'path':str(p.relative_to(OBJ)),'sha256':digest(p)})
    if d=='S':write(OUT/'published-camera.json',rec)
# Append private exact canonical objects for hard two-port native fixture.
with bpy.data.libraries.load(str(BASE/'resources/canonical-middle.blend'),link=False) as (fr,to):to.collections=['reef-middle']
middle=to.collections[0];SC.collection.children.link(middle);mr=next(o for o in middle.objects if o.type=='EMPTY');mr.rotation_euler.z=0;mr.location=(0,0,0)
other=bpy.data.collections.new('outgoing canonical middle');SC.collection.children.link(other);mapping={}
for o in middle.objects:
    n=o.copy();n.data=o.data.copy() if o.data else None;other.objects.link(n);mapping[o]=n
for o,n in mapping.items():
    if o.parent in mapping:n.parent=mapping[o.parent]
nr=mapping[mr]
for d,a in ANGLES.items():
    ROOT.rotation_euler.z=a;mr.rotation_euler.z=a;mr.location=(-math.cos(a),-math.sin(a),0);nr.rotation_euler.z=a+math.pi/2;nr.location=(-math.sin(a),math.cos(a),0);bpy.context.view_layer.update();rec=camera((448,608),(224,376));p=OUT/f'native/two-port-{d}.png';render(p)
    log['nativeAssemblies'].append({'direction':d,'rootRotationZ':ROOT.rotation_euler.z,'rootMatrix':[list(r) for r in ROOT.matrix_world],'incomingMatrix':[list(r) for r in mr.matrix_world],'outgoingMatrix':[list(r) for r in nr.matrix_world],'camera':rec,'path':str(p.relative_to(OBJ)),'sha256':digest(p)})
# Render independently registered exact canonical single facings, same camera/rig.
for o in list(COL.objects)+list(other.objects):o.hide_render=True
mr.location=(0,0,0)
for d,a in ANGLES.items():
    mr.rotation_euler.z=a;bpy.context.view_layer.update();camera();render(OUT/f'canonical/static-{d}.png')
write(OUT/'capture-measurements.json',log)
print('REEF_CORNER_ROUND01_COMPLETE',flush=True)
