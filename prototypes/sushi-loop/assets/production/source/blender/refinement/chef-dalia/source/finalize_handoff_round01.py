"""Bind completed browser QA and measured zero-area summary without changing native art bytes."""
import json,hashlib
from pathlib import Path
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
rows=json.loads((OUT/'native-frames.json').read_text());v=json.loads((OUT/'complete-validation.json').read_text());assert v['ok'] and len(rows)==192
assert max(g['zeroAreaPolygons'] for r in rows for g in r['geometry'].values())==0
browser={'method':'Actual local in-app browser through cua_repl, native media DOM properties and screenshot inspection','page':'candidates/round-01/playback.html','nativeClipPlayers':16,'sourceAndCandidateContextPlayers':8,'allMediaReadyState':4,'allMediaErrorCodes':None,'allDurationsSeconds':1,'nativeDecodedSize':[384,640],'contextDecodedSize':[512,640],'loopingNativePlayersObservedContinuing':12,'nonloopNativeLoadPlayersObservedEnded':4,'nonloopContextPlayersObservedEnded':8,'allNonloopEndTimesSeconds':1,'frameRateAndFrameCountProof':'playback-validation.json: each ffprobe12/1fps, twelve decoded frames, duration1second','sampling':'Clicked Play all from frame00, inspected actual playback and decoded DOM values, later observed loop continuing and all loads ended, then paused all','nativeFrameOrAtlasEdits':False}
write(OUT/'browser-playback-qa.json',browser)
v['browserPlaybackQA']='candidates/round-01/browser-playback-qa.json';v['evaluatedZeroAreaFaceMaximum']=0;v['evaluatedNativeMeshCount']=len(rows[0]['geometry']);v['topologyScout']='candidates/round-01/topology-scout.json';write(OUT/'complete-validation.json',v)
d=json.loads((BASE/'delivery.json').read_text());d['resources']['browserPlaybackQA']='candidates/round-01/browser-playback-qa.json';d['resources']['topologyScout']='candidates/round-01/topology-scout.json';d['resources']['envelopeValidation']='candidates/round-01/envelope-validation.json';d['resources']['finalize_handoff_round01.py']='source/finalize_handoff_round01.py';write(BASE/'delivery.json',d)
files=[P/'round-01.blend',P/'recipe-round01.json',OUT/'complete-validation.json',BASE/'delivery.json']
write(OUT/'editor-handoff-hashes.json',{'status':'Ready for coordinator sealing and independent judge review; visual verdict pending','files':{p.relative_to(BASE).as_posix():sha(p) for p in files},'nativeFrames':192,'originalLayoutAtlases':16,'native12fpsPlaybacks':16,'allFramesLightGrayDarkIntendedAndEnlargedSheets':96,'sourceAndCandidateLoadContextPlaybacks':8})
print(json.dumps({'ok':v['ok'],'projectSHA256':sha(P/'round-01.blend'),'deliverySHA256':sha(BASE/'delivery.json'),'restHeight':v['restHeight'],'nativeFrames':192,'atlases':16,'nativePlaybacks':16,'frameSheets':96,'zeroAreaFaceMaximum':0,'sourceIntegrity':v['originalSourceIntegrity']['unchanged']},indent=2))
