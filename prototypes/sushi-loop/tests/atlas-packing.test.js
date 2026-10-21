import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const publisher = fileURLToPath(new URL('../assets/production/source/blender/publish_captures.py', import.meta.url));
const selectColumns = (frame, count, scale = 2) => JSON.parse(execFileSync('python3', ['-c', String.raw`
import ast,json,math,pathlib,sys
tree=ast.parse(pathlib.Path(sys.argv[1]).read_text())
nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='atlas_columns']
namespace={'math':math,'MAX_ATLAS_DIMENSION':8192}
exec(compile(ast.Module(body=nodes,type_ignores=[]),sys.argv[1],'exec'),namespace)
frame,count,scale=json.loads(sys.argv[2])
columns=namespace['atlas_columns'](frame,count,scale)
print(json.dumps({'columns':columns,'size':[frame[0]*scale*columns,frame[1]*scale*math.ceil(count/columns)]}))
`, publisher, JSON.stringify([frame, count, scale])], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));

test('conveyor keeps six columns, all 24 complete frames and original resolution', () => {
  assert.deepEqual(selectColumns([192, 352], 24), { columns: 6, size: [2304, 2816] });
});

test('large dock cover packs five columns within the 8192 texture cap', () => {
  assert.deepEqual(selectColumns([736, 704], 12), { columns: 5, size: [7360, 4224] });
});

test('tall frames increase columns when needed without scaling the image', () => {
  assert.deepEqual(selectColumns([250, 1500], 24), { columns: 12, size: [6000, 6000] });
});

test('one-frame tiles retain one complete cell', () => {
  assert.deepEqual(selectColumns([128, 128], 1), { columns: 1, size: [256, 256] });
});

test('impossible packing fails with a paging requirement instead of shrinking art', () => {
  assert.throws(() => selectColumns([500, 1500], 24), /split the clip into atlas pages rather than resizing frames/);
  assert.throws(() => selectColumns([5000, 128], 1), /Cannot pack/);
});

test('all existing native clip frames have a valid full-resolution atlas layout', () => {
  const source = fileURLToPath(new URL('../assets/production/source/native-records/', import.meta.url));
  const results = JSON.parse(execFileSync('python3', ['-c', String.raw`
import ast,json,math,pathlib,sys
path=pathlib.Path(sys.argv[1]);tree=ast.parse(path.read_text())
nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='atlas_columns']
ns={'math':math,'MAX_ATLAS_DIMENSION':8192};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
root=pathlib.Path(sys.argv[2]);index=json.loads((root/'index.json').read_text())
count=0
for aid in index['assetIds']:
 meta=json.loads((root/aid/'asset.json').read_text())
 for clip in meta['clips'].values():
  columns=ns['atlas_columns'](meta['frame'],clip['frames'],2)
  assert columns*meta['frame'][0]*2<=8192
  assert math.ceil(clip['frames']/columns)*meta['frame'][1]*2<=8192
  count+=1
print(json.dumps({'assets':len(index['assetIds']),'clips':count}))
`, publisher, source], { encoding: 'utf8' }));
  assert.equal(results.assets, 103);
  assert.ok(results.clips > 100);
});
