"""Reproduce and audit the approved C125 production character revision.

Root orchestrator can load character_builders.py normally and rebuild all IDs.
This script deliberately does not overwrite an existing Blender project. Example:
  Blender --background --factory-startup --python THIS_FILE -- --out /tmp/c125-audit
Optional --save-project writes a NEW isolated project with all twelve characters.
The audit samples actual evaluated weighted meshes, all clips/facings and records
contact, full silhouette width/depth, complete projected height and source hashes.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import sys
import bpy
from mathutils import Vector

BASE=Path(__file__).resolve().parent


def load_builder():
    spec=importlib.util.spec_from_file_location('s33_character_revision_builder',BASE/'character_builders.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def evaluated_points(asset,include_2d=True):
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for obj in asset['collection'].all_objects:
        if obj.type!='MESH' or obj.hide_render:continue
        if not include_2d and obj.get('camera_ray_depth_bias_world_cells') is not None:continue
        evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
        try:
            for vertex in mesh.vertices:yield obj.matrix_world@vertex.co
        finally:evaluated.to_mesh_clear()


def audit_character(builder,asset):
    structural=builder.validate_character(asset,samples=12)
    if structural['weight_issues'] or structural['nonfinite_pose_matrices'] or not structural['ground_root_unchanged']:
        raise ValueError('Invalid native character rig: '+asset['root'].name)
    max_width=max_depth=max_height=max_planted_error=max_gait_contact_error=0.;full_bounds=None;largest_pose=None
    for clip,recipe in asset['clips'].items():
        count=12
        for i in range(count):
            phase=i/count if recipe['loop'] else i/(count-1)
            asset['pose'](clip,phase)
            for facing,radians in {'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2}.items():
                asset['root'].rotation_euler.z=radians;bpy.context.view_layer.update()
                points=list(evaluated_points(asset))
                ground_points=list(evaluated_points(asset,include_2d=False))
                bounds=[[min(p[k] for p in ground_points),max(p[k] for p in ground_points)] for k in range(3)]
                full_x=[min(p.x for p in points),max(p.x for p in points)]
                if any(abs(x)>.5001 for x in full_x):raise ValueError('Full 2D silhouette width exceeds tile '+asset['root'].name)
                width=full_x[1]-full_x[0];depth=bounds[1][1]-bounds[1][0]
                projected=[p.y*math.sin(math.radians(35))+p.z*math.cos(math.radians(35)) for p in points]
                height=max(projected)-min(projected)
                max_width=max(max_width,width);max_depth=max(max_depth,depth)
                if height>max_height:max_height=height;largest_pose=[clip,i,facing]
                if any(abs(v)>0.5001 for axis in bounds[:2] for v in axis):
                    raise ValueError('One-cell anatomy exceeded '+asset['root'].name+' '+str([clip,i,facing,bounds]))
                full_bounds=bounds if full_bounds is None else [[min(full_bounds[k][0],bounds[k][0]),max(full_bounds[k][1],bounds[k][1])] for k in range(3)]
            if clip in ('idle','stand','work','hold','load'):
                goals=json.loads(asset['armature']['feet_current'])
                for side in ('L','R'):
                    error=(asset['armature'].pose.bones['foot_'+side].head-Vector(goals[side])).length
                    max_planted_error=max(max_planted_error,error*builder.CHARACTER_SCALE)
            if clip in ('walk','panic'):
                goals=json.loads(asset['armature']['feet_current'])
                for side,offset in [('L',0.),('R',.5)]:
                    if (phase*(2 if clip=='panic' else 1)+offset)%1<.5:
                        error=(asset['armature'].pose.bones['foot_'+side].head-Vector(goals[side])).length
                        max_gait_contact_error=max(max_gait_contact_error,error*builder.CHARACTER_SCALE)
    if max_gait_contact_error>1e-5:raise ValueError('Walking stance ankle cannot reach ground goal '+asset['root'].name)
    asset['root'].rotation_euler.z=0;asset['pose']('idle' if asset['identity']['kind']=='chef' else 'stand',0.)
    if max_height>3.:raise ValueError('Complete projected silhouette exceeds three tiles')
    return {'identity':asset['identity'],'revision':'C-chunky-r3-125','nativeScale':builder.CHARACTER_SCALE,
        'ordinaryCameraElevationDegrees':35,'pixelAspect':[1,1],'footwear':'minimal navy toe ends; .043 unscaled cells high',
        'walkWorldTravelPerCycle':builder.WALK_STRIDE_CELLS,'panicCyclesPerSecond':2,
        'oneCellBoundsAcrossAllPoses':full_bounds,'maximumWidthCells':max_width,'maximumDepthCells':max_depth,
        'maximumCompleteProjectedHeightTiles':max_height,'largestPose':largest_pose,
        'maximumPlantedAnkleErrorCells':max_planted_error,'maximumGaitStanceAnkleErrorCells':max_gait_contact_error,'structuralRig':structural,
        'twoDimensionalFootprintPolicy':'Camera-ray depth bias on flat held sushi changes depth ordering only; strict full projected X bounds remain inside one cell. Physical body and knife XY are checked independently.',
        'framesPerClip':{clip:recipe['frames'] for clip,recipe in asset['clips'].items()},
        'visualApproval':'pending review of native captures; structural checks do not establish final art approval'}


def render_previews(assets,out):
    def module(name,file):
        spec=importlib.util.spec_from_file_location(name,BASE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
    runtime=module('s33_character_preview_runtime','capture_runtime.py')
    style=module('s33_character_preview_style','catalog_style.py')
    runtime.SCENE_NAME=bpy.context.scene.name;scene=bpy.context.scene;records=[]
    destination=out/'previews';destination.mkdir(exist_ok=True)
    for ident,clip in [('chef_lena','hold'),('chef_ellis','work'),('customer_rosa','walk'),('customer_june','eat')]:
        for other in assets.values():other['collection'].hide_render=True
        asset=assets[ident];asset['collection'].hide_render=False;style.apply(asset,ident.replace('_','-'))
        for direction,angle in [('S',0.),('E',math.pi/2),('N',math.pi),('W',-math.pi/2)]:
            asset['pose'](clip,.25);asset['root'].rotation_euler.z=angle
            runtime.configure_camera('character-orthographic',(192,320),(96,248),2)
            path=destination/(ident+'-'+clip+'-'+direction+'.png');scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True,scene=scene.name)
            records.append({'id':ident.replace('_','-'),'clip':clip,'phase':.25,'direction':direction,'path':str(path.relative_to(out)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return records


def run(out,save_project=False,with_props=False,preview=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    scene=bpy.data.scenes.new('S33 C125 isolated character audit');bpy.context.window.scene=scene
    builder=load_builder();assets={};report={
        'source':str(BASE/'character_builders.py'),'sourceSHA256':hashlib.sha256((BASE/'character_builders.py').read_bytes()).hexdigest(),
        'compositionSourceSHA256':hashlib.sha256((BASE/'character_composition.py').read_bytes()).hexdigest() if with_props else None,
        'selectedReference':'assets/character-scale-study C revision3 at uniform125%',
        'scope':'isolated character geometry and rig audit; no unrelated scene or project changes',
        'assets':{}}
    for ident in builder.CHARACTER_IDS:
        asset=builder.create_character(ident)
        if with_props:
            def module(name,file):
                spec=importlib.util.spec_from_file_location(name,BASE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
            food=module('s33_audit_food','food_belt_builders.py');composition=module('s33_audit_composition','character_composition.py')
            composition.add_held_props(asset,food,'dish-salmon' if ident.startswith('chef_') else 'dish-cucumber')
        assets[ident]=asset
        report['assets'][ident.replace('_','-')]=audit_character(builder,asset)
        print('AUDITED '+ident,flush=True)
    if save_project:
        destination=out/'characters-C125.blend'
        if destination.exists():raise FileExistsError('Refusing to overwrite editable project '+str(destination))
        bpy.data.libraries.write(str(destination),{scene},fake_user=True,compress=True)
        report['project']=str(destination);report['projectSHA256']=hashlib.sha256(destination.read_bytes()).hexdigest()
    if preview:report['nativePreviewCaptures']=render_previews(assets,out)
    (out/'character-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'assets':len(assets),'out':str(out),'maximumWidth':max(x['maximumWidthCells'] for x in report['assets'].values()),'maximumProjectedHeight':max(x['maximumCompleteProjectedHeightTiles'] for x in report['assets'].values())}),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--save-project',action='store_true');parser.add_argument('--with-props',action='store_true');parser.add_argument('--render-previews',action='store_true')
    options=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    run(options.out,options.save_project,options.with_props,options.render_previews)
