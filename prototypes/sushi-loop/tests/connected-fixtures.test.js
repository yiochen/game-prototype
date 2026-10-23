import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { groundRoot, orderPlacements, placementAtTime } from '../wireframe/sprite-layout.js';

const production = fileURLToPath(new URL('../assets/production/', import.meta.url));
const publisher = `${production}source/blender/publish_captures.py`;
// Run only the publisher's pure metadata code. Packing/importing Blender/Pillow is
// intentionally unnecessary for verifying a context-only publication.
const python = String.raw`
import argparse,ast,contextlib,copy,hashlib,io,json,math,os,shutil,sys,tempfile
from pathlib import Path
path,target=Path(sys.argv[1]),Path(sys.argv[2])
tree=ast.parse(path.read_text());constants={'DIRECTIONS','ANGLES','ALIASES','FX_IDS','PROP_IDS','CLUSTER_IDS','MAX_ATLAS_DIMENSION'}
body=[node for node in tree.body if isinstance(node,ast.FunctionDef) or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets)]
pack_calls=[]
def forbidden_pack(*args,**kwargs):
    pack_calls.append(True)
    raise AssertionError('Context refresh must not repack a capture')
ns={'argparse':argparse,'hashlib':hashlib,'json':json,'math':math,'os':os,'shutil':shutil,'sys':sys,'Path':Path,'HERE':path.parent,'pack':forbidden_pack}
exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),ns)
manifest=json.loads((target/'library.json').read_text())
ns['hydrate_registrations'](manifest,target);ns['refresh_interactions'](manifest)
first=json.dumps(manifest,sort_keys=True)
ns['refresh_interactions'](manifest)
idempotent=first==json.dumps(manifest,sort_keys=True)
probe=copy.deepcopy(next(o for o in manifest['objects'] if o['kind']=='belt'))
info=json.loads((target/probe['source']['assetRecord']).read_text());camera=json.loads((target/probe['source']['camera']).read_text())
info['flow']={'incoming':None,'outgoing':'N'};info['supportLayout']={'authored':'native-foot-layout'}
ns['set_registration'](probe,info,camera)
with tempfile.TemporaryDirectory(prefix='sushi-context-test-') as temp:
    repo=Path(temp);out=repo/'prototypes/sushi-loop/assets/production';out.mkdir(parents=True)
    (out/'library.json').write_text(json.dumps(manifest))
    sys.argv=[str(path),'--repo',str(repo),'--interactions-only']
    log=io.StringIO()
    with contextlib.redirect_stdout(log):ns['main']()
    after=json.loads((out/'library.json').read_text())
    mode={'sameInteractions':all(a['interactions']==b['interactions'] for a,b in zip(manifest['objects'],after['objects'])),'files':[str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()],'log':log.getvalue(),'packCalls':len(pack_calls)}
fields=('id','kind','family','footprint','directionFootprints','directionRootCells','rootCell','ports','portProfiles','portDefinition','sockets','interactions')
objects=[]
for o in manifest['objects']:
    record=o.get('source',{}).get('assetRecord')
    source=o.get('source',{});pipeline=source.get('pipeline')
    if o.get('status')=='ready' and not record:
        if pipeline not in ('imagegen-2d','procedural-2d'):raise AssertionError('Ready object lacks declared native/2D provenance: '+o['id'])
        if o['kind']=='belt' or o.get('ports'):raise AssertionError('Connected native module must retain native registration: '+o['id'])
        reference=source.get('artwork') if pipeline=='imagegen-2d' else source.get('godot')
        if not reference or not (target/reference).is_file():raise AssertionError('2D object lacks editable source: '+o['id'])
        if pipeline=='imagegen-2d' and hashlib.sha256((target/reference).read_bytes()).hexdigest()!=source.get('sha256'):raise AssertionError('2D artwork hash mismatch: '+o['id'])
        for clip in o.get('clips',[]):
            if not clip.get('directions') or any(not (target/d['image']).is_file() for d in clip['directions'].values()):raise AssertionError('2D object lacks actual sprite exports: '+o['id'])
    native=json.loads((target/record).read_text()) if record else {}
    objects.append({**{k:o[k] for k in fields if k in o},'native':{k:native[k] for k in ('flow','ports') if k in native}})
print(json.dumps({'objects':objects,'probe':{'portDefinition':probe['portDefinition'],'supportLayout':probe['supportLayout']},'idempotent':idempotent,'mode':mode}))
`;
const data = JSON.parse(execFileSync('python3', ['-c', python, publisher, production], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024, timeout: 20000 }));
const byId = new Map(data.objects.map(object => [object.id, object]));
const opposite = { N: 'S', E: 'W', S: 'N', W: 'E' };
const vectors = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
const near = (a, b) => Math.abs(a - b) < 1e-3;
const point = (placement, port) => {
  const object = byId.get(placement.object);
  const root = groundRoot(placement, object, 128);
  return object.ports[placement.direction || 'S'][port].map((value, index) => root[index] + value);
};
const matching = (left, right) => left.every((value, index) => near(value, right[index]));

function portMatch(placement, name, other, candidate) {
  if (!matching(point(placement, name), point(other, candidate))) return false;
  const a = byId.get(placement.object), b = byId.get(other.object);
  if (a.kind === 'belt') return b.kind === 'belt' && name !== candidate;
  return a.portProfiles[name] === b.portProfiles[candidate];
}

test('native belt flow replaces stale end definitions and preserves authored support layout', () => {
  const belts = data.objects.filter(object => object.kind === 'belt');
  assert.equal(belts.length, 20);
  for (const object of belts) {
    const expected = Object.fromEntries(['incoming', 'outgoing'].filter(name => object.native.flow[name]).map(name => [name, object.native.flow[name]]));
    assert.deepEqual(object.portDefinition, expected, object.id);
  }
  assert.equal(byId.get('belt-end-n').portDefinition.incoming, 'S');
  assert.equal(byId.get('belt-end-e').portDefinition.incoming, 'W');
  assert.deepEqual(data.probe, { portDefinition: { outgoing: 'N' }, supportLayout: { authored: 'native-foot-layout' } });
});

test('every declared seam port meets a compatible neighbor at the actual projected position', () => {
  const modules = data.objects.filter(object => Object.keys(object.ports?.S || {}).length);
  assert.equal(modules.length, 42);
  for (const object of modules) {
    const context = object.interactions.find(scene => scene.connectionReview);
    assert.ok(context, `${object.id} has a connected context`);
    const target = context.placements.find(placement => placement.object === object.id && placement.x === 2 && placement.y === 2);
    assert.ok(target, `${object.id} has its reviewed module`);
    for (const name of Object.keys(object.ports.S)) {
      assert.ok(context.placements.some(other => other !== target && Object.keys(byId.get(other.object).ports?.[other.direction || 'S'] || {}).some(candidate => portMatch(target, name, other, candidate))), `${object.id}/${name} must touch, rather than sit near, a compatible port`);
    }
  }
});

test('all directed belt neighbors connect and every corner dish follows the native quarter circle', () => {
  for (const object of data.objects.filter(object => object.kind === 'belt')) {
    const scene = object.interactions.find(scene => scene.connectionReview?.kind === 'directed-belt' && scene.placements.some(p => p.motion));
    assert.ok(scene, `${object.id} shows a separate conveyed dish`);
    const route = scene.placements.filter(p => byId.get(p.object).kind === 'belt');
    for (let index = 1; index < route.length; index++) assert.ok(matching(point(route[index - 1], 'outgoing'), point(route[index], 'incoming')), `${object.id}: directed route ${index - 1}→${index}`);
    const dish = scene.placements.find(p => p.motion);
    assert.ok(matching(dish.offset, object.sockets.S.deck), `${object.id}: dish is supported at deck height`);
    assert.equal(dish.renderPass, 'foreground', `${object.id}: attached plate remains over the isolated deck fixture`);
    for (const seconds of [0, dish.motion.duration / 4, dish.motion.duration / 2, dish.motion.duration * 3 / 4, dish.motion.duration - .1]) {
      const ordered = orderPlacements(scene.placements.map(placement => placementAtTime(placement, seconds)), data.objects);
      assert.equal(ordered.at(-1).object, dish.object, `${object.id}: fractional ground position must never paint the attached plate beneath a deck`);
    }
    assert.match(scene.note, /independent of slat timing/);
    const { incoming, outgoing } = object.portDefinition;
    if (incoming && outgoing && opposite[incoming] !== outgoing) {
      assert.equal(route.length, 5);
      assert.equal(route[1].object, `belt-straight-${opposite[incoming].toLowerCase()}`);
      assert.equal(route[3].object, `belt-straight-${outgoing.toLowerCase()}`);
      const center = [2, 2].map((value, index) => value + .5 * (vectors[incoming][index] + vectors[outgoing][index]));
      const arc = dish.motion.path.slice(2, -2);
      assert.equal(arc.length, 17);
      for (const p of arc) assert.ok(near(Math.hypot(p[0] - center[0], p[1] - center[1]), .5), `${object.id}: plate must follow the curved deck centerline`);
      assert.ok(matching(arc[0], vectors[incoming].map((value, index) => 2 + .5 * value)));
      assert.ok(matching(arc.at(-1), vectors[outgoing].map((value, index) => 2 + .5 * value)));
    }
  }
});

test('floors meet all cell edges and every dock view includes the native overlapping entry', () => {
  for (const object of data.objects.filter(object => object.kind === 'floor')) {
    const scene = object.interactions.find(scene => scene.connectionReview?.kind === 'floor-patch');
    assert.deepEqual(scene.placements.map(p => [p.x, p.y]), Array.from({ length: 9 }, (_, index) => [index % 3, Math.floor(index / 3)]));
  }
  for (const object of data.objects.filter(object => object.family === 'W10')) {
    const scene = object.interactions.find(scene => scene.connectionReview?.kind === 'dock-assembly');
    const entry = scene.placements.find(p => p.object === 'dock-entry');
    assert.ok(matching([entry.x, entry.y, ...entry.offset], [1, 2.5, 0, 0]));
    const sub = scene.placements.find(p => p.object === 'submarine-yellow');
    const deck = scene.placements.find(p => p.object === 'dock-floor');
    const hut = scene.placements.find(p => p.object === 'workshop-hut');
    assert.equal(sub.supportedBy, deck.id, 'The docked submarine must draw above its declared deck');
    assert.equal(hut.supportedBy, deck.id, 'The hut must draw above its declared deck');
    assert.equal(entry.supportedBy, undefined, 'External stairs retain their independent depth order');
    const ordered = orderPlacements(scene.placements, data.objects);
    assert.ok(ordered.findIndex(p => p.id === deck.id) < ordered.findIndex(p => p.object === hut.object));
    assert.ok(ordered.findIndex(p => p.id === deck.id) < ordered.findIndex(p => p.object === sub.object));
    assert.ok(matching([sub.x, sub.y], [.3, .92]));
    assert.ok(matching(sub.offset, [0, -.23 * 128 * .70]), 'The .23-world-unit dock support follows the approved70% front projection');
  }
});

test('context-only publication is deterministic and does not require or repack captures', () => {
  assert.equal(data.idempotent, true);
  assert.equal(data.mode.sameInteractions, true);
  assert.equal(data.mode.packCalls, 0);
  assert.deepEqual(data.mode.files, ['library.json']);
  assert.ok(data.mode.log.includes(`${data.objects.length} objects; no captures copied or repacked`));
  assert.equal(byId.get('submarine-yellow').interactions.filter(scene => scene.name.startsWith('Baseline and upgraded')).length, 1);
});
