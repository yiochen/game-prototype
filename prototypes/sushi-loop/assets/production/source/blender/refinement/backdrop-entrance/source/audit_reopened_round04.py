from pathlib import Path
src=Path(__file__).with_name('capture_validate_round04.py').read_text()
# Reuse exact audit routines, without repeating or replacing any selected hero or joined render.
exec(compile(src.split('# This script starts')[0],str(Path(__file__).with_name('capture_validate_round04.py')),'exec'))
v=json.loads((R/'validation.json').read_text());ga=audit_collection(G);wa=audit_collection(W)
v['assetAudit']=ga;v['wallContextAudit']=wa;v['protectedJoinPlanes']['geometryAndMatricesUnchanged']=all(o.get('protectedProfileUnchanged',True) for a in [ga,wa] for o in a['objects'].values())
sc.render.resolution_x=576;sc.render.resolution_y=1344;cam.data.ortho_scale=1.5;cam.data.shift_y=recipe['camera']['shift'][1]*4.5/1.5
sc.view_layers[0].update();v['wallContextCapture']={'camera':camera_record(),'rootMatrix':matrix(wr),'registeredContact':project((0,-.5,0)),'path':'candidates/round-04/wall-context-S.png','status':'context-only; separate wall approval required','collectionVisibility':'source collection explicitly unhidden for context capture and measured after dependency-graph update','recipe':'source/render_wall_context_round04.py'}
v['wallContextAudit']['captureCalibration']={'nativePixelsPerWorldUnitX':project((1,-.5,0))[0]-project((0,-.5,0))[0],'frontContactAnchor':project((0,-.5,0))}
v['checks']['wallContextPitchError']=abs((project((1,-.5,0))[0]-project((0,-.5,0))[0])-384)
v['checks']['wallContextAnchorErrorPixels']=math.dist(project((0,-.5,0)),[288,1248])
v['renderer']['reopenedNote']='Scene device setting is recorded; reopened process hardware utilization was not independently queried. Selected hero build configured METAL explicitly.'
v['camera']['sensorFit']=cam.data.sensor_fit
v['wallContextCapture']['camera']['sensorFit']=cam.data.sensor_fit
(R/'validation.json').write_text(json.dumps(v,indent=2));print('ACTUAL_REOPEN_AUDIT',v['checks'],v['protectedJoinPlanes'])
