"""Portable native June rebuild/capture. Run with Blender --background --python this.py -- --mode main --label reproduction --preview.
Original packed libraries, native_actions.py, canonical food and registries travel beside this recipe.
No target image pixels are loaded in Blender. All actor forms are editable weighted geometry.
"""
import bpy, json, math, sys, hashlib, argparse, importlib.util
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent; OBJ=HERE.parent
ap=argparse.ArgumentParser(); ap.add_argument('--mode', choices=['main','runtime'], default='main'); ap.add_argument('--label', default='round-02'); ap.add_argument('--preview',action='store_true'); ap.add_argument('--capture-only',action='store_true'); ap.add_argument('--repeat',action='store_true'); ap.add_argument('--first',type=int,default=0); ap.add_argument('--last',type=int,default=1000)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
MODE=args.mode; LABEL=args.label; OUT=OBJ/'candidates'/LABEL; OUT.mkdir(parents=True,exist_ok=True)
PROJECT=HERE/(LABEL+('-runtime' if MODE=='runtime' else '')+'.blend')
spec=importlib.util.spec_from_file_location('june_native',HERE/'native_actions.py'); native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
REGPATH=OBJ/('inputs/runtime-variants/export/source/customer-june/rig.json' if MODE=='runtime' else 'inputs/source-rig.json')
record=json.loads(REGPATH.read_text()); brief=json.loads((OBJ/'brief.json').read_text()); foodmap=json.loads((OBJ/'reviews/food-mapping-proposal.json').read_text())
if not args.capture_only:
    if PROJECT.exists(): raise FileExistsError('Immutable source already exists: '+str(PROJECT))
    bpy.ops.wm.open_mainfile(filepath=str(HERE/('original-runtime.blend' if MODE=='runtime' else 'original-library.blend')))
root=bpy.data.objects[record['groundRootObject']]
sc=next(s for s in bpy.data.scenes if root.name in s.objects); bpy.context.window.scene=sc; bpy.context.window.view_layer=sc.view_layers[0]
col=next(c for c in sc.collection.children if root in list(c.all_objects)); arm=next(o for o in col.all_objects if o.type=='ARMATURE')
prefix='S10 meal ' if MODE=='runtime' else ''
def short(o): return o.name.split('customer_june__')[-1].replace('.001','')
def part(name): return next(o for o in col.all_objects if short(o)==name)
plane=next(o for o in col.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi');foodroot=plane.parent
asset={'root':root,'collection':col}
def linear(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def rgb(h): return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))
def material(key,h,rough=.55,specular=.25,coat=.04):
    m=bpy.data.materials.new('June warm '+key);m.diffuse_color=(*rgb(h),1);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*rgb(h),1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=specular;bs.inputs['Coat Weight'].default_value=coat;bs.inputs['Coat Roughness'].default_value=.4
    # Local soft occlusion modulates albedo; no baked direction or target texture.
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.075;ao.inputs['Color'].default_value=(1,1,1,1)
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.25;mix.inputs[1].default_value=(*rgb(h),1);m.node_tree.links.new(ao.outputs['Color'],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color']);m.node_tree.links.new(bs.outputs[0],out.inputs[0]);return m
def assign(o,m):o.data.materials.clear();o.data.materials.append(m)
def apply_modifier(o,m):
    bpy.context.view_layer.objects.active=o;o.hide_set(False);bpy.ops.object.modifier_apply(modifier=m.name)
def bind(o,group):
    o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1);o.vertex_groups.clear();o.vertex_groups.new(name=group).add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Weighted character deformation','ARMATURE');mod.object=arm
def mesh_replace(o,verts,faces,group=None):
    old=o.data;mesh=bpy.data.meshes.new(o.name+' remodeled mesh');mesh.from_pydata(verts,[],faces);mesh.update();o.data=mesh
    for m in list(o.modifiers):o.modifiers.remove(m)
    if group:bind(o,group)
    if old.users==0:bpy.data.meshes.remove(old)
def smooth(o):
    for p in o.data.polygons:p.use_smooth=True
def sphere_mesh(o,center,radius,group='head',rotation=(0,0,0),segments=36,rings=24):
    # Ring quads with true poles, no disconnected cap points.
    rm=Matrix.Rotation(rotation[0],4,'X')@Matrix.Rotation(rotation[1],4,'Y')@Matrix.Rotation(rotation[2],4,'Z');vs=[tuple(Vector(center)+rm@Vector((0,0,radius[2])))];fs=[]
    for j in range(1,rings):
        th=math.pi*j/rings
        for i in range(segments):
            a=2*math.pi*i/segments;v=Vector((radius[0]*math.sin(th)*math.cos(a),radius[1]*math.sin(th)*math.sin(a),radius[2]*math.cos(th)));vs.append(tuple(Vector(center)+rm@v))
    bottom=len(vs);vs.append(tuple(Vector(center)+rm@Vector((0,0,-radius[2]))))
    for i in range(segments):fs.append((0,1+i,1+(i+1)%segments))
    for j in range(rings-2):
        for i in range(segments):a=1+j*segments+i;b=1+j*segments+(i+1)%segments;fs.append((a,a+segments,b+segments,b))
    for i in range(segments):fs.append((bottom,1+(rings-2)*segments+(i+1)%segments,1+(rings-2)*segments+i))
    mesh_replace(o,vs,fs,group);smooth(o);return o
def new_obj(name):
    o=bpy.data.objects.new(prefix+'customer_june__'+name,bpy.data.meshes.new(name));col.objects.link(o);return o
def bevel(o,width,segments=5,weighted=True):
    # Replace source edge treatment while keeping central support planes.
    for m in list(o.modifiers):
        if m.type in ['BEVEL','WEIGHTED_NORMAL']:o.modifiers.remove(m)
    arm_mod=next((m for m in o.modifiers if m.type=='ARMATURE'),None)
    if arm_mod:o.modifiers.remove(arm_mod)
    b=o.modifiers.new('Soft crafted edges','BEVEL');b.width=width;b.segments=segments;b.affect='EDGES'
    apply_modifier(o,b);smooth(o)
    if weighted:
        w=o.modifiers.new('Crafted surface normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=35;apply_modifier(o,w)
    if arm_mod:
        m=o.modifiers.new('Weighted character deformation','ARMATURE');m.object=arm
def curve_mesh(o,points,radius,group,mat):
    cu=bpy.data.curves.new(o.name+' curved native form','CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=radius;cu.bevel_resolution=4;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
    tmp=bpy.data.objects.new('temporary construction',cu);col.objects.link(tmp);bpy.context.view_layer.objects.active=tmp;tmp.select_set(True);bpy.ops.object.convert(target='MESH');mesh=tmp.data.copy();bpy.data.objects.remove(tmp,do_unlink=True)
    o.data=mesh
    for m in list(o.modifiers):o.modifiers.remove(m)
    bind(o,group);assign(o,mat);smooth(o)

if not args.capture_only:
    # Rebuild in armature rest-space. Animation/rest data and all action IDs are untouched.
    for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
    col.hide_render=col.hide_viewport=False
    for o in col.all_objects:o.hide_set(False)
    mats={k:material(k,*v) for k,v in {'pink':('F14491',.4,.29,.08),'pinkLight':('F6529C',.43,.25,.05),'skin':('FFC477',.6,.23,.02),'shirt':('F4BD1D',.64,.2,.01),'collar':('FFD13D',.62,.2,.01),'navy':('153E88',.62,.22,.01),'navyCuff':('1B4F9C',.6,.2,.01),'shoe':('422920',.5,.27,.04),'eye':('241006',.22,.35,.1),'white':('FFF8DB',.3,.23,.02),'blush':('F77A7F',.68,.15,0)}.items()}
    for o in col.all_objects:
        if o.type!='MESH' or o==plane:continue
        for i,m in enumerate(o.data.materials):
            n=m.name.lower();key='pink' if 'hair' in n or 'ff5ab3' in n else 'skin' if 'skin' in n else 'shirt' if 'yellow' in n else 'navy' if 'navy' in n else 'blush' if 'blush' in n else 'white' if 'white' in n else 'eye' if 'eye' in n else None
            if key:o.data.materials[i]=mats[key]
    # Face box with broad soft corners; the fixed central mouth approach surface is retained.
    for v in part('head').data.vertices:
        if v.co.z>.8:v.co.z=.84
    bevel(part('head'),.082,8);bevel(part('neck'),.021,6)
    for s in [-1,1]:
        o=part('ear_'+str(s));bevel(o,.022,6)
        o=part('eye_'+str(s));sphere_mesh(o,(s*.103,-.244,.6892),(.025,.0135,.038));assign(o,mats['eye'])
        o=part('eye_glint_'+str(s));sphere_mesh(o,(s*.103-.007,-.256,.703),(.0068,.003,.009),segments=20,rings=12);assign(o,mats['white'])
        o=part('cheek_'+str(s));sphere_mesh(o,(s*.182,-.240,.591),(.035,.009,.019),segments=28,rings=14);assign(o,mats['blush'])
        bevel(part('brow_'+str(s)),.006,5)
    bevel(part('nose'),.020,6)
    curve_mesh(part('smile'),[(-.040,-.254,.555),(-.023,-.256,.539),(0,-.257,.534),(.023,-.256,.539),(.040,-.254,.555)],.004,'head',mats['eye'])
    # Native coherent bob: a common rounded crown and rear mass with overlapping flowing locks.
    sphere_mesh(part('rounded_crown'),(0,.018,.811),(.300,.273,.189));assign(part('rounded_crown'),mats['pink'])
    sphere_mesh(part('rounded_occiput'),(0,.115,.716),(.282,.193,.240));assign(part('rounded_occiput'),mats['pink'])
    for s in [-1,1]:
        for i in range(3):
            o=part('bob_side_'+str(s)+'_'+str(i));sphere_mesh(o,(s*(.263-i*.011),-.059+i*.119,.671+i*.017),(.075,.107,.205),rotation=(0,s*.08,s*.045));assign(o,mats['pinkLight'] if i==1 else mats['pink'])
        o=new_obj('bob_continuous_side_'+str(s));sphere_mesh(o,(s*.267,.028,.655),(.073,.231,.203));assign(o,mats['pink'])
    for i in range(5):
        x=(i-2)*.106;z=.826+(.012 if i%2==0 else 0);o=part('bob_fringe_'+str(i));sphere_mesh(o,(x,-.236,z),(.085,.072,.089),rotation=(0,-.14*x/.212,0));assign(o,mats['pinkLight'] if i in [0,4] else mats['pink'])
    for i in range(3):
        o=part('bob_nape_'+str(i));sphere_mesh(o,((i-1)*.173,.218,.558),(.109,.091,.107));assign(o,mats['pink'])
    # Larger soft swept crown petals, real geometry reaching into the common crown instead of a flat cap.
    for i,a in enumerate([2*math.pi*i/9 for i in range(9)]):
        o=new_obj('crown_swept_lock_%02d'%i);vs=[];fs=[];count=30;cross=16
        for j in range(count+1):
            u=j/count;th=.04+u*1.40;aa=a+.18*(1-u);dx=math.sin(aa);dy=-math.cos(aa)
            center=Vector((.300*math.sin(th)*dx,.018+.273*math.sin(th)*dy,.811+.189*math.cos(th)))
            normal=Vector((math.sin(th)*dx/.300,math.sin(th)*dy/.273,math.cos(th)/.189)).normalized();tangent=Vector((.300*math.cos(th)*dx,.273*math.cos(th)*dy,-.189*math.sin(th))).normalized();binormal=tangent.cross(normal).normalized()
            profile=math.sin(math.pi*u)**.45;wide=.006+.062*math.sin(th)*profile;deep=.001+.018*profile
            for k in range(cross):
                ang=2*math.pi*k/cross;v=center+normal*(math.cos(ang)*deep)+binormal*(math.sin(ang)*wide);vs.append(tuple(v))
        for j in range(count):
            for k in range(cross):p=j*cross+k;q=j*cross+(k+1)%cross;fs.append((p,q,q+cross,p+cross))
        fs.extend([tuple(reversed(range(cross))),tuple(count*cross+k for k in range(cross))]);mesh_replace(o,vs,fs,'head');smooth(o);assign(o,mats['pink'])
    # Keep functional hand/foot/pelvis carrier planes and weights, soften only bounded edges.
    bevel(part('pelvis'),.014,6)
    for side in ['L','R']:
        bevel(part('palm_'+side),.030,8);bevel(part('thumb_'+side),.015,7)
        bevel(part('minimal_foot_'+side),.010,6);assign(part('minimal_foot_'+side),mats['shoe'])
        # Original blended rings become gentle continuous cloth and skin volumes.
        for n in ['arm_'+side,'leg_'+side]:
            o=part(n);mod=next(m for m in o.modifiers if m.type=='ARMATURE');o.modifiers.remove(mod)
            sub=o.modifiers.new('Smooth native limb rings','SUBSURF');sub.subdivision_type='CATMULL_CLARK';sub.levels=2;apply_modifier(o,sub);smooth(o);mod=o.modifiers.new('Weighted character deformation','ARMATURE');mod.object=arm
        # Distinct sewn cuffs around the shorts, bound to the same thigh carrier.
        x=(-.115 if side=='L' else .115);o=new_obj('shorts_cuff_'+side)
        sphere_mesh(o,(x,-.014,.074),(.071,.067,.020),'thigh_'+side,segments=32,rings=14);assign(o,mats['navyCuff'])
    # Tunic has soft ring construction and a continuous hem, collar and small placket.
    def cloth_rings(o,rings,groups):
        vs=[];fs=[];num=40
        for z,rx,ry in rings:
            for i in range(num):
                a=2*math.pi*i/num;ca=math.cos(a);sa=math.sin(a);vs.append((rx*math.copysign(abs(ca)**.5,ca),-.008+ry*math.copysign(abs(sa)**.5,sa),z))
        for j in range(len(rings)-1):
            for i in range(num):p=j*num+i;q=j*num+(i+1)%num;fs.append((p,q,q+num,p+num))
        fs.extend([tuple(reversed(range(num))),tuple((len(rings)-1)*num+i for i in range(num))]);mesh_replace(o,vs,fs);o.vertex_groups.clear()
        for g in groups:o.vertex_groups.new(name=g)
        for i,v in enumerate(o.data.vertices):
            w=max(0,min(1,(v.co.z-.17)/.09)) if len(groups)>1 else 1
            o.vertex_groups[groups[-1]].add([i],w,'REPLACE')
            if len(groups)>1:o.vertex_groups[groups[0]].add([i],1-w,'REPLACE')
        mod=o.modifiers.new('Weighted character deformation','ARMATURE');mod.object=arm;smooth(o)
    cloth_rings(part('tailored_tunic'),[(.142,.192,.162),(.151,.200,.170),(.21,.204,.170),(.29,.208,.143),(.345,.200,.132),(.379,.164,.112)],['pelvis','spine']);assign(part('tailored_tunic'),mats['shirt'])
    cloth_rings(part('shirt_hem'),[(.143,.192,.163),(.148,.201,.171),(.164,.202,.172),(.172,.198,.170)],['pelvis']);assign(part('shirt_hem'),mats['collar'])
    for s in [-1,1]:
        o=part('collar_'+str(s))
        pts=[(s*.004,-.148,.387),(s*.058,-.139,.416),(s*.124,-.137,.396),(s*.104,-.174,.348),(s*.061,-.178,.358)]
        vs=pts+[(x,y+.014,z) for x,y,z in pts];faces=[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
        mesh_replace(o,vs,faces,'spine');bevel(o,.006,4);assign(o,mats['collar'])
    o=new_obj('polo_placket');sphere_mesh(o,(0,-.160,.333),(.021,.012,.043),'spine',segments=24,rings=16);assign(o,mats['collar'])
    # Canonical raster food remains an honest transparent full-UV packed plane.
    food='dish-salmon' if MODE=='runtime' else 'dish-cucumber';fm=foodmap[food]['isotropicFullUVMappingByThreshold']['128']
    for v,co in zip(plane.data.vertices,fm['canonicalFullQuadNativeVertices']):v.co=co
    for poly in plane.data.polygons:
        for li in poly.loop_indices:plane.data.uv_layers.active.data[li].uv=[(0,0),(1,0),(1,1),(0,1)][plane.data.loops[li].vertex_index]
    image=bpy.data.images.load(str(HERE/('canonical-salmon.png' if MODE=='runtime' else 'canonical-cucumber.png')),check_existing=False);image.pack()
    for m in plane.data.materials:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE':n.image=image
    plane['source_sha256']=hashlib.sha256(Path(image.filepath).read_bytes()).hexdigest();plane['source_image']='//'+Path(image.filepath).name;plane['mapping_threshold']=128;plane['mapping_convention']='pixel-boundary EDGE; bottommost occupied row support midpoint';plane['representation']='2D ImageGen sprite, not modeled sushi'
    # One constant depth for each food, along the registered orthographic camera ray.
    # No root/action/visibility or projected corner/support adjustment is made.
    depth=.33;xy=depth*math.cos(math.radians(35))/1.25
    for f in plane.animation_data.drivers:
        if f.data_path=='location' and f.array_index==0:f.driver.expression='-sin(facing)*'+repr(xy)
        if f.data_path=='location' and f.array_index==1:f.driver.expression='-cos(facing)*'+repr(xy)
    plane.location.z=depth*math.sin(math.radians(35))/1.25;plane['camera_ray_depth_bias_world_cells']=depth
    # One horizontally symmetric light setup for all views and actions.
    for o in list(sc.objects):
        if o.type=='LIGHT':o.hide_render=True
    lightcol=bpy.data.collections.new('June warm symmetric soft lighting');sc.collection.children.link(lightcol)
    for i,(loc,energy,size) in enumerate([((0,0,4.5),320,3.5)]+[((3*math.cos(i*math.pi/4),3*math.sin(i*math.pi/4),2.1),35,4.0) for i in range(8)]):
        d=bpy.data.lights.new('June soft area %02d'%i,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=(1,.965,.90);o=bpy.data.objects.new(d.name,d);lightcol.objects.link(o);o.location=loc;o.rotation_euler=(-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    world=bpy.data.worlds.new('June neutral warm ambient');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.68,.72,.78,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.30;sc.world=world
    sc.use_nodes=True;sc.compositing_node_group=None
    tree=bpy.data.node_groups.new('June transparent native pass','CompositorNodeTree');tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');rl=tree.nodes.new('CompositorNodeRLayers');out=tree.nodes.new('NodeGroupOutput');tree.links.new(rl.outputs['Image'],out.inputs['Image']);sc.compositing_node_group=tree
    sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=64;sc.eevee.use_raytracing=False
    sc.render.film_transparent=True;sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1;sc.render.fps=12;sc.render.dither_intensity=0
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=45
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    cam=sc.camera;cam.matrix_world=Matrix(json.loads((OBJ/'inputs/source-camera.json').read_text())['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
    def pixel(p):q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*384,(1-q.y)*640))
    y=pixel((0,0,0)).y;cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-y;cam.data.shift_y=(496-y)/dy
    native.apply_clip(asset,record,next(iter(record['clips'])),1,'S',sc)
    # All textures packed, source image paths resolve relative to portable recipe bundle.
    for image in bpy.data.images:
        if image.packed_file and image.filepath:image.filepath='//'+Path(image.filepath).name
    for o in col.all_objects:
        if o.type=='MESH' and o!=plane:
            for uv in list(o.data.uv_layers):o.data.uv_layers.remove(uv)
    plane['current_full_quad_world_dimensions']=[(plane.data.vertices[1].co-plane.data.vertices[0].co).length*1.25,(plane.data.vertices[3].co-plane.data.vertices[0].co).length*1.25]
    plane['legacy_fixed_alpha_rectangle_provenance']=plane.get('fixed_alpha_rectangle','')
    if 'fixed_alpha_rectangle' in plane:del plane['fixed_alpha_rectangle']
    plane['legacy_nominal_world_width_provenance']=plane.get('world_width_cells',.35)
    plane['world_width_cells']=(plane.data.vertices[1].co-plane.data.vertices[0].co).length*1.25
    sc['refinement']='June warm soft native round02';sc['sourceScale']=2
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT),compress=True)

cam=sc.camera
def pixel(p):q=world_to_camera_view(sc,cam,Vector(p));return [q.x*384,(1-q.y)*640]
def jwrite(name,obj): (OUT/(MODE+'-'+name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
def tree_hash(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];polys=[list(p.vertices) for p in m.polygons];tree=BVHTree.FromPolygons(vs,polys);e.to_mesh_clear();return vs,tree
baselines=json.loads((OBJ/('reviews/runtime-samples.json' if MODE=='runtime' else 'reviews/main-samples.json')).read_text());base={(b['clip'],b['facing'],b['frame']):b for b in baselines}
phases=[];frames=[]
clips=list(record['clips']);preview_frames=[1,4,7,10] if args.preview else range(1,13)
captures=[(clip,d,f) for clip in clips for d in ['S','E','N','W'] for f in preview_frames]
if args.preview: captures=[(clips[0],d,1) for d in ['S','E','N','W']]+[(c,d,7) for c in clips[1:] for d in ['S','E']]
if args.repeat:captures=[(clips[0],d,1) for d in ['S','E','N','W']]
for ci,(clip,d,frame) in enumerate(captures):
    if not args.first<=ci<args.last:continue
    native.apply_clip(asset,record,clip,frame,d,sc);dg=bpy.context.evaluated_depsgraph_get();body=[];surfaces={};parts={short(o):o for o in col.all_objects if o.type=='MESH'}
    for o in col.all_objects:
        if o.type!='MESH' or o==plane or o.hide_render:continue
        e=o.evaluated_get(dg);m=e.to_mesh();body.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
    b=base[(clip,d,frame)];tests={}
    for side in ['L','R']:
        for kind in ['palm','thumb']:
            vs,tree=tree_hash(parts[kind+'_'+side]);query=b['contacts'][kind+'_upwardSurface_'+side]['point'];p,n,ix,dist=tree.find_nearest(Vector(query));tests[kind+'_surface_'+side]={'sourcePoint':query,'nearest':list(p),'distanceWorld':dist,'intendedGroup':'hand_'+side,'groups':list(parts[kind+'_'+side].vertex_groups.keys())}
        vs,tree=tree_hash(parts['minimal_foot_'+side]);z=min(v.z for v in vs);tests['sole_'+side]={'minZ':z,'sourceMinZ':b['contacts']['foot_'+side]['supportZ'],'minZError':abs(z-b['contacts']['foot_'+side]['supportZ']),'sourceSoleCenterNearestDistance':tree.find_nearest(Vector(b['contacts']['foot_'+side]['soleCenter']))[3],'intendedGroup':'foot_'+side}
    for key,name in [('seat','pelvis'),('mouthSmile','smile'),('mouthHead','head')]:
        vs,tree=tree_hash(parts[name]);query=b['contacts'][key]['point'];p,n,ix,dist=tree.find_nearest(Vector(query));tests[key]={'sourceSurfacePoint':query,'nearest':list(p),'distanceWorld':dist,'groups':list(parts[name].vertex_groups.keys())}
    bones={pb.name:[list(r) for r in arm.matrix_world@pb.matrix] for pb in arm.pose.bones};boneErr=max(abs(bones[n][r][c]-m[r][c]) for n,m in b['bones'].items() for r in range(4) for c in range(4))
    zenv=brief['constraints']['functionalGeometryEnvelope']['perClipBodyZWorld'][clip.replace('_','-')]
    bounds={'min':[min(v[i] for v in body) for i in range(3)],'max':[max(v[i] for v in body) for i in range(3)]};envpass=bounds['min'][2]>=zenv[0]-1e-5 and bounds['max'][2]<=zenv[1]+1e-5 and max(abs(v[i]) for v in body for i in [0,1])<=.50001
    rel='frames/'+clip.replace('_','-')+'-'+d+('/%03d.png'%(frame-1));dest=OUT/('runtime' if MODE=='runtime' else 'main')/rel
    if args.repeat:dest=OUT/'repeat'/(MODE+'-'+d+'.png')
    dest.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    row={'clip':clip.replace('_','-'),'sourceClipId':clip,'direction':d,'index':frame-1,'frame':frame,'rootRotationZ':float(root.rotation_euler.z),'actualRootMatrix':[list(r) for r in root.matrix_world],'path':str(dest.relative_to(OBJ)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bodyBounds':bounds,'envelopePass':envpass,'boneMatrixMaxAbsError':boneErr,'contacts':tests,'foodVisible':not plane.hide_render,'foodRootMatrix':[list(r) for r in foodroot.matrix_world],'foodPlaneMatrix':[list(r) for r in plane.evaluated_get(dg).matrix_world],'foodPlaneRotation':list(plane.rotation_euler),'foodPlaneLocation':list(plane.location),'foodQuadPx':[pixel(plane.evaluated_get(dg).matrix_world@v.co) for v in plane.data.vertices]}
    phases.append(row);frames.append({k:row[k] for k in ['clip','direction','index','path','sha256']});print('JUNE_CAPTURE',MODE,clip,d,frame,'envelope',envpass,'boneErr',boneErr,flush=True)
jwrite('phases'+('-repeat' if args.repeat else '')+('-%03d-%03d'%(args.first,args.last)),phases)
jwrite('frames'+('-repeat' if args.repeat else '')+('-%03d-%03d'%(args.first,args.last)),frames)
print('JUNE_DONE',MODE,LABEL,len(phases),flush=True)
