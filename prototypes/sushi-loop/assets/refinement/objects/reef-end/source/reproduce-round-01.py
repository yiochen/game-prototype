"""Portable reef-end native construction/capture, background Blender only.

Canonical W collar triangles and materials are adopted literally; everything
past the collar is native reef-end geometry. Camera calibration follows the
registered square-grid projection. No raster fitting, repair, or art processing.
Run Blender --background --python this.py [-- --explore ID | --replay --out DIR].
"""
import sys
sys.dont_write_bytecode = True
import bpy, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

B=Path(__file__).resolve().parent; O=B.parent; RES=B/'resources'
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
PROFILE=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)]
OUT=O/'candidates/round-01'; PROJECT=B/'round-01.blend'
if '--explore' in sys.argv:
    tag=sys.argv[sys.argv.index('--explore')+1]
    OUT=O/'candidates/explorations'/tag; PROJECT=B/'explorations'/f'{tag}.blend'
if '--out' in sys.argv: OUT=Path(sys.argv[sys.argv.index('--out')+1]).resolve()

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def update(): bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
def smooth(t): t=max(0,min(1,t));return t*t*(3-2*t)
def plain(v):
    if isinstance(v,(int,float,str,bool)) or v is None:return v
    try:return [plain(x) for x in v]
    except TypeError:return str(v)
def graph(tree):
    nodes=[]
    for n in tree.nodes:
        rec={'name':n.name,'type':n.type,'inputs':[{'name':i.name,'identifier':i.identifier,'value':plain(i.default_value)} for i in n.inputs if hasattr(i,'default_value')]}
        for k in ['operation','blend_type']:
            if hasattr(n,k):rec[k]=getattr(n,k)
        if hasattr(n,'color_ramp'):rec['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[[e.position,list(e.color)] for e in n.color_ramp.elements]}
        nodes.append(rec)
    return {'nodes':nodes,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links]}

def camera(frame=(192,352),anchor=(96,248)):
    sc=SC;cam=sc.camera
    sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
    cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
    el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.shift_x=0;cam.data.shift_y=0;update()
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
    base=px((0,0,0));cam.data.shift_y=1;update();dy=px((0,0,0)).y-base.y
    cam.data.shift_y=(anchor[1]*2-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];update();root=px((0,0,0))
    return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':2,'fps':12,
        'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'orthoScale':cam.data.ortho_scale,'elevationDegrees':math.degrees(el),'worldUnitsPerCell':1},
        'calibration':{'root':list(root),'unitX':list(px((1,0,0))-root),'unitDepth':list(px((0,-1,0))-root),'unitHeight':list(px((0,0,1))-root)},
        'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filterSize':sc.render.filter_size,'publication':'Exact direct-native2x PNG bytes; no reduction'}

def mesh(name,vs,fs,mats,mi=None,smoothness=False):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('reef-end__'+name,me);COL.objects.link(ob);ob.parent=ROOT
    for mat in mats:me.materials.append(mat)
    for p in me.polygons:p.use_smooth=smoothness;p.material_index=mi[p.index] if mi else 0
    return ob

def rock(name,loc,size,angle):
    outline=[(-.47,-.28),(-.18,-.49),(.29,-.45),(.5,-.12),(.43,.34),(.08,.5),(-.34,.43),(-.5,.10)]
    vs=[]
    for z,r in [(-.5,.70),(-.17,1),(.25,.91),(.49,.58)]:
        for i,(x,y) in enumerate(outline):vs.append((x*size[0]*r,y*size[1]*r,(z+.025*math.sin(i*2.1))*size[2]))
    fs=[tuple(reversed(range(8))),tuple(range(24,32))];mi=[0,1]
    for k in range(3):
        for i in range(8):fs.append((8*k+i,8*k+(i+1)%8,8*(k+1)+(i+1)%8,8*(k+1)+i));mi.append(1 if k==2 else 0)
    ob=mesh(name,vs,fs,[M['selected boulder blue'],M['selected boulder lit planes']],mi,True);ob.location=loc;ob.rotation_euler.z=angle
    be=ob.modifiers.new('rounded native stone shoulders','BEVEL');be.width=.010;be.segments=3;be.profile=.65
    wn=ob.modifiers.new('broad crafted stone normals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=28
    return ob

def tube(name,base,height,radius,lean,color):
    prefix='teal' if color=='teal' else 'purple';n=32;vs=[]
    rings=[(0,.72),(.34*height,.82),(.72*height,.94),(height-.018,1),(height-.007,1.025),(height-.001,.94),(height,.84),(height-.007,.69),(height-.022,.63),(height-.052,.59),(.036,.46)]
    for z,s in rings:
        f=z/height;cx=base[0]+lean[0]*f*f;cy=base[1]+lean[1]*f*f
        for i in range(n):
            a=math.tau*i/n;r=radius*s*(1+.025*math.sin(3*a+.6));vs.append((cx+r*math.cos(a),cy+r*math.sin(a),base[2]+z))
    fs=[];mi=[]
    for k in range(len(rings)-1):
        for i in range(n):fs.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i));mi.append(0 if k<3 else 1 if k<8 else 2)
    fs.append(tuple(reversed(range((len(rings)-1)*n,len(rings)*n))));mi.append(2)
    return mesh(name,vs,fs,[M[prefix+' tube coral'],M[prefix+' rounded rim'],M[prefix+' inner wall']],mi,True)

def bead(name,loc,r,material,shape=(1,1,1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc);ob=bpy.context.object
    for col in list(ob.users_collection):col.objects.unlink(ob)
    COL.objects.link(ob);ob.parent=ROOT;ob.name='reef-end__'+name;ob.scale=tuple(r*s for s in shape);ob.data.materials.append(material)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def build():
    global SC,COL,ROOT,M,CORE
    source=RES/'canonical-middle02.blend';assert sha(source)=='51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5'
    bpy.ops.wm.open_mainfile(filepath=str(source));SC=bpy.context.scene;COL=bpy.data.collections['reef-middle'];ROOT=bpy.data.objects['reef-middle__root'];ROOT.location=(0,0,0);ROOT.rotation_euler.z=0;update()
    cm=bpy.data.objects['reef-middle__continuous_core'].data;cm.calc_loop_triangles();M={m.name:m for m in bpy.data.materials}
    collar=[]
    for t in cm.loop_triangles:
        ps=[list(cm.vertices[i].co) for i in t.vertices]
        if all(-.500001<=p[0]<=-.419999 for p in ps):
            collar.append({'canonicalTriangle':t.index,'vertices':ps,'cornerNormals':[list(cm.corner_normals[i].vector) for i in t.loops],'material':t.material_index,'materialName':cm.materials[t.material_index].name})
    collar_polygons=[]
    for p in cm.polygons:
        ps=[list(cm.vertices[i].co) for i in p.vertices]
        if all(-.500001<=v[0]<=-.419999 for v in ps):collar_polygons.append({'canonicalPolygon':p.index,'vertices':ps,'material':p.material_index})
    assert collar and collar_polygons
    canonical_fields={'sourceSHA256':sha(source),'collar':collar,'originalCollarPolygons':collar_polygons,'materials':{name:graph(M[name].node_tree) for name in ['reef blue stone','reef cyan stone planes']},'worldGraph':graph(SC.world.node_tree),'lights':[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in SC.objects if o.type=='LIGHT' and not o.hide_render]}
    assert abs(SC.world.node_tree.nodes['Background'].inputs['Strength'].default_value-.32)<1e-6
    for ob in list(COL.objects):
        if ob!=ROOT:bpy.data.objects.remove(ob,do_unlink=True)
    COL.name='reef-end';ROOT.name='reef-end__root';SC.name='reef-end native round01'
    vs=[];fs=[];mi=[];lookup={}
    def vertex(p):
        key=tuple(round(float(v),7) for v in p)
        if key not in lookup:lookup[key]=len(vs);vs.append(tuple(p))
        return lookup[key]
    def face(ps,mat):fs.append(tuple(vertex(p) for p in ps));mi.append(mat)
    # Keep original polygon loops as well as vertices. Native flat polygon
    # normal arithmetic then remains the canonical field before triangulation.
    for p in collar_polygons:face(p['vertices'],p['material'])
    xs=[-.42,-.34,-.22,-.08,.06,.16,.23,.29,.34]
    rings=[]
    for x in xs:
        # Same section through the collar approach, then broad native shaping.
        end=smooth((x-.14)/.20);crown=.018*math.exp(-((x+.06)/.20)**2)*smooth((x+.34)/.17)
        ring=[]
        for j,(y,z) in enumerate(PROFILE):
            zz=z*(1-.43*end)
            if j in [3,4,5,6]:zz+=crown;yy=y*(1-.07*end)
            else:yy=y
            ring.append((x,yy,zz))
        rings.append(ring)
    for k in range(len(rings)-1):
        for j in range(8):
            nxt=(j+1)%8;mat=1 if j in [2,3,4,5] else 0
            face([rings[k][j],rings[k][nxt],rings[k+1][nxt]],mat)
            face([rings[k][j],rings[k+1][nxt],rings[k+1][j]],mat)
    face(rings[-1],0)
    CORE=mesh('continuous_core',vs,fs,[M['reef blue stone'],M['reef cyan stone planes']],mi,False)
    CORE['connector']='Exact canonical .08 W collar, no geometric or field growth';CORE['finiteGround']='X[-.5,.34] Y[-.38,.38] Z0'
    # Literal canonical collar remains flat-shaded. Softened native support and
    # terrace masses articulate the exposed east cap without changing ground.
    rock('rear_shoulder',(-.21,.255,.381),(.27,.20,.17),-.14)
    rock('focal_terrace',(-.065,.12,.416),(.33,.28,.107),.10)
    rock('front_terrace',(-.045,-.245,.342),(.40,.22,.14),-.13)
    rock('rounded_end_shoulder',(.20,-.09,.319),(.24,.30,.19),.12)
    rock('end_foot_stone',(.245,-.20,.214),(.15,.25,.14),-.11)
    tube('teal_focal',(-.065,.145,.428),.244,.064,(.006,.011),'teal')
    tube('teal_branch_west',(-.135,.15,.422),.174,.045,(-.045,.020),'teal')
    tube('teal_branch_east',(.012,.15,.419),.197,.049,(.042,.018),'teal')
    tube('teal_front_mouth',(-.065,.047,.411),.130,.042,(-.017,-.028),'teal')
    tube('purple_west_main',(-.265,-.209,.343),.242,.055,(-.005,-.008),'purple')
    tube('purple_west_branch',(-.322,-.198,.337),.162,.035,(-.017,.014),'purple')
    tube('purple_west_bud',(-.205,-.247,.331),.147,.034,(.014,-.017),'purple')
    tube('purple_end_main',(.196,-.173,.345),.221,.054,(.009,-.005),'purple')
    tube('purple_end_branch',(.253,-.157,.324),.157,.033,(.018,.014),'purple')
    tube('purple_end_bud',(.145,-.227,.326),.140,.033,(-.008,-.017),'purple')
    bead('teal_crafted_nodule',(-.055,.084,.579),.014,M['teal rounded rim'],(1,.64,1.15))
    bead('purple_crafted_nodule',(-.266,-.254,.467),.012,M['purple rounded rim'],(1,.66,1.1))
    for i,(x,y,z,r) in enumerate([(-.15,-.17,.390,.040),(.085,-.10,.412,.035),(.12,.28,.340,.040),(-.34,.02,.381,.028)]):bead('teal_pebble_'+str(i),(x,y,z),r,M['teal tube coral'],(1,.82,.57))
    ROOT['assetId']='reef-end';ROOT['functionalEnvelope']=[.84,.76,.68];ROOT['ports']='W exact asymmetric reef-section-v1';ROOT['modeling']='Native closed termination, terrace stones and hollow tube coral; private editable meshes'
    SC.render.filter_size=.01;SC.eevee.taa_render_samples=64;SC.render.fps=12;SC.render.dither_intensity=0;SC.frame_start=1;SC.frame_end=1;SC.frame_set(1);ROOT.rotation_euler.z=0;camera();update()
    for me in list(bpy.data.meshes):
        if me.users==0:bpy.data.meshes.remove(me)
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)
    write(OUT/'canonical-field-adoption.json',canonical_fields)
    PROJECT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT),compress=True)

def geometry_audit():
    update();dg=bpy.context.evaluated_depsgraph_get();parts=[];points=[];core_geo=None
    for ob in COL.objects:
        if ob.type!='MESH':continue
        ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();transform=ROOT.matrix_world.inverted()@ev.matrix_world;ps=[transform@v.co for v in me.vertices];points.extend(ps)
        row={'name':ob.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'bounds':[[min(p[a] for p in ps) for a in range(3)],[max(p[a] for p in ps) for a in range(3)]],'materials':[m.name for m in me.materials],'privateMeshUsers':ob.data.users,'constraints':[c.type for c in ob.constraints],'modifiers':[m.type for m in ob.modifiers],'animation':bool(ob.animation_data or ob.data.animation_data or ob.data.shape_keys)}
        if ob==CORE:
            nt=transform.to_3x3().inverted().transposed()
            core_geo={'vertices':[list(p) for p in ps],'triangles':[list(t.vertices) for t in me.loop_triangles],'triangleRecords':[{'vertices':[list(ps[i]) for i in t.vertices],'cornerNormals':[list((nt@me.corner_normals[i].vector).normalized()) for i in t.loops],'material':me.materials[me.polygons[t.polygon_index].material_index].name} for t in me.loop_triangles]}
            bottom=[p for p in me.polygons if all(abs(ps[i].z)<1e-7 for i in p.vertices)]
            row['groundArea']=sum(p.area for p in bottom)
        parts.append(row);ev.to_mesh_clear()
    return {'sourceSHA256':sha(PROJECT),'measurement':'Actual evaluated geometry after saved-source reopening','blenderVersion':bpy.app.version_string,'bounds':[[min(p[a] for p in points) for a in range(3)],[max(p[a] for p in points) for a in range(3)]],'groundArea':next(p['groundArea'] for p in parts if 'groundArea' in p),'finiteGroundRectangle':[[-.5,-.38,0],[.34,.38,0]],'parts':parts,'coreGeometry':core_geo,'root':ROOT.name,'rootMatrix':[list(r) for r in ROOT.matrix_world],'worldGraph':graph(SC.world.node_tree),'lighting':[{'name':ob.name,'matrix':[list(r) for r in ob.matrix_world],'energy':ob.data.energy,'size':ob.data.size,'color':list(ob.data.color)} for ob in SC.objects if ob.type=='LIGHT' and not ob.hide_render],'render':{'engine':SC.render.engine,'samples':SC.eevee.taa_render_samples,'filterSize':SC.render.filter_size,'viewTransform':SC.view_settings.view_transform,'look':SC.view_settings.look,'exposure':SC.view_settings.exposure,'gamma':SC.view_settings.gamma,'dither':SC.render.dither_intensity},'linkedLibraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':im.name,'source':im.source,'filepath':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source!='GENERATED'],'actions':[a.name for a in bpy.data.actions]}

def render(p):p.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(p);bpy.ops.render.render(write_still=True)
def append_col(file,name):
    with bpy.data.libraries.load(str(file),link=False) as (src,dst):dst.collections=[name]
    col=dst.collections[0];SC.collection.children.link(col);col.hide_render=False;col.hide_viewport=False
    for ob in col.all_objects:ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
    update();root=next(ob for ob in col.all_objects if ob.type=='EMPTY' and ob.parent is None)
    return col,root
def core_snapshot(col,root):
    update();dg=bpy.context.evaluated_depsgraph_get();ob=next(ob for ob in col.all_objects if ob.type=='MESH' and 'continuous_core' in ob.name);ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();tr=root.matrix_world.inverted()@ev.matrix_world
    result={'vertices':[list(tr@v.co) for v in me.vertices],'triangles':[list(t.vertices) for t in me.loop_triangles]};ev.to_mesh_clear();return result

if OUT.exists() and any(OUT.iterdir()):raise FileExistsError('Immutable output exists: '+str(OUT))
OUT.mkdir(parents=True,exist_ok=True)
if '--replay' not in sys.argv:
    if PROJECT.exists():raise FileExistsError('Immutable source exists: '+str(PROJECT))
    build()
# All candidate pixels come from reopened saved source, not unsaved build state.
bpy.ops.wm.open_mainfile(filepath=str(PROJECT));SC=bpy.context.scene;COL=bpy.data.collections['reef-end'];ROOT=bpy.data.objects['reef-end__root'];CORE=bpy.data.objects['reef-end__continuous_core'];ROOT.rotation_euler.z=0;ROOT.location=(0,0,0);camera();update()
audit=geometry_audit();write(OUT/'geometry-audit.json',audit)
log={'sourceProject':str(PROJECT.relative_to(O)),'sourceSHA256':sha(PROJECT),'captureRecords':[],'contexts':[],'companionBindings':{'middle':sha(RES/'canonical-middle02.blend'),'edge':sha(RES/'approved-edge01.blend'),'corner':sha(RES/'corner-binding/round-01.blend')}}
for d,a in ANGLES.items():
    ROOT.rotation_euler.z=a;ROOT.location=(0,0,0);rec=camera();p=OUT/f'native/static/{d}/000.png';render(p)
    if '--replay' not in sys.argv:
        for q in [OUT/f'frames/static/{d}/000.png',OUT/f'atlases/static-{d}.png']:q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    log['captureRecords'].append({'direction':d,'clip':'static','frame':1,'index':0,'rootRotationZ':ROOT.rotation_euler.z,'actualRootMatrix':[list(r) for r in ROOT.matrix_world],'camera':rec,'path':str(p.relative_to(O)),'sha256':sha(p)})
    if d=='S':write(OUT/'published-camera.json',rec)

if '--heroes-only' not in sys.argv:
    COL.hide_render=True
    mc,mr=append_col(RES/'canonical-middle02.blend','reef-middle');mc.hide_render=True
    ec,er=append_col(RES/'approved-edge01.blend','reef-edge');ec.hide_render=True
    cc,cr=append_col(RES/'corner-binding/round-01.blend','reef-corner');cc.hide_render=True
    mc2=bpy.data.collections.new('incoming exact approved middle');SC.collection.children.link(mc2);mapping={}
    for ob in mc.objects:n=ob.copy();n.data=ob.data.copy() if ob.data else None;mc2.objects.link(n);mapping[ob]=n
    for ob,n in mapping.items():
        if ob.parent in mapping:n.parent=mapping[ob.parent]
    mr2=mapping[mr];mc2.hide_render=True
    assets={}
    for key,col,root in [('end',COL,ROOT),('middle',mc,mr),('edge',ec,er),('corner',cc,cr)]:
        col.hide_render=False;root.location=(0,0,0);root.rotation_euler.z=0;assets[key]=core_snapshot(col,root);col.hide_render=True
    write(OUT/'context-geometry.json',{'assets':assets,'projection':'X128; depth(-Y)128; Z-89.6 logical'})
    contexts={'direct-canonical-to-end':[('middle',mc,mr,-1,0,0),('end',COL,ROOT,0,0,0)],'full-family-L':[('middle',mc2,mr2,-2,2,-math.pi/2),('edge',ec,er,-2,1,-math.pi/2),('corner',cc,cr,-2,0,-math.pi/2),('middle',mc,mr,-1,0,0),('end',COL,ROOT,0,0,0)]}
    for kind,rows in contexts.items():
        for d,a in ANGLES.items():
            for col in [COL,mc,mc2,ec,cc]:col.hide_render=True
            measured=[]
            for key,col,root,x,y,angle in rows:
                col.hide_render=False;root.rotation_euler.z=a+angle;root.location=(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0);update()
                measured.append({'asset':key,'authoredRoot':[x,y,0],'authoredAngle':angle,'actualRootMatrix':[list(r) for r in root.matrix_world],'rootRotationZ':root.rotation_euler.z})
            rec=camera((832,992),(416,560));p=OUT/f'native/contexts/{kind}-{d}.png';render(p)
            log['contexts'].append({'kind':kind,'direction':d,'roots':measured,'camera':rec,'path':str(p.relative_to(O)),'sha256':sha(p)})
write(OUT/'capture-measurements.json',log)
print('REEF_END_NATIVE_CAPTURE_COMPLETE',flush=True)
