from pathlib import Path
import shutil,json,math
HERE=Path(__file__).resolve().parent; E=HERE.parent.parent; ROOT=E.parent
AUD=json.loads((E/'source/conveyor-equivalence-audit.json').read_text())
IDS=['belt-corner-n-w','belt-corner-w-n','belt-corner-s-e','belt-corner-e-s','belt-corner-s-w','belt-corner-w-s']
for asset in IDS:
 p=ROOT/asset;S=p/'source';R=S/'resources';R.mkdir(parents=True,exist_ok=True)
 if (S/'round-01.blend').exists():continue
 for f in ['original-library.blend','approved-family.blend']:shutil.copyfile(E/'source/resources'/f,R/f)
 for f in ['source-camera.json','source-assetRecord.json','source-rig.json','catalog-object.json','family-settings.json','family-approval.json']:shutil.copyfile(p/'inputs'/f,R/f)
 row=next(x for x in AUD['rows'] if x['asset']==asset);(R/'native-equivalence.json').write_text(json.dumps(row,indent=2))
 t=(E/'source/build-round01.py').read_text().replace('belt-corner-e-n',asset).replace("s['authored_child_orientation_radians']=0.","s['authored_child_orientation_radians']=float(orient.rotation_euler.z)")
 t=t.replace("'Original angular deck geometry/UV/action;", "'Direct user authorized recipe reuse; exact source angular deck geometry/UV and original stored action explicitly restored; ")
 (S/'build-round01.py').write_text(t)
 t=(E/'source/capture-round01.py').read_text().replace('belt-corner-e-n',asset)
 # Derive physical directed ports after actual source intrinsic rotation is evaluated.
 t=t.replace("rotations={'N':math.pi", "rotations={'N':math.pi",1)
 insert='''\ndef measured_ports():
 uv=deck.data.uv_layers.active;out={}
 for name,U in [('incoming',0),('outgoing',1)]:
  vids=set(deck.data.loops[i].vertex_index for i,x in enumerate(uv.data) if abs(x.uv.x-U)<1e-6);pts=[deck.matrix_world@deck.data.vertices[i].co for i in vids];pt=sum(pts,Vector())/len(pts);normal=Vector((round(pt.x*2),round(pt.y*2),0));out[name]={'point':pt,'tangent':normal*(-1 if name=='incoming' else 1)}
 return out
root.rotation_euler.z=0; bpy.context.view_layer.update();basePorts=measured_ports();moduleSpecs=[]
for name in ['incoming','outgoing']:
 pp=basePorts[name];offset=Vector((round(pp['point'].x*2),round(pp['point'].y*2),0));tangent=pp['tangent'];angle=math.atan2(tangent.y,tangent.x)-math.pi/2;moduleSpecs.append((tuple(offset),angle))
'''
 t=t.replace('def calibration():',insert+'\ndef calibration():')
 start=t.index('def profile(o):');end=t.index('root.rotation_euler.z=0; s.frame_set(1);',start)
 t=t[:start]+'''def profile(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];out={}
 for name,p in basePorts.items():
  pt=p['point'];tan=p['tangent'];vertices=[list(v) for v in pts if abs((v-pt).dot(tan))<1e-6];caps=[f.index for f in me.polygons if all(abs((pts[i]-pt).dot(tan))<1e-6 for i in f.vertices)];out[name]={'vertices':vertices,'capPolygons':caps,'planePoint':list(pt),'travelTangent':list(tan)}
 ev.to_mesh_clear();return out
''' +t[end:]
 t=t.replace("for name,pt,tangent in [('incoming',(.5,0,.64),(-1,0,0)),('outgoing',(0,.5,.64),(0,1,0)),('deck',(0,0,.64),(0,0,0))]:", "for name,pt,tangent in [(name,tuple(p['point']),tuple(p['tangent'])) for name,p in basePorts.items()]+[('deck',(0,0,.64),(0,0,0))]:")
 t=t.replace("for rr,offset,angle in [(fr,(1,0,0),math.pi/2),(fr2,(0,1,0),0)]:", "for rr,(offset,angle) in zip([fr,fr2],moduleSpecs):")
 t=t.replace("'canonicalOffsets':[[0,0,0],[1,0,0],[0,1,0]],'familyRelativeRotations':[90,0]", "'canonicalOffsets':[[0,0,0]]+[list(x[0]) for x in moduleSpecs],'familyRelativeRotations':[math.degrees(x[1]) for x in moduleSpecs]")
 (S/'capture-round01.py').write_text(t)
 # Publish assembly uses the measured physical ports/directions captured in validation.
 t=(E/'source/package-round01.py').read_text().replace('belt-corner-e-n',asset)
 t=t.replace("rots={'N'", "VALID=json.loads((O/'validation.json').read_text());SPECS=list(zip(VALID['assemblyContract']['canonicalOffsets'][1:], [math.radians(a) for a in VALID['assemblyContract']['familyRelativeRotations']]))\nrots={'N'",1)
 t=t.replace("for x,y,a in [(1,0,math.pi/2),(0,1,0)]:", "for offset,a in SPECS:\n   x,y=offset[:2]")
 (S/'package-round01.py').write_text(t)
 t=(E/'source/replay-source.py').read_text();(S/'replay-source.py').write_text(t)
 print(asset,'PREPARED')
