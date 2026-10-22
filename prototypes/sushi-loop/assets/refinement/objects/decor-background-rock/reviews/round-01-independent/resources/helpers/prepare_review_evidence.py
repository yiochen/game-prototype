from pathlib import Path
from PIL import Image
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;CAND=OBJ/'candidates/round-01';RES=HERE/'resources';RES.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packetsha='20f3fe4297877ecc50affda4574c2ade50482e7068bd9d457fbfb3e6ff2bc54c';assert sha(CAND/'packet.json')==packetsha
packet=json.loads((CAND/'packet.json').read_text());verified=[];unique={}
for group in ['files','candidateRenders','previews']:
    for name,r in packet[group].items():
        p=(CAND/r['path']).resolve();digest=sha(p);assert digest==r['sha256'],(group,name,p,digest)
        unique[str(p)]=digest;verified.append({'group':group,'name':name,'path':r['path'],'sha256':digest,'size':p.stat().st_size})
(HERE/'packet-integrity.json').write_text(json.dumps({'candidatePacketSHA256':packetsha,'packetRecordCount':len(verified),'uniqueBoundFiles':len(unique),'records':verified},indent=2)+'\n')
resources=[]
def copy(src,rel):
    dest=RES/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists(),dest;shutil.copy2(src,dest);resources.append({'sourcePath':str(src.relative_to(OBJ)) if src.is_relative_to(OBJ) else str(src),'path':str(dest.relative_to(OBJ)),'sha256':sha(dest),'size':dest.stat().st_size})
for rel in ['brief.json','inputs/root-native-contract.json','inputs/root-preparation-reconciliation-v1.json','inputs/source-camera.json','inputs/catalog-object.json','reviews/proposedcriteria.json','reviews/initial.json','inputs/original.png','inputs/target.png']:
    copy(OBJ/rel,Path(rel))
copy(OBJ.parent.parent/'style/warm-soft-reference.png',Path('inputs/warm-soft-reference.png'))
copy(OBJ/'source/round-01.blend',Path('native/candidate.blend'))
for rel in ['packet.json','validation.json','native-validation.json','native-camera.json','published-camera.json','rig.json','assetRecord.json','publication.json','support-audit.json','consumer/results.json','consumer/provenance.json','consumer/raster-extract.json','consumer/two-mode-comparison.json','consumer/fixture.html']:
    copy(CAND/rel,Path('candidate')/rel)
for rel in ['source/reproduce-round-01.py','source/publish-and-studies-round-01.py']:
    copy(OBJ/rel,Path('recipe')/Path(rel).name)
for name in ['REVIEW-COVERAGE.txt','PUBLISHER-HANDOFF.txt','HEADLESS-BROWSER-CONFIGS.txt']:
    copy(OBJ.parent.parent/'preparation'/name,Path('instructions')/name)
copy(OBJ.parent.parent/'preparation/decor-background-rock/judge-round-01-dispatch.txt',Path('instructions/actual-dispatch.txt'))
for name in ['sprite-layout.js','world-sprite-raster.js','exact-used-raster-functions.js','selected-library.json','playwright-package.json']:
    src=OBJ/'source/round-01-resources/consumer'/name
    if src.exists():copy(src,Path('consumer')/name)
for rel in ['SKILL.md','scripts/candidate_packet.py']:
    copy(Path('/Users/yiouchen/.codex/skills/refine-3d-model')/rel,Path('instructions/refine-3d-model')/rel)
for name in ['audit_directions.py','acceptance_contract.py']:
    copy(OBJ.parent.parent/'tools'/name,Path('instructions/tools')/name)
(HERE/'used-input-resources.json').write_text(json.dumps({'candidatePacketSHA256':packetsha,'pathBase':'object root','files':resources,'copyPolicy':'Exact actual-used source/input/code closure; no runtime app trees; no editor observations or self-ratings used.'},indent=2)+'\n')
media=[];aliases=[];seen={};tileRoot=HERE/'coverage-tiles';tileRoot.mkdir(exist_ok=True)
for group in ['candidateRenders','previews']:
    for name,r in packet[group].items():
        if r['path'] in seen:
            aliases.append({'group':group,'name':name,'path':r['path'],'sha256':r['sha256'],'sameExactPathAs':seen[r['path']]});continue
        seen[r['path']]=group+':'+name;src=CAND/r['path'];im=Image.open(src);im.load();tiles=[]
        for y in range(0,im.height,1024):
            for x in range(0,im.width,1024):
                box=[x,y,min(x+1024,im.width),min(y+1024,im.height)];slug=r['path'].replace('/','__').removesuffix('.png');dest=tileRoot/f'{slug}__{x}_{y}.png';tile=im.crop(box);tile.save(dest)
                assert Image.open(dest).tobytes()==tile.tobytes()
                tiles.append({'path':str(dest.relative_to(OBJ)),'sha256':sha(dest),'box':box,'size':list(tile.size)})
        reconstructed=Image.new(im.mode,im.size)
        for t in tiles:reconstructed.paste(Image.open(OBJ/t['path']),t['box'][:2])
        assert reconstructed.tobytes()==im.tobytes()
        media.append({'packetGroup':group,'firstAlias':name,'packetPath':r['path'],'sha256':r['sha256'],'size':list(im.size),'mode':im.mode,'tiles':tiles,'fullPixelReconstructionExact':True})
(HERE/'coverage-map.json').write_text(json.dumps({'candidatePacketSHA256':packetsha,'packetPathBase':'candidate folder','tilePathBase':'object root','uniqueMediaCount':len(media),'recordCount':len(media)+len(aliases),'media':media,'exactPathAliases':aliases,'note':'All media split into nonoverlapping lossless tiles <=1024x1024; exact decoded reassembly checked. Actual tile inspection is recorded separately after viewing, not inferred from this ledger.'},indent=2)+'\n')
print('VERIFIED',len(verified),'PACKET_RECORDS',len(unique),'UNIQUE_FILES','MEDIA',len(media),'TILES',sum(len(m['tiles']) for m in media),'ALIASES',len(aliases))
