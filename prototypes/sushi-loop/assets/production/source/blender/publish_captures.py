"""Package full registered Blender captures without silhouette fitting.
Uses the skill packer at uniform 2x runtime scale; raw 4x frames remain retained.
"""
import argparse, json, shutil, hashlib, sys, math
from pathlib import Path
from PIL import Image

SKILL=Path('/Users/yiouchen/.codex/skills/generate-blender-characters/scripts')
sys.path.insert(0,str(SKILL))
from pack_captures import pack

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--ids',nargs='+',required=True);args=ap.parse_args()
    native=Path(__file__).parent/'export';target=args.repo/'prototypes/sushi-loop/assets/production';source=target/'source';source.mkdir(exist_ok=True)
    manifest=json.loads((target/'library.json').read_text());byid={a['id']:a for a in manifest['objects']}
    aliases={'crate':'crate-wood','barrel':'barrel-wood','plant':'plant-angular','lantern':'lantern-gold'}
    for capture_id in args.ids:
        aid=aliases.get(capture_id,capture_id)
        rec=native/'source'/capture_id
        info=json.loads((rec/'asset.json').read_text());camera_meta=json.loads((rec/'camera.json').read_text());a=byid[aid]
        # Canonical schema ID for the exact calibrated square top/front profile.
        if info['projection']!='character-orthographic':
            info['projection']='top-down-oblique-square-grid';camera_meta['projection']='top-down-oblique-square-grid';camera_meta['name']='square top/front oblique'
        a.update(status='ready',frameSize=info['frame'],root=info['anchor'],sourceScale=2,projection=info['projection'],footprint=info['footprint'],height=info['height'],clips=[])
        a['productionStage']='Native Blender pass · awaiting final art approval'
        a['kind']='floor' if aid.startswith('floor-') else 'belt' if aid.startswith('belt-') else 'character' if aid.startswith(('chef-','customer-')) else 'prop'
        a['layer']=0 if a['kind']=='floor' else 1 if a['kind']=='belt' else 3 if aid.startswith('dish-') else 2
        source_record=source/'records'/aid;source_record.mkdir(parents=True,exist_ok=True)
        (source_record/'camera.json').write_text(json.dumps(camera_meta,indent=2)+'\n');(source_record/'asset.json').write_text(json.dumps(info,indent=2)+'\n');camera=source_record/'camera.json'
        a['sockets']={k:[v[0]*128,(-v[1]-v[2])*128] for k,v in info.get('sockets',{}).items()}
        guides=[]
        for clip_id,recipe in info['clips'].items():
            count=recipe['frames'];static=recipe.get('static',False) or count==1
            export_clip='static' if static else clip_id
            clip={'id':export_clip,'name':export_clip.replace('_',' ').replace('-',' ').title(),'frames':count,'fps':12,'loop':False if static else recipe.get('loop',True),'directions':{}}
            for direction in ['N','E','S','W']:
                raw=native/'raw-frames'/capture_id/(clip_id+'-'+direction);frames=sorted(raw.glob('*.png'))
                if len(frames)!=count:raise ValueError(f'{aid}/{clip_id}/{direction}: {len(frames)} != {count}')
                packed=source/'registered'/aid/(export_clip+'-'+direction)
                if not packed.exists():
                    if a['kind']=='floor':
                        packed.mkdir(parents=True);(packed/'source-captures').mkdir()
                        im=Image.open(frames[0]).convert('RGBA');w,h=[v*2 for v in info['frame']];im.resize((w,h),Image.Resampling.LANCZOS).save(packed/'sheet.png')
                        shutil.copyfile(frames[0],packed/'source-captures/000.png')
                        guide={'frame':info['frame'],'anchor':info['anchor'],'captureScale':2,'sourceCaptureScale':4,'columns':1,'rows':1,'size':[w,h],'cells':[{'index':0,'rect':[0,0,w,h]}],'sourceCaptures':[{'path':'source-captures/000.png','sha256':sha(frames[0])}],'processing':'Uniform whole authored floor canvas 4x to 2x; no fitting; opaque floor deliberately covers frame'}
                        (packed/'guide.json').write_text(json.dumps(guide,indent=2)+'\n')
                    else:guide=pack(raw,camera,packed,kind='object' if static else 'animation',columns=6,gutter=0,sheet_scale=2)
                else:guide=json.loads((packed/'guide.json').read_text())
                runtime=target/'sprites'/aid;runtime.mkdir(parents=True,exist_ok=True)
                filename=export_clip+'-'+direction+'.png';shutil.copyfile(packed/'sheet.png',runtime/filename)
                clip['directions'][direction]={'image':f'sprites/{aid}/{filename}','columns':guide['columns'],'rows':guide['rows']}
                guides.append(str((packed/'guide.json').relative_to(target)))
            a['clips'].append(clip)
        a['source']={'blend':'source/blender/sushi-loop-world-library.blend','modelScript':'source/blender/character_builders.py' if a['kind']=='character' else 'source/blender/food_belt_builders.py' if aid.startswith(('floor-','dish-','belt-')) else 'source/blender/prop_builders.py','camera':str((source_record/'camera.json').relative_to(target)),'guide':guides[0],'guides':guides,'assetRecord':str((source_record/'asset.json').relative_to(target))}
        # Same-size comparisons are staged fixtures, not gameplay.
        stool='stool-wood';dish='dish-salmon';belt='belt-straight-e'
        if aid in ['stool-wood','stool-blue']:
            a['interactions']=[{'name':'Seats beside a serving belt','gridSize':[4,3],'placements':[{'object':aid,'x':1,'y':1,'direction':'S'},{'object':belt,'x':2,'y':1,'direction':'S','clip':'running'},{'object':dish,'x':2,'y':1,'direction':'S','offset':[0,-81.92]}]}]
        elif a['kind']=='belt':
            a['interactions']=[{'name':'Touching empty modules','gridSize':[3,2],'placements':[{'object':aid,'x':x,'y':1,'direction':'S','clip':'running'} for x in range(3)]},{'name':'Independent dish on a running deck','gridSize':[3,2],'placements':[{'object':aid,'x':1,'y':1,'direction':'S','clip':'running'},{'object':dish,'x':1,'y':1,'direction':'S','offset':[0,-81.92]}]}]
            if aid=='belt-corner-n-e':a['interactions'][0]={'name':'Connected straight → corner → straight','gridSize':[3,3],'placements':[{'object':belt,'x':1,'y':0,'direction':'W','clip':'running'},{'object':aid,'x':1,'y':1,'direction':'S','clip':'running'},{'object':belt,'x':2,'y':1,'direction':'S','clip':'running'}]}
            if aid=='belt-straight-e':a['interactions'].append({'name':'Moving dish conveyed across a connected strip','gridSize':[4,2],'placements':[{'object':aid,'x':x,'y':1,'direction':'S','clip':'running'} for x in range(4)]+[{'object':dish,'x':0,'y':1,'direction':'S','offset':[0,-81.92],'motion':{'path':[[0,1],[3,1]],'duration':3,'loop':True}}]})
        elif aid.startswith('dish-'):
            a['interactions']=[{'name':'Plate on the running serving surface','gridSize':[3,3],'placements':[{'object':belt,'x':1,'y':1,'direction':'S','clip':'running'},{'object':aid,'x':1,'y':1,'direction':'S','offset':[0,-81.92]},{'object':stool,'x':1,'y':2,'direction':'S'}]}]
        else:a['interactions']=[{'name':'Shared scale beside restaurant furniture','gridSize':[3,3],'placements':[{'object':aid,'x':1,'y':1,'direction':'S'},{'object':stool,'x':2,'y':1,'direction':'S'}]}]
        print(aid,[(c['id'],c['frames']) for c in a['clips']])
    models=source/'blender';models.mkdir(exist_ok=True)
    shutil.copyfile(native/'source/sushi-loop-world-library.blend',models/'sushi-loop-world-library.blend')
    for name in ['capture_runtime.py','prop_builders.py','character_builders.py','creature_fx_builders.py','food_belt_builders.py','publish_captures.py']:
        p=Path(__file__).parent/name
        if p.exists():shutil.copyfile(p,models/name)
    manifest['approval']={'concept':'approved','finalAssets':'pending','issue':33};manifest['production']={'pipeline':'Blender MCP native source and registered 2D captures','captureScale':4,'runtimeSourceScale':2,'fps':12,'editableProject':'source/blender/sushi-loop-world-library.blend'}
    (target/'library.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
