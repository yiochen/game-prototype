from pathlib import Path
import subprocess,json,shutil,math,hashlib
E=Path(__file__).resolve().parents[2];ROOT=E.parent;PY='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';rots={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def run(args,log):
 with log.open('w') as stream:r=subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT)
 if r.returncode or 'Traceback' in log.read_text() or 'Parse Error' in log.read_text():raise RuntimeError(str(log))
for asset in [f'belt-{k}-{d}' for k in ['start','end'] for d in ['n','e','s','w']]:
 P=ROOT/asset;S=P/'source';O=P/'candidates/round-01'
 if (O/'packet.json').exists():continue
 V=json.loads((O/'validation.json').read_text());modules={}
 for d,r in rots.items():
  m=[(0,0,d,'frames')]
  for off,a in zip(V['assemblyContract']['canonicalOffsets'][1:],V['assemblyContract']['familyRelativeRotations']):
   x,y=off[:2];xx=round(x*math.cos(r)-y*math.sin(r));yy=round(x*math.sin(r)+y*math.cos(r));rr=r+math.radians(a);fd=min(rots,key=lambda k:abs(math.atan2(math.sin(rots[k]-rr),math.cos(rots[k]-rr))));m.append((xx,yy,fd,'family-frames'))
  modules[d]=[{'kind':k,'direction':f,'offset':[256+x*256,256-y*256]} for x,y,f,k in sorted(m,key=lambda v:-v[1])]
 (S/'consumer-modules.json').write_text(json.dumps(modules,indent=2))
 (S/'quick-consumer.mjs').write_text((E/'source/batch/quick-consumer-template.mjs').read_text().replace('ASSET_ID',asset))
 for source,dest in [('verify_native_template.py','verify-native.py'),('measure_template.py','measure-proof.py'),('finalize_template.py','finalize-records.py')]:shutil.copyfile(E/'source/batch'/source,S/dest)
 run(['blender','-b','-t','2','--python',str(S/'verify-native.py')],S/'verify-native.log')
 for name in ['package-round01','playback-evidence']:run([PY,str(S/(name+'.py'))],S/(name+'.log'))
 run(['node',str(S/'quick-consumer.mjs')],S/'quick-consumer.log')
 if asset in ['belt-start-n','belt-end-n']:
  G=S/'godot-probe';(G/'runtime').mkdir(parents=True,exist_ok=True);(G/'config.json').write_text(json.dumps({'modules':modules},indent=2));shutil.copyfile(E/'source/batch/gpu_quick_template.gd',G/'bench.gd');shutil.copyfile(E/'source/godot-probe/project.godot',G/'project.godot');h={}
  for name in ['native_pixel_compositor.gd','native_world_layer.gd','native_reduce2.gdshader','native_present.gdshader']:
   src=ROOT.parents[2]/'godot/scripts'/name
   # ROOT=.../assets/refinement/objects; native Godot folder is sushi-loop/godot.
   src=ROOT.parents[2]/'godot/scripts'/name
   if not src.exists():src=ROOT.parents[2]/'godot/scripts'/name
   shutil.copyfile(src,G/'runtime'/name);h[name]={'productionPath':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
  (G/'runtime-hashes.json').write_text(json.dumps(h,indent=2));run(['godot','--path',str(G),'--script','bench.gd'],G/'run.log');assert (O/'godot-consumer/render-record.json').exists()
 run([PY,str(S/'measure-proof.py')],S/'measure-proof.log');c=json.loads((O/'technical-checks.json').read_text());assert c['actualCurrentConsumer']['allReady'] and not c['actualCurrentConsumer']['errors'] and c['actualCurrentConsumer']['joinAlphaDifferentPixels']==0 and c['actualCurrentConsumer']['joinRGBOver1Pixels']==0;assert c['nativeContinuity']['independentVsUnbroken']['joinDifferentAlphaPixels']==0 and c['nativeContinuity']['independentVsUnbroken']['joinRGBOver1Pixels']==0;assert all(s['RGBAOver1Pixels']==0 and s['alphaDifferentPixels']==0 for s in c['closurePixelResiduals'].values())
 if c['actualCurrentGodot']:assert c['actualCurrentGodot']['joinAlphaDifferentPixels']==0 and c['actualCurrentGodot']['joinRGBOver1Pixels']==0
 run([PY,str(S/'finalize-records.py')],Path('/tmp')/(asset+'-finalize.log'));print('READY',json.dumps(json.loads((O/'READY.json').read_text())),flush=True)
