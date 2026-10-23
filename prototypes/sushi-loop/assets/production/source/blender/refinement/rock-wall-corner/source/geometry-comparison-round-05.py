from pathlib import Path
import json
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05'
a=json.loads((B/'candidates/round-04/native-audit.json').read_text());b=json.loads((O/'native-audit.json').read_text());aa={p['name']:p for p in a['meshes']};bb={p['name']:p for p in b['meshes']}
report={'prior':'candidates/round-04/native-audit.json','current':'candidates/round-05/native-audit.json','meshes':{n:{'priorCoordinateSHA256':p['coordinateSHA256'],'currentCoordinateSHA256':bb[n]['coordinateSHA256'],'identicalVertexCoordinates':p['coordinateSHA256']==bb[n]['coordinateSHA256'],'priorFaces':p['faces'],'currentFaces':bb[n]['faces']} for n,p in aa.items()},'note':'The same continuous wrapped construction and native stone field are resampled in surface units; actual changed topology/coordinate hashes are retained. Functional contacts and the capture recipe are measured afresh. No raster changes.'}
(O/'geometry-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
