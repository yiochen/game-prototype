from PIL import Image,ImageChops
import pathlib,json,hashlib,collections
B=pathlib.Path(__file__).resolve().parent.parent;C=B/'candidates/round-01';packet=json.loads((C/'packet.json').read_text());fail=[];bounds=[];sheets=[];atlas=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def composite(im):
 bg=Image.new('RGBA',im.size,'#e5e2d8');bg.alpha_composite(im);return bg.convert('RGB')
for prefix,clips in [('', ['idle','work','hold','load']),('runtimeVariants/',['hold-cucumber','load-cucumber'])]:
 p=C/prefix
 rows=json.loads((p/'native-frames.json').read_text());keys={(r['clip'],r['direction'],r['index']) for r in rows}
 for clip in clips:
  overview=Image.open(p/'contact-sheets'/f'{clip}-all48.png').convert('RGB')
  for di,d in enumerate(['N','E','S','W']):
   sheet=Image.open(p/'contact-sheets'/f'{clip}-{d}.png').convert('RGB');at=Image.open(p/'atlases'/f'{clip}-{d}.png').convert('RGBA')
   for i in range(12):
    path=p/'frames'/f'{clip}-{d}'/f'{i:03}.png';im=Image.open(path).convert('RGBA');rec=next(r for r in rows if (r['clip'],r['direction'],r['index'])==(clip,d,i));rel=path.relative_to(C).as_posix()
    if sha(path)!=rec['sha256'] or im.size!=(384,640):fail.append(rel+' hash/dimensions')
    if im.tobytes()!=at.crop(((i%6)*384,(i//6)*640,(i%6+1)*384,(i//6+1)*640)).tobytes():fail.append(rel+' atlas pixels')
    logical=composite(im.resize((192,320),Image.Resampling.LANCZOS));crop=sheet.crop(((i%6)*192,(i//6)*352+28,(i%6+1)*192,(i//6)*352+348))
    if logical.tobytes()!=crop.tobytes():fail.append(rel+' sheet pixels')
    small=composite(im.resize((96,160),Image.Resampling.LANCZOS));ocrop=overview.crop((i*96,di*176+16,(i+1)*96,di*176+176))
    if small.tobytes()!=ocrop.tobytes():fail.append(rel+' overview pixels')
    bounds.append({'path':rel,'alphaBounds':im.getbbox()})
   sheets.append((p/'contact-sheets'/f'{clip}-{d}.png').relative_to(C).as_posix());atlas.append((p/'atlases'/f'{clip}-{d}.png').relative_to(C).as_posix())
  sheets.append((p/'contact-sheets'/f'{clip}-all48.png').relative_to(C).as_posix())
hashes=[]
for section in ['files','candidateRenders','previews']:
 for k,v in packet[section].items():
  path=C/v['path'];hashes.append({'section':section,'key':k,'path':v['path'],'matches':path.exists() and sha(path)==v['sha256']})
result={'packetSHA256':sha(C/'packet.json'),'boundFileCount':len(hashes),'allPacketHashesMatch':all(x['matches'] for x in hashes),'rawFramesVerified':len(bounds),'sheetFrameRegionsVerified':len(bounds)*2,'verifiedContactSheets':sheets,'atlasesVerified':atlas,'failures':fail,'alphaBounds':bounds}
(B/'reviews/round-01-pixel-evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['verifiedContactSheets','atlasesVerified','alphaBounds']}))
