extends RefCounted
## Seeded chunk-based expedition routes: a line-for-line port of
## assets/expedition/route/route.js (the reference shared with the HTML review
## and map designer). tests/expedition_route_tests.gd checks it against the
## JS output for fixed seeds, so keep both in step.
##
## Chunks are map-designer documents in res://content/expedition/chunks/,
## analysed when loaded: invalid chunks are reported and left out.

const COLUMNS := 11
const VIEW_COLUMNS := 7
const MIN_SEAM := 2
const MAX_SHIFT := 2
## Ship physics model (see route.js): collider half-size in cells; positions
## every quarter column and sixth of a row, sliding at most one quarter column
## per step (1.5 columns per row). Positions are bits of one 64-bit mask per step.
const SHIP_HALF := [0.32, 0.44]
const QX := 4
const QY := 6
const SHIP_LO := 2
const SHIP_HI := COLUMNS * QX - 2
const CHUNK_DIR := "res://content/expedition/chunks"
## Issue #22 feature chunks (current, portal, boost) are offered only by their own plan slots.
## Issue #25 creature chunks belong to one species (`creature`) and mark the
## rows where its attacks may be live (`attack_rows`); see discharge.gd.
const KINDS := ["launch", "start", "normal", "rest", "fork", "finish", "current", "portal", "boost", "creature"]
const DEFAULT_PLAN := ["launch", "launch", "start", 1.5, 2.0, "rest", 2.5, "fork", 3.0, 3.5, "rest", "fork", 4.0, "finish"]
const MASK := 0xFFFFFFFF
const DIRS := ["N", "E", "S", "W"]
const GROWTH := {"decor-kelp": "k", "decor-foreground-coral": "c", "decor-midground-coral": "m"}

# ------------------------------------------------------------ 32-bit integer math

## Low 32 bits of a * b (JS Math.imul), as an unsigned value.
static func imul(a: int, b: int) -> int:
	a &= MASK; b &= MASK
	return (((a & 0xFFFF) * b) + ((((a >> 16) * b) & MASK) << 16)) & MASK

static func cell_hash(x: int, y: int, salt: int) -> float:
	var h := (imul(x, 374761393) + imul(y, 668265263) + imul(salt, 2147483647)) & MASK
	h = imul(h ^ (h >> 13), 1274126177)
	return float((h ^ (h >> 16)) & MASK) / 4294967296.0

## mulberry32 (JS reference): one 32-bit state, uniform [0, 1).
class Mulberry32:
	var a := 0
	func _init(seed_value: int) -> void: a = seed_value & 0xFFFFFFFF
	static func _imul(x: int, y: int) -> int:
		x &= 0xFFFFFFFF; y &= 0xFFFFFFFF
		return (((x & 0xFFFF) * y) + ((((x >> 16) * y) & 0xFFFFFFFF) << 16)) & 0xFFFFFFFF
	func next() -> float:
		a = (a + 0x6D2B79F5) & 0xFFFFFFFF
		var t := a
		t = _imul(t ^ (t >> 15), t | 1)
		t = (t ^ ((t + _imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
		return float((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

# ------------------------------------------------------------ grid queries

static func is_rock(ch: String) -> bool:
	return ch == "#" or ch == "k" or ch == "c" or ch == "m"

static func _open_at(rows: Array, x: int, y: int) -> bool:
	return y >= 0 and y < rows.size() and x >= 0 and x < str(rows[y]).length() and not is_rock(str(rows[y])[x])

## Contiguous open runs of a row as [start, end] inclusive.
static func runs(row: String) -> Array:
	var out: Array = []
	var start := -1
	for x in range(row.length() + 1):
		var open := x < row.length() and not is_rock(row[x])
		if open and start < 0: start = x
		if not open and start >= 0:
			out.append([start, x - 1]); start = -1
	return out

static func _open_set(row: String) -> Array:
	var out: Array = []
	for x in range(row.length()):
		if not is_rock(row[x]): out.append(x)
	return out

static func seam_width(upper_entry: String, lower_exit: String) -> int:
	var best := 0
	var run := 0
	for x in range(upper_entry.length()):
		run = run + 1 if not is_rock(upper_entry[x]) and not is_rock(lower_exit[x]) else 0
		best = maxi(best, run)
	return best

static func _key(x: int, y: int) -> String:
	return "%d,%d" % [x, y]

## Cells reachable from the entry row moving up, sliding at most `shift` cells
## sideways per row within an open run.
static func reachable(rows: Array, shift: int = MAX_SHIFT) -> Dictionary:
	var h := rows.size()
	var seen := {}
	var frontier: Array = _open_set(str(rows[h - 1]))
	for x in frontier: seen[_key(x, h - 1)] = true
	for y in range(h - 1, 0, -1):
		var next := {}
		for x in frontier:
			for dx in range(-shift, shift + 1):
				var nx: int = x + dx
				var clear := true
				for s in range(mini(x, nx), maxi(x, nx) + 1):
					if not _open_at(rows, s, y): clear = false
				if not clear: continue
				seen[_key(nx, y)] = true
				if _open_at(rows, nx, y - 1): next[nx] = true
		frontier = next.keys()
		for x in frontier: seen[_key(x, y - 1)] = true
	return seen

## Reachable open cells from which the exit cannot be reached (dead ends).
static func dead_ends(rows: Array) -> Array:
	var can_exit := {}
	for x in _open_set(str(rows[0])): can_exit[_key(x, 0)] = true
	for y in range(rows.size()):
		for run in runs(str(rows[y])):
			var ok := false
			for x in range(run[0], run[1] + 1):
				if can_exit.has(_key(x, y)) or (y > 0 and can_exit.has(_key(x, y - 1))): ok = true
			if ok:
				for x in range(run[0], run[1] + 1): can_exit[_key(x, y)] = true
	var out: Array = []
	for key in reachable(rows, str(rows[0]).length()):
		if not can_exit.has(key): out.append(key)
	return out

## Difficulty 1–5 from narrowness, required swerving and rock density.
static func difficulty(rows: Array) -> float:
	var narrow := 0.0
	var swerve := 0.0
	var rock := 0.0
	var prev = null
	var reach := reachable(rows)
	for y in range(rows.size() - 1, -1, -1):
		var row := str(rows[y])
		var usable: Array = []
		for run in runs(row):
			for x in range(run[0], run[1] + 1):
				if reach.has(_key(x, y)):
					usable.append(run); break
		if usable.is_empty(): continue
		var widest := 0
		for run in usable: widest = maxi(widest, run[1] - run[0] + 1)
		narrow += 1.0 / widest
		var ref: float = prev if prev != null else row.length() / 2.0
		var centre := 0.0
		var best := INF
		for run in usable:
			var c: float = (run[0] + run[1]) / 2.0
			var d := absf(c - ref)
			if d < best or (d == best and c < centre): best = d; centre = c
		if prev != null: swerve += absf(centre - prev)
		prev = centre
		var first: int = usable[0][0]
		var last: int = usable[0][1]
		for run in usable:
			first = mini(first, run[0]); last = maxi(last, run[1])
		var span := mini(VIEW_COLUMNS, last - first + 3)
		var inner := 0
		for x in range(first - 1, last + 2):
			if x >= 0 and x < row.length() and is_rock(row[x]): inner += 1
		rock += float(inner) / span
	var n := float(rows.size())
	var score := 1.0 + 5.0 * (narrow / n - 0.25) + 3.0 * (swerve / n) + 2.0 * (rock / n - 0.45)
	return round(clampf(score, 1.0, 5.0) * 2.0) / 2.0

# ------------------------------------------------------------ chunk files

## Designer document → {id, name, kind, source, difficulty_override, rows}
## (creature chunks add creature and attack_rows).
static func chunk_from_map(doc: Dictionary, id: String) -> Dictionary:
	var columns := int(doc.grid.columns)
	var height := int(doc.grid.rows)
	var rock := {}
	var decor := {}
	var gold := {}
	for p in doc.placements:
		var key := _key(int(p.x), int(p.y))
		match str(p.layer):
			"obstacles": rock[key] = str(p.object)
			"decor": decor[key] = str(p.object)
			"pickups": gold[key] = str(p.object)
	var rows: Array = []
	for y in range(height):
		var row := ""
		for x in range(columns):
			var key := _key(x, y)
			if rock.has(key): row += GROWTH.get(decor.get(key, ""), "#")
			elif gold.has(key): row += "$"
			elif decor.has(key): row += ","
			else: row += "."
		rows.append(row)
	var meta: Dictionary = doc.get("chunk", {}) if doc.get("chunk") is Dictionary else {}
	var chunk := {"id": id, "name": str(doc.get("name", id)), "kind": str(meta.get("kind", "normal")), "source": str(meta.get("source", "")),
		"difficulty_override": meta.get("difficulty"), "rows": rows}
	if chunk.kind == "creature": chunk.creature = meta.get("creature"); chunk.attack_rows = meta.get("attack_rows")
	return chunk

static func load_chunks(dir: String = CHUNK_DIR) -> Array:
	var out: Array = []
	var files := DirAccess.get_files_at(dir)
	for file in files:
		if not file.ends_with(".json"): continue
		var doc = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join(file)))
		if doc is Dictionary and doc.get("format") == "sushi-loop-underwater-map" and doc.get("grid") is Dictionary and doc.get("placements") is Array:
			out.append(chunk_from_map(doc, file.get_basename()))
		else:
			push_warning("Expedition chunk %s is not a map document" % file)
	return out

static func validate_chunk(chunk: Dictionary) -> Array:
	var rows: Array = chunk.rows
	if rows.is_empty() or rows.any(func(r): return str(r).length() != COLUMNS): return ["rows must be %d cells wide" % COLUMNS]
	var problems: Array = []
	if str(chunk.get("kind", "normal")) not in KINDS: problems.append("unknown kind %s" % chunk.kind)
	var reach := reachable(rows)
	if not _open_set(str(rows[0])).any(func(x): return reach.has(_key(x, 0))): problems.append("exit unreachable at steering speed")
	var dead := dead_ends(rows)
	if not dead.is_empty(): problems.append("dead ends at %s" % " ".join(dead))
	problems.append_array(ship_problems(rows))
	for y in range(rows.size()):
		for x in range(str(rows[y]).length()):
			if str(rows[y])[x] == "$" and not reach.has(_key(x, y)): problems.append("unreachable gold %d,%d" % [x, y])
	if chunk.get("kind") == "creature":
		var attack = chunk.get("attack_rows")
		if not chunk.get("creature") is String or str(chunk.creature).is_empty(): problems.append("creature chunks name their creature")
		if not attack is Array or attack.size() != 2 or not attack.all(func(v): return (v is int or v is float) and v == floor(v)) or int(attack[0]) < 0 or int(attack[0]) >= int(attack[1]) or int(attack[1]) >= rows.size():
			problems.append("creature chunks need attack_rows [first, last] inside the chunk")
	# Launch: the preparation cruise runs straight up the middle without steering.
	if chunk.get("kind") == "launch":
		if rows.any(func(r): return "$" in str(r)): problems.append("launch chunks carry no gold")
		if rows.any(func(r): return is_rock(str(r)[4]) or is_rock(str(r)[5]) or is_rock(str(r)[6])): problems.append("launch chunks keep columns 4-6 open")
	return problems

## Fly the real hull through rows (route.js shipProblems): unreachable exit,
## gold it cannot collect and still leave, and lanes it can enter but not leave.
static func ship_problems(rows: Array) -> Array:
	var n := rows.size()
	var top := QY / 2
	var bottom := n * QY - QY / 2
	var rock_rows: Array = []
	for y in range(n):
		var mask := 0
		for x in range(COLUMNS):
			if is_rock(str(rows[y])[x]): mask |= 1 << x
		rock_rows.append(mask)
	var cols: Array = []
	cols.resize(SHIP_HI + 1)
	for i in range(SHIP_LO, SHIP_HI + 1):
		var x := i / float(QX)
		var mask := 0
		for cx in range(maxi(0, floori(x - SHIP_HALF[0])), mini(COLUMNS - 1, floori(x + SHIP_HALF[0])) + 1): mask |= 1 << cx
		cols[i] = mask
	var opens := {}
	for yy in range(top, bottom + 1):
		var y := yy / float(QY)
		var rock := 0
		for cy in range(maxi(0, floori(y - SHIP_HALF[1])), mini(n - 1, floori(y + SHIP_HALF[1])) + 1): rock |= int(rock_rows[cy])
		var open := 0
		for i in range(SHIP_LO, SHIP_HI + 1):
			if (rock & int(cols[i])) == 0: open |= 1 << i
		opens[yy] = open
	var forward := {bottom: opens[bottom]}
	var alive := {top: opens[top]}
	for yy in range(bottom - 1, top - 1, -1): forward[yy] = _ship_step(forward[yy + 1], opens[yy])
	for yy in range(top + 1, bottom + 1): alive[yy] = _ship_step(alive[yy - 1], opens[yy])
	var problems: Array = []
	if int(forward[top]) == 0: problems.append("exit unreachable by the ship")
	for y in range(n):
		var yy := y * QY + QY / 2
		var f: int = forward[yy]
		var both: int = f & int(alive[yy])
		var row := str(rows[y])
		for x in range(COLUMNS):
			if row[x] != "$": continue
			var ok := false
			for i in range(SHIP_LO, SHIP_HI + 1):
				if (both & (1 << i)) != 0 and absf(i / float(QX) - x - 0.5) <= 0.6: ok = true; break
			if not ok: problems.append("gold %d,%d out of the ship's reach" % [x, y])
		for run in runs(row):
			var lane := 0
			for i in range(maxi(SHIP_LO, int(run[0]) * QX), mini(SHIP_HI, (int(run[1]) + 1) * QX) + 1): lane |= 1 << i
			if (f & lane) != 0 and (both & lane) == 0: problems.append("trap lane %d-%d,%d" % [run[0], run[1], y])
	return problems

## One step: stay or slide a quarter column; the hull fits before and after.
static func _ship_step(live: int, open: int) -> int:
	var fits := live & open
	return open & (fits | (fits << 1) | (fits >> 1))

## Hull check across a seam (route.js seamFlies): only problems the upper
## chunk introduces over the same window under open water.
static func seam_flies(lower: Dictionary, upper: Dictionary) -> bool:
	var below: Array = lower.rows.slice(0, 4)
	var above: Array = upper.rows.slice(maxi(0, upper.rows.size() - 4))
	var water: Array = []
	for row in above: water.append(".".repeat(COLUMNS))
	var baseline := {}
	for p in ship_problems(water + below):
		if not str(p).begins_with("gold"): baseline[p] = true
	for p in ship_problems(above + below):
		if not str(p).begins_with("gold") and not baseline.has(p): return false
	return true

## May `upper` directly follow `lower` (upper sits above; the ship rises into it)?
static func compatible(lower: Dictionary, upper: Dictionary) -> bool:
	# Each chunk is validated on its own; across the seam the hull must still fly.
	return seam_width(str(upper.rows[upper.rows.size() - 1]), str(lower.rows[0])) >= MIN_SEAM and seam_flies(lower, upper)

## {chunks (sorted by id, with difficulty and next), problems {id: [..]}}.
static func analyze_library(chunks: Array) -> Dictionary:
	var sorted := chunks.duplicate()
	sorted.sort_custom(func(p, q): return str(p.id) < str(q.id))
	var problems := {}
	var valid: Array = []
	for chunk in sorted:
		var found := validate_chunk(chunk)
		if not found.is_empty():
			problems[chunk.id] = found; continue
		var entry: Dictionary = chunk.duplicate(true)
		entry.difficulty = float(chunk.difficulty_override) if chunk.get("difficulty_override") != null else difficulty(chunk.rows)
		valid.append(entry)
	for lower in valid:
		var next: Array = []
		if lower.kind != "finish":
			for upper in valid:
				# Launch chunks open the route: only launch or the start chunk may follow one.
				var opening: bool = lower.kind == "launch" if upper.kind in ["start", "launch"] else true
				if upper != lower and opening and compatible(lower, upper): next.append(upper.id)
		lower.next = next
	return {"chunks": valid, "problems": problems}

# ------------------------------------------------------------ runs

## Plan a run (start → rising difficulty with rest stops and forks → finish).
static func generate(seed_value: int, library: Array, plan: Array = DEFAULT_PLAN, force: String = "") -> Array:
	var rng := Mulberry32.new(seed_value)
	var by_id := {}
	for chunk in library: by_id[chunk.id] = chunk
	var sequence: Array = []
	var used := {}
	for slot in plan:
		var prev: Dictionary = sequence[sequence.size() - 1] if not sequence.is_empty() else {}
		var kind: String = slot if slot is String else "normal"
		var target = null if slot is String else float(slot)
		if force != "" and not used.has(force) and by_id.has(force):
			var forced: Dictionary = by_id[force]
			if forced.kind == kind and (prev.is_empty() or force in prev.next):
				sequence.append(forced); used[force] = 1; continue
		var pool: Array = library.filter(func(c): return c.kind == kind and (prev.is_empty() or c.id in prev.next))
		if pool.is_empty() and not prev.is_empty():
			pool = library.filter(func(c): return (c.kind == "normal" or c.kind == "rest") and c.id in prev.next)
		if pool.is_empty():
			push_error("No chunk can follow %s for slot %s" % [prev.get("id", "start"), slot])
			return []
		var weights: Array = []
		var total := 0.0
		for c in pool:
			var w: float = (1.0 if target == null else exp(-2.2 * absf(float(c.difficulty) - target))) / (1.0 + 3.0 * int(used.get(c.id, 0)))
			weights.append(w); total += w
		var r := rng.next() * total
		var pick: Dictionary = pool[pool.size() - 1]
		for i in range(pool.size()):
			r -= weights[i]
			if r <= 0.0:
				pick = pool[i]; break
		sequence.append(by_id[pick.id])
		used[pick.id] = int(used.get(pick.id, 0)) + 1
	return sequence

## Stack a sequence (start first) into one grid with the finish at the top.
static func assemble(sequence: Array) -> Dictionary:
	var rows: Array = []
	var spans: Array = []
	for i in range(sequence.size() - 1, -1, -1):
		var c: Dictionary = sequence[i]
		spans.append({"id": c.id, "kind": c.kind, "difficulty": c.difficulty, "y0": rows.size(), "y1": rows.size() + c.rows.size() - 1})
		rows.append_array(c.rows)
	spans.reverse()
	return {"rows": rows, "spans": spans}

# ------------------------------------------------------------ scene

## Sprite choice for an assembled grid: approved production pieces, same-recipe
## v2 variants (`v2` in library order: {id, family, height?}) and kit beds.
static func compose_scene(grid: Array, v2: Array, seed_value: int) -> Dictionary:
	var rows := grid.size()
	var cols := str(grid[0]).length()
	var H := func(x: int, y: int, salt: int) -> float: return cell_hash(x, y + seed_value * 977, salt)
	var solid := func(x: int, y: int) -> bool: return y >= 0 and y < rows and x >= 0 and x < cols and is_rock(str(grid[y])[x])
	var bed_solid := func(x: int, y: int) -> bool:
		if x < 0 or x >= cols: return y >= 0 and y < rows and solid.call(clampi(x, 0, cols - 1), y)
		return solid.call(x, y)
	var exposed := func(x: int, y: int) -> bool: return not solid.call(x - 1, y) or not solid.call(x + 1, y) or not solid.call(x, y + 1) or not solid.call(x, y - 1)

	var beds: Array = []
	for y in range(rows):
		for x in range(cols):
			if not solid.call(x, y): continue
			var mask := (1 if bed_solid.call(x, y - 1) else 0) | (2 if bed_solid.call(x + 1, y) else 0) | (4 if bed_solid.call(x, y + 1) else 0) | (8 if bed_solid.call(x - 1, y) else 0)
			beds.append({"x": x, "y": y, "sprite": "bed-%02d" % mask})

	var rocks: Array = v2.filter(func(o): return o.family == "rock")
	var pale: Array = ["column-broken", "decor-ruin-fragment"]
	for o in v2:
		if o.family == "ruin": pale.append(o.id)
	var landmark_ids := {}
	var sea_edge: Array = []
	var sea_floor: Array = []
	for o in v2:
		if o.family == "landmark": landmark_ids[o.id] = true
		elif o.family == "sealife-edge": sea_edge.append(o.id)
		elif o.family == "sealife-floor": sea_floor.append(o.id)

	var landmarks: Array = []
	var legs := {}
	var styles := ["arch-ruin", "bridge", "arch-pointed", "arch-broken"]
	for y in range(rows - 6, 3, -1):
		if landmarks.any(func(a): return absi(int(a.y) - y) < 10): continue
		for run in runs(str(grid[y])):
			var a: int = run[0]
			var b: int = run[1]
			var span := b - a + 1
			if span > 3 or a == 0 or b == cols - 1 or not solid.call(a - 1, y) or not solid.call(b + 1, y) or H.call(a, y, 51) > 0.5: continue
			var start := int(floor(H.call(a, y, 53) * styles.size()))
			var order: Array = styles.slice(start) + styles
			var id := ""
			for style in order:
				if landmark_ids.has("%s-%d" % [style, span]):
					id = "%s-%d" % [style, span]; break
			landmarks.append({"x": a - 1, "y": y, "w": span + 2, "h": 1, "id": id, "dir": "S"})
			legs[_key(a - 1, y)] = true; legs[_key(b + 1, y)] = true
			break

	var objects: Array = []
	var chosen := {}
	var plant_for := {"k": "decor-kelp", "c": "decor-foreground-coral", "m": "decor-midground-coral"}
	for y in range(rows):
		for x in range(cols):
			if not solid.call(x, y) or legs.has(_key(x, y)): continue
			var ch := str(grid[y])[x]
			var dir: String = DIRS[int(floor(H.call(x, y, 21) * 4))]
			var edge: bool = exposed.call(x, y)
			var plant := ""
			if plant_for.has(ch) and H.call(x, y, 24) < 0.42: plant = plant_for[ch]
			if plant == "" and ch == "#" and edge and H.call(x, y, 27) < 0.1:
				plant = "decor-foreground-coral" if H.call(x, y, 28) < 0.65 else ("decor-midground-coral" if H.call(x, y, 29) < 0.5 else "decor-kelp")
			if plant != "":
				objects.append({"x": x, "y": y, "id": plant, "dir": dir}); chosen[_key(x, y)] = plant; continue
			var r: float = H.call(x, y, 23)
			var pale_near := false
			for d in [[-1, 0], [0, -1], [-1, -1], [1, -1]]:
				if chosen.get(_key(x + d[0], y + d[1]), "") in pale: pale_near = true
			var id := ""
			if edge and not pale_near and r < 0.24: id = pale[int(floor(H.call(x, y, 25) * pale.size()))]
			elif edge and r >= 0.24 and r < 0.3 and not sea_edge.is_empty(): id = sea_edge[int(floor(H.call(x, y, 22) * sea_edge.size()))]
			else:
				var pool: Array = []
				for o in rocks:
					if (float(o.height) < 1.7) if edge else (float(o.height) > 0.9): pool.append(o.id)
				pool.append_array(["decor-background-rock", "decor-foreground-rock"])
				if not edge: pool.append("boulder-underwater")
				id = pool[int(floor(H.call(x, y, 26) * pool.size()))]
			objects.append({"x": x, "y": y, "id": id, "dir": dir})
			chosen[_key(x, y)] = id
	objects.append_array(landmarks)

	var seabed: Array = []
	var pickups: Array = []
	var vents: Array = []
	var shells := 0
	for y in range(rows):
		for x in range(cols):
			var ch := str(grid[y])[x]
			if ch == "$": pickups.append({"x": x + 0.5, "y": y + 0.5})
			if ch == ",":
				var r: float = H.call(x, y, 31)
				if r < 0.3: seabed.append({"x": x, "y": y, "id": "decor-starfish", "dir": DIRS[int(floor(H.call(x, y, 32) * 4))], "scale": 0.55})
				elif r < 0.4 and shells < 6 and not sea_floor.is_empty():
					seabed.append({"x": x, "y": y, "id": sea_floor[int(floor(H.call(x, y, 33) * sea_floor.size()))], "dir": DIRS[int(floor(H.call(x, y, 32) * 4))], "scale": 0.7}); shells += 1
			if not solid.call(x, y) and (solid.call(x - 1, y) or solid.call(x + 1, y)) and H.call(x, y, 41) < 0.07: vents.append({"x": x + 0.5, "y": y + 0.85})
	var shafts: Array = []
	for y in range(3, rows, 9): shafts.append({"x": int(floor(H.call(y, 1, 42) * cols)), "y": y, "id": "decor-light-shafts", "dir": "S"})

	# Review/steering guide: nearest open-run centre per row (start at the bottom).
	var autopilot: Array = []
	autopilot.resize(rows)
	var prev := cols / 2.0
	for y in range(rows - 1, -1, -1):
		var opts: Array = runs(str(grid[y]))
		var best: Array = opts[0]
		var best_d := INF
		for run in opts:
			var d := absf((run[0] + run[1] + 1) / 2.0 - prev)
			if d < best_d or (d == best_d and run[0] < best[0]): best_d = d; best = run
		prev = clampf(prev, best[0] + 0.5, best[1] + 0.5)
		if best[1] - best[0] >= 2: prev = (best[0] + best[1] + 1) / 2.0
		autopilot[y] = prev
	var collision: Array = []
	for y in range(rows):
		for x in range(cols):
			if solid.call(x, y): collision.append(Vector2i(x, y))
	return {"columns": cols, "view_columns": VIEW_COLUMNS, "rows": rows, "beds": beds, "objects": objects, "seabed": seabed,
		"pickups": pickups, "vents": vents, "shafts": shafts, "autopilot": autopilot, "collision": collision}
