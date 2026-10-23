"""Assemble inspection-only sheets and measured records; never edit art PNGs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import json, hashlib, math, sys, platform
B=Path(__file__).resolve().parent;O=B.parent;C=O/'candidates/round-01';P=C/'previews';P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def load(p):return Image.open(p).convert('RGBA')
def bg(im,color='#808080'):
    out=Image.new('RGBA',im.size,color);out.alpha_composite(im);return out.convert('RGB')
def pack(items,columns=2,padding=12):
    widths=[max(280,max(item[1].width for item in items[i::columns])) if items[i::columns] else 280 for i in range(columns)]
    rows=[items[i:i+columns] for i in range(0,len(items),columns)];heights=[max(v[1].height for v in row)+30 for row in rows]
    out=Image.new('RGB',(sum(widths)+(columns+1)*padding,sum(heights)+(len(rows)+1)*padding),'#ecebe5');draw=ImageDraw.Draw(out);records=[];y=padding
    for row,h in zip(rows,heights):
        x=padding
        for i,(label,im,record) in enumerate(row):
            draw.text((x,y),label,fill='#17354a');out.paste(im,(x,y+24));records.append({'label':label,'sheetRect':[x,y+24,im.width,im.height],**record});x+=widths[i]+padding
        y+=h+padding
    return out,records
coverage=[];previews={}
def save(name,im,tiles):
    path=P/(name+'.png');im.save(path);previews[name]=str(path.relative_to(O));coverage.append({'preview':str(path.relative_to(O)),'sha256':sha(path),'size':list(im.size),'tiles':tiles});return path
def rel(p):return str(Path(p).relative_to(O))

# Hero sheet uses every complete native frame at1:1 pixel scale.
items=[]
for d in 'NESW':
    path=C/f'frames/static/{d}/000.png';items.append((d+' direct native2x384x704 / exact complete frame',bg(load(path),'#f6f6f2'),{'sources':[rel(path)],'sourceRect':[0,0,384,704],'resampling':False,'role':'exact hero pixel coverage over display background'}))
im,tiles=pack(items,4);save('four-view-sheet',im,tiles)

# Original and candidate remain equally registered, target/style separated.
items=[('Original / exact registered frame',bg(load(B/'resources/reference/original.png'),'#f6f6f2'),{'sources':[rel(B/'resources/reference/original.png')],'resampling':False}),('Candidate S / exact registered frame',bg(load(C/'frames/static/S/000.png'),'#f6f6f2'),{'sources':[rel(C/'frames/static/S/000.png')],'resampling':False})]
target=load(B/'resources/reference/target.png');target.thumbnail((384,500),Image.Resampling.LANCZOS);style=load(B/'resources/reference/style.png');style.thumbnail((192,340),Image.Resampling.LANCZOS)
panel=Image.new('RGB',(400,704),'#f6f6f2');panel.paste(bg(target,'#f6f6f2'),(0,0));panel.paste(bg(style,'#f6f6f2'),(200,360));items.append(('Fixed target and style / reference thumbnails only',panel,{'sources':[rel(B/'resources/reference/target.png'),rel(B/'resources/reference/style.png')],'resampling':'reference thumbnails only; no registration claim'}))
im,tiles=pack(items,3);save('registered-source-target-comparison',im,tiles)

# Full native combined frames at logical display scale, with original resources
# retained separately. No view-specific crop or fitting.
for kind in ['direct-canonical-to-end','full-family-L']:
    items=[]
    for d in 'NESW':
        path=C/f'native/contexts/{kind}-{d}.png';im=load(path).resize((832,992),Image.Resampling.LANCZOS)
        items.append((kind+' '+d+' / complete native assembly at logical scale',bg(im,'#f6f6f2'),{'sources':[rel(path)],'sourceRect':[0,0,1664,1984],'displayScale':.5,'derivation':'overview display only; full untouched native source retained'}))
    im,tiles=pack(items,4);save('native-'+kind+'-all4',im,tiles)
previews['full-family-L']=previews['native-full-family-L-all4']

PROFILE=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)]
ANGLE={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
def contact_boxes(record):
    # Actual planned contacts, ordered profile plus .08 surfaces on both sides.
    contacts=[(-.5,0,1,0,0,1)] if record['kind']=='direct-canonical-to-end' else [(-2,1.5,0,-1,1,0),(-2,.5,0,-1,1,0),(-1.5,0,1,0,0,1),(-.5,0,1,0,0,1)]
    a=ANGLE[record['d']];co=math.cos(a);si=math.sin(a);zoom=record['size']/128;r=record['rootPhase'];pan=record['panPhase'];boxes=[]
    for x,y,ax,ay,wx,wy in contacts:
        points=[]
        for t in [-.08,.08]:
            for width,z in PROFILE:
                xx=x+ax*t+wx*width;yy=y+ay*t+wy*width;rx=xx*co-yy*si;ry=xx*si+yy*co
                points.append((12+(416+rx*128+r)*zoom+pan,12+(560-ry*128-z*89.6+r)*zoom+pan))
        boxes.append((math.floor(min(p[0] for p in points))-4,math.floor(min(p[1] for p in points))-4,math.ceil(max(p[0] for p in points))+4,math.ceil(max(p[1] for p in points))+4))
    return boxes
def source_extent_box(record):
    sprites=record['sprites'];zoom=record['size']/128;pan=record['panPhase'];left=min(s['x'] for s in sprites);top=min(s['y'] for s in sprites);right=max(s['x']+s['width'] for s in sprites);bottom=max(s['y']+s['height'] for s in sprites)
    return(math.floor(12+(left+416)*zoom+pan)-3,math.floor(12+(top+560)*zoom+pan)-3,math.ceil(12+(right+416)*zoom+pan)+3,math.ceil(12+(bottom+560)*zoom+pan)+3)
def css_join_strip(record,bgname):
    src=O/record['media']['css-'+bgname];im=load(src);offset=record['display']['width']+16;pieces=[];mapping=[]
    for index,box in enumerate(contact_boxes(record)):
        a=im.crop(box).convert('RGB');ib=(box[0]+offset,box[1],box[2]+offset,box[3]);b=im.crop(ib).convert('RGB');tile=Image.new('RGB',(a.width+b.width+4,max(a.height,b.height)+18),'#ecebe5');draw=ImageDraw.Draw(tile);draw.text((0,0),f'{index+1}: N / I',fill='#17354a');tile.paste(a,(0,18));tile.paste(b,(a.width+4,18));pieces.append(tile);mapping.append({'contactIndex':index,'source':str(src.relative_to(O)),'nativeSourceRect':box,'independentSourceRect':ib})
    out=Image.new('RGB',(sum(p.width for p in pieces)+8*(len(pieces)-1),max(p.height for p in pieces)),'#ecebe5');x=0
    for piece,m in zip(pieces,mapping):out.paste(piece,(x,0));m['tileRect']=[x,0,piece.width,piece.height];x+=piece.width+8
    return out,mapping

reports={b:read(C/f'consumer/{b}-results.json') for b in ['full-chromium','headless-shell']}
for backend,report in reports.items():
    for kind in ['direct-canonical-to-end','full-family-L']:
        # Full context at native consumer128/phone32 for representative integer
        # and fractional phases. All remaining cases appear in contact sheets.
        items=[]
        for d in 'NESW':
            for size in [128,32]:
                for phase in [0,7]:
                    r=next(v for v in report['records'] if (v['kind'],v['d'],v['size'],v['phase'])==(kind,d,size,phase));path=O/r['media']['css-gray'];src=load(path);box=source_extent_box(r);w=r['display']['width'];other=(box[0]+w+16,box[1],box[2]+w+16,box[3]);a=src.crop(box).convert('RGB');b=src.crop(other).convert('RGB');tile=Image.new('RGB',(a.width+b.width+6,a.height),'#808080');tile.paste(a,(0,0));tile.paste(b,(a.width+6,0))
                    items.append((f'{d} cell{size} phase{phase} / native left, independent right',tile,{'sources':[str(path.relative_to(O))],'sourceRects':[box,other],'caseId':r['id'],'resampling':False,'cropRole':'inspection excerpt from union of registered complete source rectangles, never alpha fitting'}))
        im,tiles=pack(items,2);name=backend+'-'+kind+'-context';save(name,im,tiles)
        if backend=='full-chromium' and kind=='direct-canonical-to-end':previews['repeated']=previews[name]
        for d in 'NESW':
            for size in [128,32]:
                items=[]
                for phase in range(8):
                    r=next(v for v in report['records'] if (v['kind'],v['d'],v['size'],v['phase'])==(kind,d,size,phase))
                    for background in ['light','gray','dark']:
                        im,mapping=css_join_strip(r,background);items.append((f'phase{phase} root{r["rootPhase"]}/pan{r["panPhase"]} {background}',im,{'caseId':r['id'],'sources':[r['media']['css-'+background]],'contacts':mapping,'resampling':False,'cropRole':'exact planned finite ordered-profile plus .08 adjacent collar,4px inspection margin'}))
                im,tiles=pack(items,3);save(f'{backend}-{kind}-{d}-cell{size}-all-phases',im,tiles)

# Comparison-only extent diagnostics are visibly separate from all actual CSS.
diag_reports={b:read(C/f'extent-diagnostic/{b}-results.json') for b in reports}
for backend,report in diag_reports.items():
    actual={r['id']:r for r in reports[backend]['records']}
    for kind in ['direct-canonical-to-end','full-family-L']:
        items=[]
        for d in 'NESW':
            for size in [128,32]:
                r=next(v for v in report['records'] if (v['kind'],v['d'],v['size'],v['phase'])==(kind,d,size,7));base=actual[r['id']];paths=[O/base['media']['native'],O/r['comparisonPath'],O/base['media']['independent']];images=[load(p) for p in paths];pieces=[];maps=[]
                for index,box in enumerate(contact_boxes(base)):
                    parts=[bg(im.crop(box)) for im in images];tile=Image.new('RGB',(sum(p.width for p in parts)+8,max(p.height for p in parts)+18),'#ecebe5');dr=ImageDraw.Draw(tile);dr.text((0,0),f'{index+1}: actual / diagnostic / I',fill='#17354a');x=0
                    for p in parts:tile.paste(p,(x,18));x+=p.width+4
                    pieces.append(tile);maps.append({'contactIndex':index,'sourceRect':box,'sources':[str(p.relative_to(O)) for p in paths]})
                tile=Image.new('RGB',(sum(p.width for p in pieces)+8*(len(pieces)-1),max(p.height for p in pieces)),'#ecebe5');x=0
                for p in pieces:tile.paste(p,(x,0));x+=p.width+8
                items.append((f'{d} cell{size} r.25/p.75 / comparison only',tile,{'caseId':r['id'],'contacts':maps,'sources':[str(p.relative_to(O)) for p in paths],'resampling':False,'scope':'Actual raw retained; diagnostic changes only transparent source extent and is never published.'}))
        im,tiles=pack(items,2);save(backend+'-'+kind+'-extent-diagnostic',im,tiles)

# Explicit finite contact rectangles and all case coverage let a judge trace
# every sheet excerpt back to its unmodified whole CSS screenshot.
write(C/'preview-coverage-map.json',{'pathBase':'object-root','scope':'Every768 actual CSS case is represented at each exact planned finite contact; complete-context integer/fractional overviews supplement these. Sheet crops/overviews are inspection media only, never exported sprites.','previews':coverage,'heroAliasCoverage':{d:{'path':f'candidates/round-01/frames/static/{d}/000.png','sameBytesNative':f'candidates/round-01/native/static/{d}/000.png','sameBytesAtlas':f'candidates/round-01/atlases/static-{d}.png','coveredBy':previews['four-view-sheet']} for d in 'NESW'},'previewAliases':{'full-family-L':previews['full-family-L'],'repeated':previews['repeated']}})
write(B/'preview-index.json',{'previews':previews})

audit=read(C/'geometry-audit.json');native=read(C/'native-contract-audit.json');capt=read(C/'capture-measurements.json');replay=[]
for d in 'NESW':
    p=C/f'frames/static/{d}/000.png';a=load(p);b=load(C/f'replay/native/static/{d}/000.png');diff=ImageChops.difference(a,b);count=sum(v!=0 for v in diff.tobytes());bounds=a.getchannel('A').getbbox()
    replay.append({'direction':d,'publishedSHA256':sha(p),'replaySHA256':sha(C/f'replay/native/static/{d}/000.png'),'differentRGBAComponents':count,'maximumRGBAComponentDelta':max(v[1] for v in diff.getextrema()),'alphaBounds':bounds,'nativeBytesEqual':sha(p)==sha(C/f'native/static/{d}/000.png'),'atlasBytesEqual':sha(p)==sha(C/f'atlases/static-{d}.png'),'noFrameEdgeTouch':bounds[0]>0 and bounds[1]>0 and bounds[2]<384 and bounds[3]<704})
write(C/'saved-source-replay.json',{'sourceSHA256':sha(B/'round-01.blend'),'capturesFromReopenedSavedSource':True,'records':replay})
allrows=[r for report in reports.values() for r in report['records']];diagrows=[r for report in diag_reports.values() for r in report['records']];controls=[r for report in diag_reports.values() for r in report['controls']]
consumer_summary={'actualCases':len(allrows),'actualCSSBackgroundCases':len(allrows)*3,'actualBrowserVersions':{b:v['browserVersion'] for b,v in reports.items()},'actualLaunchOptions':{b:v['launchOptions'] for b,v in reports.items()},'errors':{b:v['errors'] for b,v in reports.items()},'maximumMetrics':{b:{k:max(r['metrics'][k] for r in report['records']) for k in report['records'][0]['metrics']} for b,report in reports.items()},'localVisibleJudgment':'Pending original independent judge; no numeric-only seam waiver. All raw actual outputs and precise contact excerpts retained, with native field audit separately bound.','residualSeparation':'Broad finite-area lights/source extent/browser raster and local connection appearance remain distinct. Whole-image RGB/alpha identity is not asserted.'}
write(C/'consumer-summary.json',consumer_summary)
extent_summary={'trigger':'Actual fullChromium maxalpha255/maxopaqueRGB209 versus shell maxalpha7/maxopaqueRGB65; source-extent component assessed only after these raw discrepancies occurred.','cases':len(diagrows),'controls':len(controls),'visiblePixelsDiscarded':sum(v['discardedVisiblePixels'] for v in controls),'maximumIntegerRestorationPixelDifferences':max(v['integerRestoration']['differingPixels'] for v in controls),'maximumActualAlpha':max(v['actualConsumer']['maxAlphaDelta'] for v in diagrows),'maximumDiagnosticAlpha':max(v['comparisonOnlyEqualExtent']['maxAlphaDelta'] for v in diagrows),'maximumActualOpaqueRGB':max(v['actualConsumer']['maxOpaqueRGBDelta'] for v in diagrows),'maximumDiagnosticOpaqueRGB':max(v['comparisonOnlyEqualExtent']['maxOpaqueRGBDelta'] for v in diagrows),'maximumActualLocalRGB':max(v['actualConsumer']['localMaxRGBDelta'] for v in diagrows),'maximumDiagnosticLocalRGB':max(v['comparisonOnlyEqualExtent']['localMaxRGBDelta'] for v in diagrows),'limits':'Same required fixtures/configurations/single capture policy. Known frozen comparison method only. All original actual images remain unchanged; comparison crop is not a runtime fix, publication crop, numeric seam waiver or visual approval.'}
write(C/'extent-diagnostic/summary.json',extent_summary)
checks=dict(native['checks']);checks.update({'savedSourceReplayRGBAExactAll4':all(v['differentRGBAComponents']==0 for v in replay),'publishedNativeAtlasBytesExactAll4':all(v['nativeBytesEqual'] and v['atlasBytesEqual'] for v in replay),'allHeroesInsideFrame':all(v['noFrameEdgeTouch'] for v in replay),'all256NativeIndependentPairsAnd768CSSCases':len(allrows)==256 and len(allrows)*3==768,'bothActualBrowserModesNoPageErrors':all(not v['errors'] for v in reports.values()),'noAnalyticalFiniteCoreInteriorAlphaLoss':all(r['metrics']['nativeInteriorAlphaLoss']==r['metrics']['independentInteriorAlphaLoss']==0 for r in allrows),'noAnalyticalJoinedCollarInteriorAlphaLoss':all(r['metrics']['localJoinNativeAlphaLoss']==r['metrics']['localJoinIndependentAlphaLoss']==0 for r in allrows),'diagnosticNoVisibleSourceDiscard':all(v['discardedVisiblePixels']==0 for v in controls),'diagnosticExactIntegerRestoration':all(v['integerRestoration']['differingPixels']==0 for v in controls),'initialUnchanged':sha(B/'initial-observations.json')=='b0df6ff709adaa58a7db6f2a86bb8fc841e948092d6cf91a745aa99327f96fe5'})
write(C/'validation.json',{'asset':'reef-end','round':'round-01','status':'native and evidence checks complete; original independent visual review pending','sourceSHA256':sha(B/'round-01.blend'),'checks':checks,'allChecksPassed':all(checks.values()),'nativeValidation':'candidates/round-01/capture-measurements.json','captureRecords':capt['captureRecords'],'nativeContractAudit':'candidates/round-01/native-contract-audit.json','consumerEvidence':'candidates/round-01/consumer-summary.json','extentDiagnostic':'candidates/round-01/extent-diagnostic/summary.json','visualApproval':False,'limits':['Technical checks do not decide all-view appearance or visible local connection quality.','Native connected vs independently captured finite-area-light/context RGB residuals and original actual browser contour residuals remain retained. No wholeimage identity or seam waiver.','The rejected initial inactive-library transform measurements and unsubmitted triangulated-collar draft remain clearly labeled; final native audit uses independently evaluated saved source.']})
asset={'id':'reef-end','projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'scale':2,'footprint':[1,1],'height':.68,'measuredGeometryBounds':audit['bounds'],'finiteGroundRectangle':audit['finiteGroundRectangle'],'finiteGroundArea':audit['groundArea'],'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True}},'sockets':{},'ports':[{'direction':'W','position':[-.5,0,0],'profile':'reef-section-v1','normal':[-1,0,0]}],'nonblocking':False,'depth_layer':'world','directions':list('NESW'),'artStyle':{'revision':'warm-soft-native-refinement-reef-end-round01','lighting':'Exact canonical middle02 native light/world graphs, Background Strength.32 and centered100W/4cardinal45W finite area lights','normalMaterialField':'Full exact canonical .08 W collar original native polygons/triangles/materials, zero normalized-post-interpolation field delta','publication':'Exact direct-native2x384x704/filter.01; no reduction'},'nativeSourceSHA256':sha(B/'round-01.blend')}
write(C/'assetRecord.json',asset)
write(C/'rig.json',{'assetId':'reef-end','fps':12,'static':True,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'actions':[],'geometryOwners':[p['name'] for p in audit['parts']],'shaderChannels':[]}},'armatures':[],'footprint':[1,1],'projection':'top-down-oblique-square-grid','groundRootObject':'reef-end__root','sockets':{},'actionCount':0,'sourceFiles':{'reproduce-round-01.py':sha(B/'reproduce-round-01.py')},'status':'measured native static ownership; independent visual review pending','nativeGeometryEvidence':'candidates/round-01/geometry-audit.json'})
write(C/'native-context-alpha-bounds.json',{'records':[{'path':rel(p),'size':list(load(p).size),'alphaBounds':load(p).getchannel('A').getbbox(),'sourceSHA256':sha(B/'round-01.blend')} for p in sorted((C/'native/contexts').glob('*.png'))]})
write(C/'editor-change-notes.json',{'nativeChanges':['Retained exact original canonical W collar polygons and actual material/world/light graphs; redesigned only the finite end support and native decoration.','Lowered and articulated exposed east termination within exact original ground rectangle; five rounded terrace stones give readable support volume.','Replaced three closed pegs with ten hollow tube-corals in purposeful teal and purple clusters, shaped rims, inner walls, recessed floors, two substantial nodules and four teal pebbles.'],'capture':'Static1/frame1/12fps/nonloop/all4; exact direct-native2x384704/root192496/.01/EEVEE64. No fitting, postprocessing, alpha/RGB repair, overlap or target card.','originalInspection':'Own initial unchanged. Raw inactive-library bounds retained explicitly rejected. Corrected authored-transform original measurements and final evaluated saved-native audits are separate.','constructionCorrection':'Unsubmitted draft retained outside final used closure under candidates/explorations/native-draft-01. It triangulated canonical quads and produced1.6859e-7 float normal-field deviation. Final keeps original collar polygons; independent audit reports zero normal error.','residuals':extent_summary,'review':'Editor has issued no visual approval, packet seal, family approval, Godot or production change.'})
write(C/'toolchain.json',{'pythonExecutable':sys.executable,'pythonVersion':sys.version,'PillowVersion':Image.__version__,'platform':platform.platform(),'blender':'5.2.2 LTS /opt/homebrew/bin/blender; actual version recorded in native logs/audits','commands':['PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender --background --python-exit-code 1 --python source/reproduce-round-01.py','PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender --background --python-exit-code 1 --python source/verify-native-round-01.py','PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender --background --python-exit-code 1 --python source/reproduce-round-01.py -- --replay --out <fresh-output> --heroes-only','DEBUG=pw:browser node source/capture-consumer-round-01.cjs','DEBUG=pw:browser node source/diagnose-source-extent-round-01.cjs','<bundled Pillow Python> -B source/assemble-evidence-round-01.py','<bundled Pillow Python> -B source/finalize-handoff-round-01.py'],'portableInputs':'Construction and context recipes use only source/resources. Commands interpreted from object root; use fresh paths to retain immutable outputs. Actual launch argv retained in source/round-01-consumer-launch.log and source/round-01-extent-launch.log.'})
print(json.dumps({'previewFiles':len(coverage),'previewAliases':len(previews),'checks':checks,'extentSummary':extent_summary},indent=2))
if not all(checks.values()):raise RuntimeError('Technical handoff checks failed')
