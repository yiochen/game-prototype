"""Native reef-middle round 02. Run in Blender 5.2.2: --background --python reproduce-round-02.py.
-- --replay opens immutable round-02.blend instead of rebuilding it; --singles skips strips.
All image operations are native renders or byte-for-byte publication copies.
"""
import sys
sys.dont_write_bytecode=True
import bpy, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent; OBJ=BASE.parent; OUT=OBJ/'candidates/round-02'
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
PROFILE=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)]
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def mat(name,h,rough=.57,depth=False):
    c=[linear(int(h[i:i+2],16)/255) for i in (0,2,4)]
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.22
    bs.inputs['Base Color'].default_value=(*c,1)
    if not depth:
        geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(*(x*.70 for x in c),1)
        ramp.color_ramp.elements[1].position=.7;ramp.color_ramp.elements[1].color=(*(min(1,x*1.13) for x in c),1)
        l.new(sep.outputs['Z'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
    m.diffuse_color=(*c,1);return m
def mesh(name,vs,fs,mats,indices=None,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=ROOT
    for m in mats:me.materials.append(m)
    for p in me.polygons:p.use_smooth=smooth;p.material_index=indices[p.index] if indices else 0
    return o
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global SC,COL,ROOT
    SC=bpy.context.scene;SC.name='reef-middle native refinement round-02'
    COL=bpy.data.collections.new('reef-middle');SC.collection.children.link(COL)
    ROOT=bpy.data.objects.new('reef-middle__root',None);COL.objects.link(ROOT)
    blue=mat('reef blue stone','329BD3',.64);top=mat('reef cyan stone planes','47B6DD',.62)
    teal=mat('teal tube coral','21CDB4',.45);purple=mat('purple tube coral','B15BDA',.48)
    tlip=mat('teal rounded rim','66E5C0',.42);plip=mat('purple rounded rim','E18BE5',.44)
    tinner=mat('teal inner wall','128C86',.7,True);pinner=mat('purple inner wall','733297',.7,True)
    # Exact8point end rings and unchanged .08wide endpoint normal/material bands.
    # A continuous interior surface is sculpted into broad rock masses; no gaps/overlaps.
    stone=mat('selected boulder blue','368BC1',.60);stone_top=mat('selected boulder lit planes','42AAD2',.58)
    vs=[];vmap={};fs=[];mi=[];section=[]
    def vertex(p):
        key=tuple(round(float(v),10) for v in p)
        if key not in vmap:vmap[key]=len(vs);vs.append(tuple(p))
        return vmap[key]
    rings={x:[vertex((x,y,z)) for y,z in PROFILE] for x in [-.5,.5,-.42,.42]}
    fs.extend([tuple(reversed(rings[-.5])),tuple(rings[.5])]);mi.extend([0,0]);section.extend([-1,-1])
    def face(ids,j):fs.append(tuple(ids));mi.append(1 if j in [2,3,4,5] else 0);section.append(j)
    for xa,xb in [(-.5,-.42),(.42,.5)]:
        for j in range(8):face([rings[xa][j],rings[xa][(j+1)%8],rings[xb][(j+1)%8],rings[xb][j]],j)
    def sculpt(x,y,z):
        if abs(x)>=.42-1e-9 or z<1e-9:return (x,y,z)
        t=max(0,min(1,(.42-abs(x))/.10));w=t*t*(3-2*t)
        gap=max(math.exp(-((x+.16)/.034)**2),math.exp(-((x-.17)/.034)**2))
        side=max(0,min(1,(abs(y)-.20)/.18));rise=min(1,z/.07)
        inset=w*(.018*math.sin(math.pi*min(1,z/.46))+.062*gap*(.45+.55*side))*rise
        yy=y-math.copysign(inset,y) if abs(y)>.0001 else y
        dz=w*(.028*(1-gap)*math.sin(math.pi*min(1,z/.46))-.037*gap)*min(1,z/.10)
        bulge=.032*math.exp(-((x+.26)/.12)**2-((y-.17)/.20)**2)+.036*math.exp(-((x-.26)/.12)**2-((y-.17)/.20)**2)+.022*math.exp(-(x/.14)**2-((y+.25)/.15)**2)
        dz+=w*bulge*max(0,min(1,(z-.20)/.15))
        return (x,yy,z+dz)
    xs=[-.42,-.35,-.26,-.20,-.16,-.12,-.05,.06,.13,.17,.21,.28,.35,.42]
    for j in range(8):
        layers=[]
        for x in xs:
            us=[0,1] if abs(x)>=.42-1e-9 else [0,.22,.52,.78,1]
            a=PROFILE[j];b=PROFILE[(j+1)%8]
            layers.append([vertex(sculpt(x,a[0]*(1-u)+b[0]*u,a[1]*(1-u)+b[1]*u)) for u in us])
        for a,b in zip(layers,layers[1:]):
            if len(a)==len(b):
                for k in range(len(a)-1):face([a[k],a[k+1],b[k+1],b[k]],j)
            elif len(a)==2:
                face([a[0],a[1],b[-1]],j)
                for k in range(len(b)-1):face([a[0],b[k+1],b[k]],j)
            else:
                for k in range(len(a)-1):face([a[k],a[k+1],b[0]],j)
                face([a[-1],b[1],b[0]],j)
    core=mesh('reef-middle__continuous_core',vs,fs,[blue,top],mi,False)
    core['polygonSectionEdges']=section
    # Purposeful native boulders have rounded volumetric shoulders, small top planes
    # and broader contrasting side planes. Their lower parts are naturally buried.
    def rock(name,loc,size,ang,color):
        ring=[(-.45,-.29),(-.16,-.5),(.33,-.44),(.5,-.12),(.44,.35),(.10,.5),(-.34,.43),(-.5,.12)]
        layers=[(-.5,.72),(-.18,1),(.26,.91),(.49,.55)];v=[]
        for z,r in layers:
            for i,(x,y) in enumerate(ring):v.append((x*size[0]*r,y*size[1]*r,(z+.035*math.sin(i*2.0))*size[2]))
        f=[tuple(reversed(range(8))),tuple(range(24,32))];idx=[0,1]
        for k in range(3):
            for i in range(8):f.append((k*8+i,k*8+(i+1)%8,(k+1)*8+(i+1)%8,(k+1)*8+i));idx.append(1 if k==2 else 0)
        o=mesh(name,v,f,[color,stone_top],idx,True);o.location=loc;o.rotation_euler.z=ang
        be=o.modifiers.new('native softly rounded rock shoulders','BEVEL');be.width=.009;be.segments=3;be.affect='EDGES';be.profile=.65
        no=o.modifiers.new('weighted crafted stone planes','WEIGHTED_NORMAL');no.keep_sharp=True;no.weight=28
        return o
    rock('reef-middle__focal_rock',(-.025,.10,.417),(.32,.25,.12),-.10,stone)
    rock('reef-middle__front_rock',(.025,-.235,.383),(.33,.23,.18),.12,stone)
    rock('reef-middle__left_stone',(-.285,.14,.412),(.21,.25,.18),-.12,stone)
    rock('reef-middle__right_stone',(.285,.145,.416),(.21,.24,.175),.12,stone)
    rock('reef-middle__rear_crown',(0,.281,.339),(.25,.155,.215),-.10,stone)
    # Continuous hollow tube surfaces include rolled lip, true internal wall and recessed bowl floor.
    def tube(name,base,height,radius,lean,m,pad,inner):
        count=24;v=[];rings=[(0,.76),(height*.45,.88),(height-.018,1),(height-.005,1.02),(height,.88),(height-.009,.67),(height-.038,.62),(.045,.48)]
        for k,(z,s) in enumerate(rings):
            frac=z/height;cx=base[0]+lean[0]*frac*frac;cy=base[1]+lean[1]*frac*frac
            for i in range(count):
                a=2*math.pi*i/count;organic=1+.027*math.sin(3*a+.6)
                v.append((cx+radius*s*math.cos(a)*organic,cy+radius*s*math.sin(a)*organic,base[2]+z))
        faces=[];idx=[]
        for k in range(len(rings)-1):
            for i in range(count):faces.append((k*count+i,k*count+(i+1)%count,(k+1)*count+(i+1)%count,(k+1)*count+i));idx.append(0 if k<2 else 1 if k<5 else 2)
        faces.append(tuple(reversed(range((len(rings)-1)*count,len(rings)*count))));idx.append(2)
        return mesh(name,v,faces,[m,pad,inner],idx,True)
    tube('reef-middle__teal_focal',(-.035,.13,.421),.251,.071,(.006,.008),teal,tlip,tinner)
    tube('reef-middle__teal_left',(-.105,.13,.423),.163,.047,(-.042,.012),teal,tlip,tinner)
    tube('reef-middle__teal_right',(.054,.135,.423),.195,.052,(.049,.018),teal,tlip,tinner)
    tube('reef-middle__teal_front',(.005,.035,.417),.118,.043,(.023,-.023),teal,tlip,tinner)
    for label,x,y,highest in [('left',-.245,-.225,.617),('right',.245,-.215,.602)]:
        tube('reef-middle__purple_'+label,(x,y,.356),highest-.356,.057,((-.008 if x<0 else .009),-.005),purple,plip,pinner)
        tube('reef-middle__purple_'+label+'_bud',(x+(.066 if x<0 else -.066),y-.026,.346),.154,.035,(0,-.016),purple,plip,pinner)
        tube('reef-middle__purple_'+label+'_branch',(x+(-.061 if x<0 else .061),y+.014,.351),.169,.036,((-.018 if x<0 else .018),.018),purple,plip,pinner)
    # A few larger cyan pebbles provide a quiet secondary rhythm rather than uniform speckles.
    for i,(x,y,z,s) in enumerate([(-.13,-.15,.383,.055),(.14,-.12,.393,.045),(-.31,.285,.337,.04),(.30,-.03,.405,.035)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z));o=bpy.context.object
        for c in list(o.users_collection):c.objects.unlink(o)
        COL.objects.link(o);o.name='reef-middle__cyan_pebble_'+str(i);o.parent=ROOT;o.scale=(s,s*.83,s*.57);o.data.materials.append(teal)
        for p in o.data.polygons:p.use_smooth=True
    # Symmetric soft rig, no ground plane and no preferred horizontal key.
    SC.world=bpy.data.worlds.new('neutral soft environment');SC.world.use_nodes=True
    bg=SC.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.62,.69,.78,1);bg.inputs['Strength'].default_value=.32
    def light(n,loc,power,size):
        d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);SC.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    light('broad centered overhead',(0,0,4.5),100,5)
    for i in range(4):
        a=i*math.pi/2;light('equal cardinal fill '+str(i),(3*math.cos(a),3*math.sin(a),2.4),45,4.5)
    cam=bpy.data.objects.new('registered square-grid camera',bpy.data.cameras.new('registered square-grid camera'));SC.collection.objects.link(cam);SC.camera=cam
    SC.render.engine='BLENDER_EEVEE';SC.eevee.taa_render_samples=64
    SC.render.film_transparent=True;SC.render.filter_size=.01;SC.render.image_settings.file_format='PNG';SC.render.image_settings.color_mode='RGBA';SC.render.image_settings.color_depth='8';SC.render.image_settings.compression=100
    SC.render.dither_intensity=0;SC.render.fps=12;SC.frame_start=1;SC.frame_end=1;SC.frame_set(1)
    SC.view_settings.view_transform='Standard';SC.view_settings.look='None';SC.view_settings.exposure=0;SC.view_settings.gamma=1
    camera((192,352),(96,248));bpy.context.view_layer.update()
def camera(frame,anchor):
    sc=SC;cam=sc.camera;scale=2
    sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
    cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128;el=math.atan(1/.7)
    cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
    b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(anchor[1]*scale-b.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
    origin=px((0,0,0));return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'orthoScale':cam.data.ortho_scale,'elevationDegrees':math.degrees(el),'worldUnitsPerCell':1},'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filterSize':sc.render.filter_size,'publication':'Exact native PNG bytes; no reduction'}
def audit():
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();geoms=[];pts=[]
    for o in COL.objects:
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();vs=[o.matrix_world@v.co for v in me.vertices];pts.extend(vs)
        geoms.append({'name':o.name,'vertices':len(me.vertices),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'bounds':[[min(v[j] for v in vs) for j in range(3)],[max(v[j] for v in vs) for j in range(3)]],'privateMeshUsers':o.data.users,'materials':[m.name for m in me.materials],'animation':o.animation_data is not None,'shapeKeys':o.data.shape_keys is not None});e.to_mesh_clear()
    core=bpy.data.objects['reef-middle__continuous_core'];me=core.data;me.calc_loop_triangles();fields={}
    for side,x in [('W',-.5),('E',.5)]:
        ring=[(i,list(v.co)) for i,v in enumerate(me.vertices) if abs(v.co.x-x)<1e-6];adj=[]
        for p in me.polygons:
            if p.index<2:continue
            if any(abs(me.vertices[i].co.x-x)<1e-6 for i in p.vertices):
                adj.append({'sectionEdge':int(core.get('polygonSectionEdges',[])[p.index]),'polygon':p.index,'vertices':[list(me.vertices[i].co) for i in p.vertices],'normal':list(p.normal),'cornerNormals':[list(me.corner_normals[li].vector) for li in p.loop_indices],'material':me.materials[p.material_index].name,'baseColor':list(me.materials[p.material_index].diffuse_color)})
        fields[side]={'orderedYZ':[v[1][1:] for v in ring],'adjacentBands':adj}
    mats=[]
    for m in bpy.data.materials:
        nodes=[{'type':n.bl_idname,'name':n.name,'inputs':{s.identifier:list(s.default_value) if hasattr(s.default_value,'__iter__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and isinstance(s.default_value,(int,float,str,bool,tuple,list,bpy.types.bpy_prop_array))}} for n in m.node_tree.nodes] if m.use_nodes else []
        ramps=[{'node':n.name,'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]} for n in m.node_tree.nodes if n.type=='VALTORGB'] if m.use_nodes else []
        mats.append({'name':m.name,'nodes':nodes,'colorRamps':ramps,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links] if m.use_nodes else [],'animation':m.animation_data is not None or (m.node_tree.animation_data is not None if m.use_nodes else False)})
    return {'blender':bpy.app.version_string,'geometry':geoms,'bounds':[[min(v[j] for v in pts) for j in range(3)],[max(v[j] for v in pts) for j in range(3)]],'ports':fields,'evaluatedTriangles':[{'vertices':[list(me.vertices[i].co) for i in t.vertices],'normal':list(t.normal),'material':me.materials[t.material_index].name} for t in me.loop_triangles],'materials':mats,'images':list(bpy.data.images.keys()),'linkedLibraries':[l.filepath for l in bpy.data.libraries],'actions':list(bpy.data.actions.keys()),'lighting':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size,'type':o.data.type} for o in SC.objects if o.type=='LIGHT'],'world':{'strength':SC.world.node_tree.nodes.get('Background').inputs['Strength'].default_value},'frame':SC.frame_current,'filterSize':SC.render.filter_size,'static':True}
if '--replay' in sys.argv:
    if '--out' not in sys.argv:raise ValueError('Immutable replay requires --out pointing to a fresh directory inside the object folder')
    OUT=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
    if not OUT.is_relative_to(OBJ.resolve()):raise ValueError('Replay output must remain inside object folder')
    if OUT.exists() and any(OUT.iterdir()):raise FileExistsError('Refuse to overwrite prior capture evidence')
    OUT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-02.blend'));SC=bpy.context.scene;COL=bpy.data.collections['reef-middle'];ROOT=bpy.data.objects['reef-middle__root']
else:
    if (BASE/'round-02.blend').exists() or (OUT.exists() and any(OUT.iterdir())):raise FileExistsError('Refuse to overwrite saved source or prior candidate. Use --replay --out for a saved-source recapture.')
    OUT.mkdir(parents=True,exist_ok=True)
    build();bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'round-02.blend'),compress=True)
ROOT.rotation_euler.z=0;bpy.context.view_layer.update();write(OUT/'native-audit.json',audit())
log={'sourceProject':'source/round-02.blend','sourceSHA256':digest(BASE/'round-02.blend'),'captureRecords':[],'joined':[]}
for direction,angle in ANGLES.items():
    ROOT.rotation_euler.z=angle;bpy.context.view_layer.update();rec=camera((192,352),(96,248))
    p=OUT/f'native/static/{direction}/000.png';p.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    pub=OUT/f'frames/static/{direction}/000.png';pub.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,pub)
    atlas=OUT/f'atlases/static-{direction}.png';atlas.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,atlas)
    log['captureRecords'].append({'direction':direction,'clip':'static','frame':1,'index':0,'rootRotationZ':ROOT.rotation_euler.z,'actualRootMatrix':[list(r) for r in ROOT.matrix_world],'camera':rec,'nativePath':str(p.relative_to(OBJ)),'sha256':digest(p),'publishedSHA256':digest(pub),'atlasSHA256':digest(atlas)})
    if direction=='S':write(OUT/'published-camera.json',rec)
if '--singles' not in sys.argv:
    copies=[]
    for offset in [-1,1]:
        cc=bpy.data.collections.new('temporary exact native module '+str(offset));SC.collection.children.link(cc);mapping={}
        for o in COL.objects:
            n=o.copy();cc.objects.link(n);mapping[o]=n
        for o,n in mapping.items():
            if o.parent in mapping:n.parent=mapping[o.parent]
        copies.append((offset,mapping[ROOT]))
    for direction,angle in ANGLES.items():
        ROOT.rotation_euler.z=angle
        for offset,r in copies:r.rotation_euler.z=angle;r.location=(offset*math.cos(angle),offset*math.sin(angle),0)
        bpy.context.view_layer.update();rec=camera((448,608),(224,376));p=OUT/f'native/three-joined-{direction}.png';SC.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        log['joined'].append({'direction':direction,'rootRotationZ':ROOT.rotation_euler.z,'roots':[{'offset':i,'matrix':[list(row) for row in r.matrix_world]} for i,r in copies],'camera':rec,'path':str(p.relative_to(OBJ)),'sha256':digest(p)})
write(OUT/'capture-measurements.json',log)
print('NATIVE_REEF_CAPTURE_COMPLETE',flush=True)
