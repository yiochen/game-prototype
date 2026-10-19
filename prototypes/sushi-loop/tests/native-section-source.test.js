import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const source = fileURLToPath(new URL('../assets/production/source/blender/', import.meta.url));
const world = readFileSync(join(source, 'world_components.py'), 'utf8');
const revision = readFileSync(join(source, 'catalog_art_revision.py'), 'utf8');
const extract = directory => JSON.parse(execFileSync('python3', ['-c', String.raw`
import importlib.util,json,pathlib,sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('native_sections',pathlib.Path(sys.argv[1])/'validate_connected_fixtures.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
print(json.dumps(module.cross_sections(pathlib.Path(sys.argv[2])/'world_components.py')))
`, source, directory], { encoding: 'utf8', timeout: 10000, stdio: ['ignore', 'pipe', 'pipe'] }));
const copied = (recipe, callback) => {
  const directory = mkdtempSync(join(tmpdir(), 'sushi-native-sections-'));
  try {
    writeFileSync(join(directory, 'world_components.py'), world);
    if (recipe !== null) writeFileSync(join(directory, 'catalog_art_revision.py'), recipe);
    return callback(directory);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
};

test('native seam AST includes original asymmetric sections and the approved full V2 wall/cliff sections', () => {
  const sections = extract(source);
  assert.ok(sections['reef-section-v1'].length, 'Original asymmetric reef section must remain checked');
  assert.ok(sections['wreck-frame-section-v1'].length, 'Original asymmetric wreck section must remain checked');
  assert.equal(sections['restaurant-wall-wood-blue-v1'].length, 7);
  assert.equal(sections['restaurant-wall-wood-blue-v2'].length, 7, 'Panel, four board rings, cap and complete tapered coping must all be checked');
  assert.equal(sections['restaurant-wall-wood-blue-v2'].at(-1).length, 6, 'The coping slope must remain part of the section');
  assert.deepEqual(sections['rock-wall-full-cell-v2'][0].slice(0, 3), [[-.5, 0], [.5, 0], [.5, .67]]);
  assert.equal(Math.max(...sections['rock-wall-full-cell-v2'][0].map(point => point[1])), 1.15);
});

test('native seam extraction follows modified source literals and loop heights without importing Blender or executing source', () => {
  const changed = `raise RuntimeError('Native recipe was executed')\n${revision}`
    .replace('[(.105, .07), (.105, .89)]', '[(.137, .07), (.137, .89)]')
    .replace('enumerate((.12, .34, .56, .78))', 'enumerate((.13, .35, .57, .79))')
    .replace('profile = [(-.5, 0), (.5, 0)', 'profile = [(-.56, 0), (.56, 0)');
  copied(changed, directory => {
    const sections = extract(directory);
    assert.equal(sections['restaurant-wall-wood-blue-v2'][0][0][0], -.137);
    assert.equal(sections['restaurant-wall-wood-blue-v2'][1][0][1], .13);
    assert.equal(sections['restaurant-wall-wood-blue-v2'][4][0][1], .79);
    assert.equal(sections['rock-wall-full-cell-v2'][0][0][0], -.56);
    assert.equal(sections['restaurant-wall-wood-blue-v1'][0][0][0], -.105, 'Older source sections retain their own dimensions');
  });
});

test('native seam extraction rejects unknown runtime geometry and details outside their audited cliff section', () => {
  copied(revision.replace('[(.105, .07), (.105, .89)]', 'runtime_section()'), directory => {
    assert.throws(() => extract(directory), /Native cross-section must use resolvable source literals/);
  });
  copied(revision.replace("'middle', [(.5, .001), (.5, .10), (.44, .21)]", "'middle', [(.7, .001), (.7, .10), (.44, .21)]"), directory => {
    assert.throws(() => extract(directory), /Native detail tier extends outside the audited loft section/);
  });
});

test('original-only source snapshots keep their V1 seam audit without requiring later modeling files', () => {
  copied(null, directory => {
    const sections = extract(directory);
    assert.ok(sections['rock-wall-section-v1'].length);
    assert.equal(sections['rock-wall-full-cell-v2'], undefined);
  });
});
