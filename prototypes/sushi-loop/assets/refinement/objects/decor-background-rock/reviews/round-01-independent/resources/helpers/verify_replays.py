from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import json,hashlib,math
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;CAND=OBJ/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def difference(a,b):
    a=Image.open(a).convert('RGBA') if isinstance(a,Path) else a.convert('RGBA');b=Image.open(b).convert('RGBA') if isinstance(b,Path) else b.convert('RGBA');assert a.size==b.size
    diff=ImageChops.difference(a,b);stat=ImageStat.Stat(diff)
    return {'size':list(a.size),'decodedExact':a.tobytes()==b.tobytes(),'meanAbsoluteRGBA':stat.mean,'maxAbsoluteRGBA':[v[1] for v in diff.getextrema()],'alphaExact':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'differentPixelCount':sum(px!=(0,0,0,0) for px in diff.getdata())}
native=load(HERE/'independent-native-audit.json');natives={}
for d in 'NESW':
    submitted=CAND/'native/static'/d/'000.png';replay=HERE/'native-replay'/d/'000.png';pub=CAND/'frames/static'/d/'000.png';atlas=CAND/'atlases'/f'static-{d}.png';image=Image.open(submitted).convert('RGBA');expected=image.resize((384,704),Image.Resampling.LANCZOS)
    natives[d]={'independentReplay':difference(submitted,replay),'wholeCanvasLanczosEqualsPublished':expected.tobytes()==Image.open(pub).convert('RGBA').tobytes(),'publishedEqualsAtlasBytes':sha(pub)==sha(atlas),'publishedFrame':list(Image.open(pub).size),'nativeFrame':list(image.size),'submittedSHA256':sha(submitted),'replaySHA256':sha(replay),'publishedSHA256':sha(pub),'atlasSHA256':sha(atlas)}
assert all(x['wholeCanvasLanczosEqualsPublished'] and x['publishedEqualsAtlasBytes'] for x in natives.values())
assert all(x['independentReplay']['alphaExact'] and max(x['independentReplay']['maxAbsoluteRGBA'])<=1 for x in natives.values())
replay=load(HERE/'consumer-replay/results.json');browser=[]
for mode in replay['modes']:
    for c in mode['cases']:
        origScreen=OBJ/c['originalScreenshot'];origNative=OBJ/c['originalNativeCanvas']
        rec={'mode':mode['mode'],'browserVersion':mode['browserVersion'],'config':c['config'],'viewport':c['viewport'],'dpr':c['dpr'],'boundsExact':c['bounds']==c['originalBounds'],'planExact':c['plan']==c['originalPlan'],'spriteRecordsExact':c['spriteRecords']==c['originalSpriteRecords'],'orderExact':c['order']==c['originalOrder'],'errors':c['errors'],'screenshot':difference(origScreen,OBJ/c['screenshot']),'nativeCanvas':difference(origNative,OBJ/c['nativeCanvas'])}
        assert rec['boundsExact'] and rec['planExact'] and rec['spriteRecordsExact'] and rec['orderExact'] and not rec['errors'];browser.append(rec)
assert all(r['nativeCanvas']['decodedExact'] for r in browser)
brief=load(HERE/'resources/brief.json');expectedCases=brief['qualityCriteria']['requiredEvidence']['consumerCasesPerMode'];assert all([c['config'] for c in m['cases']]==expectedCases for m in replay['modes'])
code=(HERE/'resources/consumer/world-sprite-raster.js').read_text();extract=code[code.index('export function worldRasterPlan'):code.index('export function useWorldSpriteRaster')];assert extract==(HERE/'resources/consumer/exact-used-raster-functions.js').read_text()
expectedHashes={'sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65','world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'}
assert all(sha(HERE/'resources/consumer'/k)==v for k,v in expectedHashes.items())
comparison=[]
original=load(CAND/'consumer/results.json')
for a,b in zip(original['modes'][0]['cases'],original['modes'][1]['cases']):
    comparison.append({'case':a['config']['name'],'screenshot':difference(OBJ/a['screenshot'],OBJ/b['screenshot']),'nativeCanvas':difference(OBJ/a['nativeCanvas'],OBJ/b['nativeCanvas'])})
assert all(c['nativeCanvas']['decodedExact'] for c in comparison)
light=native['lights'];fills=[x for x in light if x['name'].startswith('Equal cardinal fill')];over=[x for x in light if x['name']=='Broad centered overhead'];assert len(fills)==4 and len(over)==1
fillPositions=[[r['matrixWorld'][0][3],r['matrixWorld'][1][3],r['matrixWorld'][2][3]] for r in fills]
lightingSymmetry=(all(abs(math.hypot(*p[:2])-3)<1e-6 and abs(p[2]-1.8)<1e-6 for p in fillPositions) and len({r['energy'] for r in fills})==1 and len({r['size'] for r in fills})==1 and abs(over[0]['matrixWorld'][0][3])<1e-6 and abs(over[0]['matrixWorld'][1][3])<1e-6)
assert lightingSymmetry and len([o for o in native['sceneObjects'] if o['type']=='MESH'])==5
imageNodes=[{'material':n,'node':x['name']} for n,m in native['materials'].items() for x in m['tree']['nodes'] if x['type']=='ShaderNodeTexImage'];assert not imageNodes and not native['resources']['libraries']
closed=all(o.get('nonManifoldEdges',0)==0 and o.get('boundaryEdges',0)==0 and o.get('signedVolume',1)>0 for o in native['objects']);assert closed and native['noTemporalChannels'] and native['staticInvariance'] and native['allNativeMeshesConnectedToGroundedMass'] and all(x['envelopePass'] for x in native['captureRecords'])
report={'asset':'decor-background-rock','candidatePacketSHA256':'20f3fe4297877ecc50affda4574c2ade50482e7068bd9d457fbfb3e6ff2bc54c','sourceSHA256':sha(OBJ/'source/round-01.blend'),'nativeReplayAndPublication':natives,'browserReplay':browser,'submittedTwoModeComparison':comparison,'actualHelperHashes':expectedHashes,'exactRasterExtract':True,'allSixCasesPerModeExact':True,'symmetry':{'equalCardinalFillCount':len(fills),'positions':fillPositions,'oneCenteredOverhead':len(over)==1,'passed':lightingSymmetry},'nativeChecks':{'all4EvaluatedEnvelopes':True,'all5ClosedPositiveVolume':closed,'all5ConnectedToGroundedNativeMass':native['allNativeMeshesConnectedToGroundedMass'],'noImageTexturesOrLinkedLibraries':not imageNodes and not native['resources']['libraries'],'staticOwnerCount':len(native['staticTemporalOwners']),'noTemporalChannels':native['noTemporalChannels'],'staticStateInvariantFrames1_2_12':native['staticInvariance'],'fullCanvasLanczosPublicationExact':True},'limits':['Independent native replay retains1/255 RGB rounding where present; decoded/byte identity is not claimed without measured equality.','Both actual browser modes retained. Native composition and CSS-filtered screenshots remain separate evidence layers.','Contact/base-cap union/old topology/count are not compared as exact locks; finite closed grounded semantics and reconciled envelope are checked.']}
(HERE/'replay-and-contract-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE',natives);print('BROWSER_REPLAY',len(browser),'NATIVE_EXACT',all(r['nativeCanvas']['decodedExact'] for r in browser),'SCREEN_EXACT',all(r['screenshot']['decodedExact'] for r in browser));print('CONTRACT_CHECKS',report['nativeChecks'])
