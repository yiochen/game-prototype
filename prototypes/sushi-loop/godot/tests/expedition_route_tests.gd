extends SceneTree
## The GDScript route port must reproduce the JS reference exactly
## (fixture: node assets/expedition/route/parity-fixture.mjs).
const Route = preload("res://scripts/expedition/route.gd")
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

static func v2_list() -> Array:
	var pieces: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/expedition/pieces.json"))
	var out: Array = []
	for id in pieces.objects:
		var o: Dictionary = pieces.objects[id]
		if o.family in ["rock", "ruin", "landmark", "sealife-edge", "sealife-floor"]:
			var entry := {"id": id, "family": o.family}
			if o.has("height"): entry.height = o.height
			out.append(entry)
	return out

func run() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/expedition_route_parity.json"))
	var hashes: Array = []
	for args in [[0, 0, 0], [3, 17, 21], [10, 97700, 51], [-1, 5, 7]]: hashes.append(Route.cell_hash(args[0], args[1], args[2]))
	check(_close(hashes, fixture.primitives.hash), "32-bit cell hash matches JS: %s vs %s" % [hashes, fixture.primitives.hash])
	var rng := Route.Mulberry32.new(12345)
	var draws: Array = []
	for i in range(5): draws.append(rng.next())
	check(_close(draws, fixture.primitives.mulberry), "mulberry32 matches JS: %s vs %s" % [draws, fixture.primitives.mulberry])

	var analysis := Route.analyze_library(Route.load_chunks())
	check(analysis.problems.is_empty(), "every chunk file is valid: %s" % analysis.problems)
	var library: Array = analysis.chunks
	var summary: Array = library.map(func(c): return {"id": c.id, "difficulty": c.difficulty, "next": c.next})
	check(summary.size() == fixture.library.size(), "library size matches")
	for i in range(mini(summary.size(), fixture.library.size())):
		var a: Dictionary = summary[i]
		var b: Dictionary = fixture.library[i]
		check(a.id == b.id and float(a.difficulty) == float(b.difficulty) and a.next == b.next, "chunk %s analysis matches JS" % b.id)

	var v2 := v2_list()
	for expected in fixture.runs:
		var seed_value := int(expected.seed)
		var sequence := Route.generate(seed_value, library, expected.get("plan", Route.DEFAULT_PLAN))
		check(sequence.map(func(c): return c.id) == expected.sequence, "seed %d%s chunk sequence matches" % [seed_value, " (feature plan)" if expected.has("plan") else ""])
		var assembled := Route.assemble(sequence)
		check(assembled.rows == expected.rows, "seed %d grid matches" % seed_value)
		var scene := Route.compose_scene(assembled.rows, v2, seed_value)
		check(scene.objects.map(func(o): return [o.x, o.y, o.id, o.dir, o.get("w", 1)]) == _ints(expected.objects), "seed %d objects match" % seed_value)
		check(scene.beds.map(func(b): return b.sprite) == expected.beds, "seed %d beds match" % seed_value)
		check(scene.seabed.map(func(o): return [o.x, o.y, o.id, o.dir]) == _ints(expected.seabed), "seed %d seabed matches" % seed_value)
		check(scene.pickups.map(func(p): return [p.x, p.y]) == expected.pickups, "seed %d pickups match" % seed_value)
		check(scene.vents.map(func(v): return [v.x, v.y]) == expected.vents, "seed %d vents match" % seed_value)
		check(scene.shafts.map(func(s): return [s.x, s.y]) == _ints(expected.shafts), "seed %d shafts match" % seed_value)
		check(scene.autopilot == expected.autopilot, "seed %d autopilot matches" % seed_value)

	# Load-time analysis rejects a broken chunk without breaking the library.
	var broken := {"id": "broken", "kind": "normal", "difficulty_override": null, "rows": ["###########", "###########"]}
	var mixed := Route.analyze_library(Route.load_chunks() + [broken])
	check(mixed.problems.has("broken") and not mixed.chunks.any(func(c): return c.id == "broken"), "invalid chunk is reported and left out")
	print("Expedition route parity: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)

## JSON integers arrive as floats; compare grid coordinates as ints.
func _ints(rows: Array) -> Array:
	return rows.map(func(r): return r.map(func(v): return int(v) if v is float and v == floor(v) else v))

## Fixture floats pass through JSON text; compare to well below a 2^-32 step.
func _close(a: Array, b: Array) -> bool:
	if a.size() != b.size(): return false
	for i in range(a.size()):
		if absf(float(a[i]) - float(b[i])) > 1e-12: return false
	return true
