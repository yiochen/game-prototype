from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;O=P.parent.parent;current=P/'independent-native-audit.json';previous=O/'reviews/round-01-independent/independent-native-audit.json';d=json.loads(current.read_text());old=json.loads(previous.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();adj={m['object']:set() for m in d['topology']}
for q in d['nativeOwnedSurfaceIntersections']:adj[q['a']].add(q['b']);adj[q['b']].add(q['a'])
components=[];left=set(adj)
while left:
 todo=[next(iter(left))];comp=set()
 while todo:
  q=todo.pop()
  if q in comp:continue
  comp.add(q);todo.extend(adj[q]-comp)
 left-=comp;components.append(sorted(comp))
report={'asset':'decor-background-wreck','round':'round-02','candidatePacketSHA256':'778463b2f5fc0c9f47375b66e0524ec164d7c1b0abbc4237643b94d55fd43f2f','currentAudit':{'path':str(current.relative_to(O)),'sha256':sha(current)},'previousAudit':{'path':str(previous.relative_to(O)),'sha256':sha(previous)},'oneSavedRenderCameraLightingFilterColorRecipeMatchesPrevious':d['settings']==old['settings'],'rawRestBoundsUnchanged':d['restRawBounds']==old['restRawBounds'],'evaluatedRestBounds':d['restEvaluatedBounds'],'allOwnedNativeSurfaceIntersectionComponents':components,'all21MeshesOnePhysicallyIntersectingAssembly':len(components)==1 and len(components[0])==21,'allEvaluatedMeshesClosedManifold':all(m['nonManifoldEdges']==0 and m['boundaryEdges']==0 for m in d['topology']),'allNoZeroAreaFaces':all(m['zeroAreaFaces']==0 for m in d['topology']),'noZ0Intersections':all(m['groundIntersectionFaces']==0 for m in d['topology']),'noExternalFilesOrImageCards':not d['externalLibraries'] and not any(m['imageNodes'] for m in d['topology']),'allTemporalChannelsEmpty':not any(m['action'] or m['drivers'] or m['nla'] for m in d['staticOwners']),'staticHoldsEqual':d['staticHoldGeometryMatrixVisibilityEqual'],'limits':'These are independent native technical observations. Complete directly inspected media establish the visual verdict; surface counts, source equality and topology do not waive appearance.'}
(P/'native-regression-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if isinstance(v,bool)},indent=2))
