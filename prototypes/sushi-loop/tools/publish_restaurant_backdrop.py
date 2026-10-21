#!/usr/bin/env python3
"""Promote the user-approved uniform-light wall without altering authored pixels."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/restaurant-backdrop/uniform35'
DEST=ROOT/'assets/production'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
def main():
 book=json.loads((SOURCE/'camera.json').read_text())
 receipt=json.loads((SOURCE/'render-receipt.json').read_text())
 assert sha(SOURCE/'source/restaurant-backdrop-35.blend')==receipt['sourceSha256']
 native=DEST/'source/backdrop';native.mkdir(parents=True,exist_ok=True)
 for name in ['camera.json','geometry-audit.json','render-receipt.json','provenance.json']:
  shutil.copyfile(SOURCE/name,native/name)
 shutil.copyfile(SOURCE/'source/restaurant-backdrop-35.blend',native/'restaurant-backdrop-35.blend')
 library=json.loads((DEST/'library.json').read_text())
 identities={'gate':'backdrop-entrance','wall-plain':'backdrop-wall'}
 objects=[]
 for source_id,identity in identities.items():
  camera=book['assets'][source_id];width=camera['widthTiles'];frame=camera['frame'];scale=camera['captureScale']
  image=f'sprites/{identity}/static-S.png';target=DEST/image;target.parent.mkdir(parents=True,exist_ok=True)
  original=SOURCE/'renders'/f'{source_id}.png'
  assert sha(original)==next(r['sha256'] for r in receipt['renders'] if r['id']==source_id)
  shutil.copyfile(original,target)
  plane={'width':width,'height':3,'openingWidth':2 if source_id=='gate' else 0,'baseboard':True,'lighting':'uniform ambient'}
  obj={'id':identity,'name':'Restaurant entrance backdrop' if source_id=='gate' else 'Blank wood wall backdrop','family':'W02','kind':'backdrop','status':'ready','footprint':[width,3],'rootCell':[width/2,3],'frameSize':frame,'root':camera['anchor'],'sourceScale':scale,'projection':'character-orthographic','facingPolicy':'single-player-facing','layer':0,'renderPass':'background','backdrop':plane,'productionStage':'Approved Blender backdrop · 35° camera · uniform light','reviewNote':f'{width} × 3 projected tiles, including flat roof tiles and a continuous wooden baseboard. '+('The clear opening is exactly 2 tiles wide.' if source_id=='gate' else 'Repeats horizontally with no windows or extra pillars.'),'registration':{'method':'authored-backdrop-plane','completeFrame':frame,'anchor':camera['anchor'],'cellSize':128,'sourceCaptureScale':scale,'poseFitting':False,'contentRect':camera['contentRect']},'clips':[{'id':'static','name':'Static','frames':1,'fps':12,'static':True,'loop':False,'directions':{'S':{'image':image,'columns':1,'rows':1,'atlasSize':[v*scale for v in frame],'rects':[[0,0,*[v*scale for v in frame]]],'sha256':sha(target)}}}],'requirements':{'directions':['S'],'states':['static'],'animated':False,'fps':12,'notes':'Fixed restaurant backdrop plane; no turning or per-sprite stretching.'},'source':{'pipeline':'blender-backdrop','blend':'source/backdrop/restaurant-backdrop-35.blend','camera':'source/backdrop/camera.json','assetRecord':f'source/backdrop/{identity}.json','approvedSource':'../restaurant-backdrop/uniform35','hashes':{'source/backdrop/restaurant-backdrop-35.blend':receipt['sourceSha256'],image:sha(target)}},'interactions':[{'name':'Three blank tiles, entrance, then blank walls','gridSize':[11,6],'placements':[{'object':'backdrop-wall','x':x,'y':0,'direction':'S'} for x in [0,1,2,7,8,9,10]]+[{'object':'backdrop-entrance','x':3,'y':0,'direction':'S'},{'object':'chef-lena','x':4,'y':4,'direction':'S','clip':'idle'}]}]}
  write(native/f'{identity}.json',{'id':identity,'surface':plane,'camera':camera,'geometryAudit':'geometry-audit.json','approvedOn':'2026-10-20'})
  objects.append(obj)
 library['objects']=[o for o in library['objects'] if o['id'] not in {'entry-finished',*identities.values()}]
 index=next(i for i,o in enumerate(library['objects']) if o['family']=='W02')
 library['objects'][index:index]=objects
 library['approval']['backdrop']={'approvedOn':'2026-10-20','source':'../restaurant-backdrop/uniform35','lighting':'uniform ambient','replaces':'entry-finished'}
 current=DEST/'source/blender/sushi-loop-world-library-current.blend'
 if current.is_file():
  library['production']['editableProject']=current.relative_to(DEST).as_posix()
  library['production']['currentProjectSha256']=sha(current)
 write(DEST/'library.json',library)
 # Existing character/feedback derivatives bind to the current catalog only
 # while their complete approved base object records remain identical.
 by_id={obj['id']:obj for obj in library['objects']}
 for family in ['recipe-variants','chef-variants','feedback-variants']:
  path=ROOT/'godot/assets'/family/'manifest.json'
  variants=json.loads(path.read_text())
  for identity,expected in variants['baseObjectSha256'].items():
   actual=hashlib.sha256(json.dumps(by_id[identity],sort_keys=True,separators=(',',':')).encode()).hexdigest()
   if actual!=expected:raise ValueError('Approved derivative base changed: '+identity)
  variants['baseLibrarySha256']=sha(DEST/'library.json')
  write(path,variants)
 for relative in ['sprites/entry-finished','source/records/entry-finished','source/native-records/entry-finished','source/registered/entry-finished']:
  folder=DEST/relative
  if folder.exists():shutil.rmtree(folder)
 for group in ['native-records','records']:
  index=DEST/'source'/group/'index.json'
  if index.exists():
   data=json.loads(index.read_text())
   data['assetIds']=[key for key in data.get('assetIds',[]) if key!='entry-finished']
   if isinstance(data.get('records'),dict):data['records'].pop('entry-finished',None)
   write(index,data)
 runtime=ROOT/'godot/assets/catalog/sprites/entry-finished'
 if runtime.exists():shutil.rmtree(runtime)
 print('Promoted two approved backdrop sprites; retired the old entrance exports and active capture records.')
if __name__=='__main__':main()
