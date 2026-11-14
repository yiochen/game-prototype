extends RefCounted
## Issue #76 Boulderhead Parrotfish reef: the parrotfish's fair lines.
##
## A reef chunk is a creature chunk packed with brittle reef ('b', the map's
## `reef-brittle` obstacles) round a few bedrock outcrops ('#'), with open
## water at the entry (bottom) and exit (top). To the route brittle reef is
## water; to travel it is rock until something breaks it.
##
## A line is the parrotfish's course: one column centre per reef row, bottom to
## top. The breach is every brittle cell the line's `breach_columns`-wide strip
## overlaps by at least OVERLAP. A line is valid when its strip never touches
## bedrock, and fair when a steering bot with the ship's real handling, a
## reaction delay and no more look-ahead than the parrotfish's lead follows it
## from the left, centre and right of the entry without touching reef. Each
## chunk keeps up to `lines_per_chunk` fair lines; a dive picks one per chunk.
##
## The search is too slow for a phone at dive start, so tools/reef_tables.gd
## stores each chunk's lines in its document (`chunk.reef`) with a key over the
## rows and these rules, as discharge.gd does. The reference is
## design/boulderhead-preview/reef.js.

const Route = preload("res://scripts/expedition/route.gd")
const OVERLAP := 0.35
const SEED := 76
const STARTS := [1.6, 5.5, 9.4]

## The reef rows of a chunk as [first, last], counted from the top ([] if none).
static func reef_rows(rows: Array) -> Array:
	var first := -1
	var last := -1
	for y in range(rows.size()):
		if "b" in str(rows[y]):
			if first < 0: first = y
			last = y
	return [] if first < 0 else [first, last]

## Columns a strip centred on x breaks in a row.
static func breach_cells(x: float, width: float) -> Array:
	var out: Array = []
	var a := x - width / 2.0
	var b := x + width / 2.0
	for cx in range(int(floor(a)), int(floor(b)) + 1):
		if minf(b, cx + 1.0) - maxf(a, float(cx)) >= OVERLAP: out.append(cx)
	return out

## Line x at a chunk row (fractional, rows from the top); the aprons hold the end values.
static func line_at(xs: Array, bottom: int, y: float) -> float:
	var i := clampf(bottom + 0.5 - y, 0.0, xs.size() - 1.0)
	var k := int(floor(i))
	var f := i - k
	return float(xs[k]) + (float(xs[k + 1]) - float(xs[k])) * f if k + 1 < xs.size() else float(xs[k])

## Carve one line bottom to top, or [] when the chunk boxes it in.
static func carve_line(rows: Array, rng, reef: Dictionary) -> Array:
	var span := reef_rows(rows)
	var top: int = span[0]
	var bottom: int = span[1]
	var n := bottom - top + 1
	var width := float(reef.breach_columns)
	var lo := 1.0 + width / 2.0 - OVERLAP + 0.05
	var hi := Route.COLUMNS - lo
	var steps: Array = []
	var s := -float(reef.max_shift_columns)
	while s <= float(reef.max_shift_columns) + 1e-9:
		steps.append(snappedf(s, 0.1)); s += 0.2
	# Waypoints every few rows make it wind; depth-first search with backtracking keeps it inside the reef.
	var targets: Array = []
	for i in range(int(ceil(n / 4.0)) + 1): targets.append(lo + rng.next() * (hi - lo))
	var ctx := {"rows": rows, "rng": rng, "width": width, "lo": lo, "hi": hi, "steps": steps, "targets": targets, "bottom": bottom, "n": n, "xs": []}
	ctx.xs.resize(n)
	for tries in range(12):
		if _go(ctx, 0, snappedf(lo + rng.next() * (hi - lo), 0.1)): return ctx.xs
	return []

static func _go(ctx: Dictionary, i: int, x: float) -> bool:
	if x < ctx.lo or x > ctx.hi: return false
	var row: String = ctx.rows[ctx.bottom - i]
	for cx in breach_cells(x, ctx.width):
		if row[cx] == "#": return false
	ctx.xs[i] = x
	if i == ctx.n - 1: return true
	var t: float = ctx.targets[int(floor((i + 1) / 4.0))]
	var order: Array = ctx.steps.map(func(s): return {"s": s, "w": -absf(x + s - t) + ctx.rng.next() * 1.2})
	order.sort_custom(func(p, q): return p.w > q.w)
	for o in order:
		if _go(ctx, i + 1, snappedf(x + o.s, 0.1)): return true
	return false

## Rows for travel with the line's breach open: intact brittle reef counts as rock.
static func carved_rows(rows: Array, xs: Array, reef: Dictionary) -> Array:
	var bottom: int = reef_rows(rows)[1]
	var grid: Array = rows.map(func(r): return str(r).replace("b", "#"))
	for i in range(xs.size()):
		var y := bottom - i
		for cx in breach_cells(float(xs[i]), float(reef.breach_columns)):
			grid[y] = str(grid[y]).substr(0, cx) + "." + str(grid[y]).substr(cx + 1)
	return grid

## Steering bot: real handling at chase speed, a reaction delay and look-ahead no
## further than the parrotfish's head. Returns where it first touches reef, or null.
## `collides(rows, x, y, reach)` is the travel collision test.
static func fly_line(rows: Array, xs: Array, rules: Dictionary, start_x: float, collides: Callable) -> Variant:
	var reef: Dictionary = rules.encounter.reef
	var bottom: int = reef_rows(rows)[1]
	# The ship arrives from the previous chunk: four rows of open water below the entry stand in for it.
	var grid := carved_rows(rows, xs, reef)
	for i in range(4): grid.append("#.........#")
	var fwd := float(rules.forward_rows_per_second) * float(rules.encounter.pursuit_speed_multiplier)
	var dt := 1.0 / 60.0
	var look := float(reef.bot_look_rows)
	var delay := int(round(float(reef.reaction_seconds) / dt))
	var x := start_x
	var y := grid.size() - 0.6
	var vx := 0.0
	var seen: Array = []
	while y > 0.6:
		seen.append(line_at(xs, bottom, y - look))
		var goal: float = seen[maxi(0, seen.size() - 1 - delay)]
		var want := 0.0 if absf(goal - x) < 0.06 else signf(goal - x) * minf(1.0, absf(goal - x) * 3.0) * float(rules.lateral_columns_per_second)
		vx += clampf(want - vx, -float(rules.lateral_acceleration) * dt, float(rules.lateral_acceleration) * dt)
		x += vx * dt; y -= fwd * dt
		if collides.call(grid, x, y, float(rules.ship_radius)): return Vector2(x, y)
	return null

## Key over everything the table depends on; a stored table must match it.
static func key(rows: Array, rules: Dictionary) -> String:
	var inputs := [rows, rules.encounter.reef.breach_columns, rules.encounter.reef.max_shift_columns, rules.encounter.reef.candidate_lines, rules.encounter.reef.lines_per_chunk,
		rules.encounter.reef.bot_look_rows, rules.encounter.reef.reaction_seconds, rules.forward_rows_per_second, rules.encounter.pursuit_speed_multiplier,
		rules.lateral_columns_per_second, rules.lateral_acceleration, rules.ship_radius, rules.rock_inset, rules.rock_corner_radius, SEED]
	return JSON.stringify(inputs).md5_text()

## {key, lines: [[x per reef row, bottom to top]…], rejected, accepted, problems}.
static func analyze(chunk: Dictionary, rules: Dictionary, collides: Callable) -> Dictionary:
	var reef: Dictionary = rules.encounter.reef
	var rows: Array = chunk.rows
	var out := {"key": key(rows, rules), "lines": [], "rejected": 0, "accepted": false, "problems": []}
	if reef_rows(rows).is_empty():
		out.problems.append("no brittle reef"); return out
	var rng := Route.Mulberry32.new(SEED + str(chunk.id).length() * 131)
	for k in range(int(reef.candidate_lines)):
		if out.lines.size() >= int(reef.lines_per_chunk): break
		var xs := carve_line(rows, rng, reef)
		if xs.is_empty(): continue
		var hit = null
		for sx in STARTS:
			var at = fly_line(rows, xs, rules, sx, collides)
			if hit == null: hit = at
		if hit == null: out.lines.append(xs)
		else: out.rejected += 1
	if out.lines.size() < int(reef.min_lines): out.problems.append("only %d fair lines (need %d)" % [out.lines.size(), int(reef.min_lines)])
	out.accepted = out.problems.is_empty()
	return out

## Why a stored table cannot be used (empty when it can).
static func table_problems(chunk: Dictionary, table, rules: Dictionary) -> Array:
	if not table is Dictionary: return ["no reef table (run tools/reef_tables.gd)"]
	if str(table.get("key")) != key(chunk.rows, rules): return ["reef table is stale (run tools/reef_tables.gd)"]
	if not table.get("accepted", false): return ["reef table rejected: %s" % "; ".join(table.get("problems", []))]
	var span := reef_rows(chunk.rows)
	var lines = table.get("lines")
	if not lines is Array or lines.is_empty() or lines.any(func(l): return not l is Array or l.size() != int(span[1]) - int(span[0]) + 1): return ["reef table lines do not fit the chunk"]
	return []
