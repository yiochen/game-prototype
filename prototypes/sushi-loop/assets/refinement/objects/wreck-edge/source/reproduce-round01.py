"""Native wreck-edge round01. Exact canonical rails/rig; new native edge construction.
Run background Blender --factory-startup --python this.py [-- --recapture --output PATH].
All actually used inputs are private sibling resources. No source/production writes.
"""
import sys
sys.dont_write_bytecode = True
import bpy, math, json, hashlib, argparse
from pathlib import Path
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
RES = HERE / 'round01-resources'
parser = argparse.ArgumentParser()
parser.add_argument('--output', default=str(EXP / 'candidates/round-01'))
parser.add_argument('--recapture', action='store_true')
parser.add_argument('--probe', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT = Path(args.output); OUT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
write = lambda p,d: Path(p).write_text(json.dumps(d,indent=2)+'\n')
ANGLES = {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}

def linear(v): return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
def color(h): return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)

if not args.recapture:
    bpy.ops.wm.open_mainfile(filepath=str(RES/'canonical-middle02.blend'))
    sc=bpy.context.scene
    col=bpy.data.collections['Wreck middle authored candidate']
    root=bpy.data.objects['wreck-middle__root']
    # Exact canonical rails are a technical base. Other middle forms are removed.
    for o in list(col.objects):
        if o!=root and 'canonical_rail' not in o.name: bpy.data.objects.remove(o,do_unlink=True)
    root.name='wreck-edge__root'; col.name='Wreck edge native authored round01'
    for o in col.objects:
        if o!=root: o.name=o.name.replace('wreck-middle__','wreck-edge__')
    with bpy.data.libraries.load(str(RES/'original-library.blend'),link=False) as (src,dst):
        dst.collections=['S33_PROP_wreck-edge.001']
    original=dst.collections[0]
    original_root=next(o for o in original.all_objects if o.get('production_id')=='wreck-edge')
    for k,v in original_root.items(): root[k]=v
    for o in list(original.all_objects): bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(original)
    root['native_refinement']='warm-soft-round01-native-edge'
    root['locked_contact']='Exact approved middle02 full .08 side/cap normalized fields'
    root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
    wood=next(m for m in bpy.data.materials if m.name=='Blue painted timber - canonical height albedo')
    wood2=next(m for m in bpy.data.materials if m.name=='Blue painted timber - lower layered hue')
    iron=next(m for m in bpy.data.materials if m.name=='Slate iron - canonical soft edge')
    ironedge=next(m for m in bpy.data.materials if m.name=='Soft worn iron bevels')
    pale=next(m for m in bpy.data.materials if m.name=='Pale worn metal fasteners')
    wear=next(m for m in bpy.data.materials if m.name=='Restrained cream paint wear')
    grain=next(m for m in bpy.data.materials if m.name=='Shallow blue grain grooves')

    def mesh(name,verts,faces,mats):
        me=bpy.data.meshes.new(name+' native mesh');me.from_pydata(verts,[],faces);me.update()
        o=bpy.data.objects.new('wreck-edge__'+name,me);col.objects.link(o);o.parent=root
        for m in mats:me.materials.append(m)
        return o

    def bevel(o,width,segments=4,edge_material=None):
        b=o.modifiers.new('Soft substantial native bevel','BEVEL');b.width=width;b.segments=segments;b.affect='EDGES';b.profile=.5
        if edge_material is not None:b.material=edge_material
        for p in o.data.polygons:p.use_smooth=True
        n=o.modifiers.new('Weighted broad face normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=40
        return o

    def box(name,center,size,mat,radius=.015):
        x,y,z=center;dx,dy,dz=[v/2 for v in size]
        vs=[(x+sx*dx,y+sy*dy,z+sz*dz) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
        fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
        o=mesh(name,vs,fs,[mat,ironedge] if mat==iron else [mat])
        return bevel(o,radius,edge_material=1 if mat==iron else None)

    def line(name,points,mat,radius):
        cu=bpy.data.curves.new(name+' native curve','CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=radius;cu.bevel_resolution=2
        sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
        for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
        o=bpy.data.objects.new('wreck-edge__'+name,cu);col.objects.link(o);o.parent=root;cu.materials.append(mat);return o

    def bolt(name,x,y,z,back=False):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1,location=(x,y,z))
        o=bpy.context.object;o.name='wreck-edge__'+name
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o);o.parent=root;o.scale=(.023,.010,.023);o.data.materials.append(pale)
        for p in o.data.polygons:p.use_smooth=False
        return o

    # Two broad aged hull timbers leave a continuous airy rail reveal behind.
    # Their shaped shoulders and offsets are independently authored for this edge.
    box('aged_hull_low',(0,.096,.300),(.762,.272,.180),wood,.032)
    box('aged_hull_high',(0,.148,.472),(.754,.144,.144),wood2,.029)
    for i,x in enumerate([-.218,.218]):
        box('rounded_iron_rib_'+str(i),(x,.008,.435),(.101,.424,.680),iron,.023)
        box('lower_fastener_plate_'+str(i),(x,-.212,.344),(.145,.040,.174),iron,.021)
        for j,z in enumerate([.305,.382]):bolt('pale_front_rivet_'+str(i)+str(j),x,-.239,z)
        box('rear_fastener_plate_'+str(i),(x,.230,.446),(.126,.034,.146),iron,.017)
        bolt('pale_rear_rivet_'+str(i),x,.249,.446,True)

    # Distinct edge identity: a thick, irregular folded sheet with an exposed
    # forward mouth. Sloped top is native geometry, not a painted highlight.
    poly=[(-.249,-.369),(-.153,-.371),(.194,-.346),(.248,-.324),(.251,-.135),(-.250,-.136)]
    tops=[.188,.184,.182,.190,.252,.248]
    vs=[(x,y,z-.031) for (x,y),z in zip(poly,tops)]+[(x,y,z) for (x,y),z in zip(poly,tops)]
    count=len(poly);faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    sheet=mesh('folded_broken_sheet',vs,faces,[iron,ironedge]);bevel(sheet,.010,4,1)
    # Subtle creased metal seam and purposeful small worn paint slivers.
    line('sheet_fold_crease',[(-.214,-.251,.221),(-.10,-.256,.216),(.076,-.244,.220),(.216,-.235,.223)],ironedge,.0023)
    for i,(z,y) in enumerate([(.389,.094),(.546,.137),(.216,-.075),(.754,-.025)]):
        line('shallow_blue_grain_'+str(i),[(-.33,y,z),(-.11,y+.006,z+.001),(.12,y-.004,z),(.33,y+.003,z)],grain,.0020)
    for i,(x,z,y) in enumerate([(-.31,.217,-.116),(.29,.754,-.055),(-.04,.546,.13)]):
        line('short_worn_paint_'+str(i),[(x-.028,y,z),(x,y+.004,z+.001),(x+.030,y+.003,z)],wear,.0025)
    sc.name='Wreck edge warm soft native round01'
    sc.frame_start=1;sc.frame_end=1;sc.frame_set(1)
    # Remove unused original-library data, preserving exact used canonical data.
    for _ in range(3):bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
else:
    sc=bpy.context.scene;root=bpy.data.objects['wreck-edge__root'];col=bpy.data.collections['Wreck edge native authored round01']

def configure(frame=(192,352),anchor=(96,248)):
    cam=sc.camera;sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2
    cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
    el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
    base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*2-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
    r=px((0,0,0))
    return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(el)},'calibration':{'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)}}

root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1);bpy.context.view_layer.update();configure()
if not args.recapture:bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-01.blend'),compress=True)
records=[]
for d in (['S'] if args.probe else ['N','E','S','W']):
    root.rotation_euler.z=ANGLES[d];root.location=(0,0,0);bpy.context.view_layer.update();camera=configure()
    p=OUT/'native/static'/d/'000.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    records.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':[list(r) for r in root.matrix_world],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'sourceFilterSize':sc.render.filter_size,'camera':camera,'frame':sc.frame_current,'path':str(p.relative_to(OUT)),'sha256':sha(p),'sourceSHA256':sha(HERE/'round-01.blend')})
write(OUT/'capture-records.json',{'asset':'wreck-edge','blender':bpy.app.version_string,'sourceSHA256':sha(HERE/'round-01.blend'),'captureRecords':records,'publication':'Direct native2 PNG identity; no crop/repair/reduction'})
if args.probe:sys.exit(0)
write(OUT/'published-camera.json',records[0]['camera'])

# True native mixed neighbors are appended from exact approved source, not rebuilt.
with bpy.data.libraries.load(str(RES/'canonical-middle02.blend'),link=False) as (src,dst):dst.collections=['Wreck middle authored candidate']
can_col=dst.collections[0];sc.collection.children.link(can_col);can_col.hide_render=False;can_col.hide_viewport=False
canon=next(o for o in can_col.objects if o.name.startswith('wreck-middle__root'))
originals=list(can_col.objects);assembly=[]
for d,a in ANGLES.items():
    root.rotation_euler.z=a;root.location=(0,0,0);canon.rotation_euler.z=a;canon.location=Vector((-1,0,0));canon.location.rotate(Euler((0,0,a)))
    clones={}
    for o in originals:cp=o.copy();can_col.objects.link(cp);clones[o]=cp
    for o,cp in clones.items():cp.parent=clones.get(o.parent);cp.matrix_parent_inverse=o.matrix_parent_inverse.copy()
    other=clones[canon];other.rotation_euler.z=a;other.location=Vector((1,0,0));other.location.rotate(Euler((0,0,a)))
    bpy.context.view_layer.update();vertical=d in ['E','W'];camera=configure((192,608) if vertical else (448,352),(96,376) if vertical else (224,248))
    p=OUT/'mixed-native'/f'{d}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    assembly.append({'direction':d,'kind':'exact approved middle02 + candidate edge + exact approved middle02','sourceSHA256':sha(HERE/'round-01.blend'),'canonicalSourceSHA256':sha(RES/'canonical-middle02.blend'),'camera':camera,'path':str(p.relative_to(OUT)),'sha256':sha(p),'moduleRootMatrices':{'middleAtMinus1':[list(r) for r in canon.matrix_world],'derivativeCenter':[list(r) for r in root.matrix_world],'middleAtPlus1':[list(r) for r in other.matrix_world]},'localModuleRoots':[[-1,0,0],[0,0,0],[1,0,0]],'internalCaps':'Actual coincident cap geometry retained; no deletion, overlap, shift or raster repair'})
    for cp in clones.values():bpy.data.objects.remove(cp,do_unlink=True)
write(OUT/'native-assembly-records.json',assembly)
print('WRECK_EDGE_NATIVE_COMPLETE',OUT)
