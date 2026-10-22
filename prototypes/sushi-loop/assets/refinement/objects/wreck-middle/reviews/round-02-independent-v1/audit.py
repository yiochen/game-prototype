"""Independent packet/native/canvas byte and geometry audit; no candidate writes."""
import json,hashlib,math,os
from pathlib import Path
from PIL import Image
import numpy as np
OUT=Path(__file__).resolve().parent; OBJ=OUT.parent.parent; CAND=OBJ/'candidates/round-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
packet=read(CAND/'packet.json'); packetsha=sha(CAND/'packet.json')
assert packetsha=='f371a2509c600cce6b4f53223aa6c0ed546a9db00b79ffcc78dc8fb710b68005'
refs=[*packet['files'].values(),*packet['candidateRenders'].values(),*packet['previews'].values()]
bound={}
for r in refs:
    p=(CAND/r['path']).resolve();assert p.is_file() and sha(p)==r['sha256'],str(p);assert p.stat().st_size<100_000_000
    bound[os.path.relpath(p,OBJ)]=r['sha256']
report={'candidatePacketSHA256':packetsha,'verifiedUniquePacketResources':len(bound),'boundFiles':bound,'frozenInputs':{},'identityPublication':{},'ownRecaptures':{},'browser':{},'opening':{}}
for path,expected in [('brief.json','610d8ea76cedd8e79b007ed00fe72f6874720ea65d2b2692d9268848b0216951'),('inputs/root-native-contract.json','257fadc191e188d52343c2f50b794195bf3ca9a2e58bde8c93943911c6fce0b5'),('inputs/root-preparation-reconciliation-v1.json','e96e84fc22de038d8b442da044f46a54613449a8bbf8ec8404fcae90ed05055f')]:
    assert sha(OBJ/path)==expected;report['frozenInputs'][path]=expected
def diff(a,b):
    aa=np.array(Image.open(a).convert('RGBA'),dtype=np.int16);bb=np.array(Image.open(b).convert('RGBA'),dtype=np.int16);assert aa.shape==bb.shape
    dd=np.abs(aa-bb)
    return {'differentPixels':int(np.any(dd,2).sum()),'maximumRGBA':[int(dd[:,:,k].max()) for k in range(4)],'interiorAlphaLossWhereControlOpaque':int(((bb[:,:,3]==255)&(aa[:,:,3]<255)).sum()),'size':[int(aa.shape[1]),int(aa.shape[0])]}
for d in 'NESW':
    ps=[CAND/'native/static'/d/'000.png',CAND/'frames/static'/d/'000.png',CAND/'atlases'/f'static-{d}.png']
    assert len(set(sha(p) for p in ps))==1
    report['identityPublication'][d]=sha(ps[0]);report['ownRecaptures'][d]=diff(OUT/'recapture'/f'{d}.png',ps[0])
native=read(OUT/'native-inspection.json');report['finiteSavedSource']={k:native[k] for k in ['sourceSHA256','bounds','maximumFiniteXYViolation','actions','armatures','images','lights','world']}
report['finiteSavedSource']['support']={k:v for k,v in native['support'].items() if k!='triangles'}
report['finiteSavedSource']['canonicalFieldEquality']={k:v['finiteDescriptorsEqual'] for k,v in native['canonicalCollars'].items()}
contract=read(OBJ/'inputs/root-native-contract.json');capchecks=[]
for cap in native['caps']:
    sec=next(s for s in contract['finitePorts'][cap['side']]['sections'] if cap['rail'] in s['name'] or cap['rail']=='rear' and 'back_hull' in s['name'])
    expected=[v[1:] for v in sec['authoredRingVertices']];loop=[v[1:] for v in cap['loop']]
    while len(loop)>4:
        removed=False
        for i in range(len(loop)):
            a,b,c=loop[i-1],loop[i],loop[(i+1)%len(loop)]
            if abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))<1e-10:
                loop.pop(i);removed=True;break
        if not removed:break
    if cap['side']=='W':expected.reverse()
    match=len(loop)==4 and any(all(max(abs(loop[(i+j)%4][k]-expected[i][k]) for k in [0,1])<1e-6 for i in range(4)) for j in range(4))
    capchecks.append({'side':cap['side'],'rail':cap['rail'],'orderedProfileMatches':match,'area':cap['area'],'normal':cap['normal']})
report['finiteSavedSource']['caps']=capchecks
assert all(r['orderedProfileMatches'] for r in capchecks)
assert all(report['finiteSavedSource']['canonicalFieldEquality'].values())
assert native['support']['insideFiniteLowestRectangle'] and not native['support']['z0Geometry'] and abs(native['support']['area']-.36)<1e-6
expected_helpers={'world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
report['browser']['helpers']={}
for name,expected in expected_helpers.items():
    p=OBJ/'source/round01-resources'/name;assert sha(p)==expected;report['browser']['helpers'][name]=expected
results=read(CAND/'consumer/results.json'); report['browser']['cases']=[]
for c in results['cases']:
    expected={'headless':True,'channel':'chromium'} if c['mode']=='full-chromium' else {'headless':True}
    assert c['launch']==expected and c['errors']==[]
    hashes=c['inputHashes']
    for path,h in hashes.items():
        if path.startswith('atlas-'):p=CAND/'atlases'/('static-'+path[-1]+'.png')
        elif path.startswith('connected-native-control-'):p=CAND/'connected-native'/(path[-1]+'.png')
        else:p=OBJ/'source'/path
        assert sha(p)==h,str(p)
    prefix=c['mode']+'-'+c['id']; entry={k:c[k] for k in ['mode','id','launch','browserVersion','browserExecutable','actualBrowserVersion','viewport','deviceScaleFactor','errors']}
    entry['nativeComparisons']={}
    for d in 'NESW':
        entry['nativeComparisons'][d]=diff(CAND/'consumer'/(prefix+'-'+d+'-independent-native.png'),CAND/'consumer'/(prefix+'-'+d+'-connected-native-control-native.png'))
    report['browser']['cases'].append(entry)
assert len(report['browser']['cases'])==8
report['browser']['crossModeCSS']=[]
for case in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
    report['browser']['crossModeCSS'].append({'case':case,**diff(CAND/'consumer'/('full-chromium-'+case+'-css.png'),CAND/'consumer'/('bundled-headless-shell-'+case+'-css.png'))})
    for d in 'NESW':
        for kind in ['independent','connected-native-control']:
            comparison=diff(CAND/'consumer'/('full-chromium-'+case+'-'+d+'-'+kind+'-native.png'),CAND/'consumer'/('bundled-headless-shell-'+case+'-'+d+'-'+kind+'-native.png'))
            assert comparison['differentPixels']==0
report['browser']['all32NativeCanvasesCrossModeDecodedEqual']=True
def spans(a):
    starts=[];start=None
    for i,v in enumerate(list(a)+[False]):
        if v and start is None:start=i
        elif not v and start is not None:starts.append([start,i-1]);start=None
    return starts
n=np.array(Image.open(CAND/'frames/static/N/000.png').convert('RGBA'))
report['opening']['singleNAlpha0RunsWithinAuthoredWidth']={str(y):[[a+64,b+64] for a,b in spans(n[y,64:320,3]==0)] for y in [411,412,413,414]}
ind=np.array(Image.open(CAND/'independent-repeated/N.png').convert('RGBA'))
con=np.array(Image.open(CAND/'connected-native/N.png').convert('RGBA'))
report['opening']['trueJoinRows']=[{'xy':[x,y],'independentAlpha':int(ind[y,x,3]),'connectedAlpha':int(con[y,x,3])} for y in [412,413] for x in [300,319,320,340,566,575,576,586]]
report['opening']['meaning']='Both zero: geometric opening. Relative opaque-control alpha-loss equality does not prove opaque coverage or visual acceptability.'
(OUT/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'verifiedUniquePacketResources':len(bound),'ownRecaptures':report['ownRecaptures'],'support':report['finiteSavedSource']['support'],'opening':report['opening'],'browserCases':len(results['cases']),'browserVersions':list(set(c['browserVersion'] for c in results['cases']))},indent=2))
