extends RefCounted
## Issue #70 Inkfin ink: which chunks stay fair when the ink limits how far
## ahead the player sees. The reference is design/inkfin-preview/sight.js.
##
## Rows run top (0, the exit) to bottom; the ship travels up. At chase handling
## the ship moves at most `shift` columns sideways per row it rises, sweeping
## through open water only.
##   - safe: cells from which the top of the chunk is still reachable.
##   - doomed: cells reachable from the entry from which it is not.
## For every fork (a safe cell with a doomed next step) the player must see
## the end of the doomed branch before committing: branch depth + 1.5 rows +
## the reaction distance. Any rock needs at least 1.5 rows + the reaction
## distance to dodge. A chunk is fair when its worst need fits the light's
## clear rows and every doomed branch ends inside the cone.

const Route = preload("res://scripts/expedition/route.gd")

static func chase_rows_per_second(rules: Dictionary) -> float:
	return float(rules.forward_rows_per_second) * float(rules.encounter.pursuit_speed_multiplier)

static func shift_per_row(rules: Dictionary) -> int:
	return maxi(1, int(floor(float(rules.lateral_columns_per_second) / chase_rows_per_second(rules))))

static func _open(rows: Array, x: int, y: int) -> bool:
	return y >= 0 and y < rows.size() and x >= 0 and x < str(rows[y]).length() and not Route.is_rock(str(rows[y])[x])

static func _steps(rows: Array, x: int, y: int, shift: int) -> Array:
	var out: Array = []
	for dx in range(-shift, shift + 1):
		var nx := x + dx
		var clear := _open(rows, nx, y - 1)
		for s in range(mini(x, nx), maxi(x, nx) + 1):
			if not clear: break
			if not _open(rows, s, y): clear = false
		if clear: out.append(nx)
	return out

## {need_rows, forks: [{x, y, to, depth, need_rows, look}], entry_traps}.
static func analyze(rows: Array, rules: Dictionary) -> Dictionary:
	var h := rows.size()
	var w := str(rows[0]).length()
	var shift := shift_per_row(rules)
	var reaction := float(rules.encounter.ink.reaction_seconds) * chase_rows_per_second(rules)
	var safe: Array = []
	var reach: Array = []
	var depth: Array = []
	for y in range(h):
		safe.append([]); reach.append([]); depth.append([])
		for x in range(w):
			safe[y].append(false); reach[y].append(false); depth[y].append(null)
	for x in range(w): safe[0][x] = _open(rows, x, 0)
	for y in range(1, h):
		for x in range(w):
			safe[y][x] = _open(rows, x, y) and _steps(rows, x, y, shift).any(func(nx): return safe[y - 1][nx])
	for x in range(w): reach[h - 1][x] = _open(rows, x, h - 1)
	for y in range(h - 1, 0, -1):
		for x in range(w):
			if reach[y][x]:
				for nx in _steps(rows, x, y, shift): reach[y - 1][nx] = true
	# Depth of each doomed cell's branch (rows it can still climb) and the columns its end spans.
	for y in range(h):
		for x in range(w):
			if not reach[y][x] or safe[y][x]: continue
			var d := 0
			var ends: Array = [x]
			if y > 0:
				for nx in _steps(rows, x, y, shift):
					var c = depth[y - 1][nx]
					if c == null: continue
					if int(c.d) + 1 > d: d = int(c.d) + 1; ends = c.ends.duplicate()
					elif int(c.d) + 1 == d: ends.append_array(c.ends)
			depth[y][x] = {"d": d, "ends": ends}
	var forks: Array = []
	var traps := 0
	for y in range(h):
		for x in range(w):
			if y == h - 1 and reach[y][x] and not safe[y][x]: traps += 1
			if not reach[y][x] or not safe[y][x] or y == 0: continue
			for nx in _steps(rows, x, y, shift):
				var c = depth[y - 1][nx]
				if c == null: continue
				var look := 0
				for ex in c.ends: look = maxi(look, absi(int(ex) - x))
				forks.append({"x": x, "y": y, "to": nx, "depth": int(c.d), "need_rows": float(c.d) + 1.5 + reaction, "look": look})
	var inner_rock := false
	for row in rows:
		for x in range(1, w - 1):
			if Route.is_rock(str(row)[x]): inner_rock = true
	var need := 1.5 + reaction if inner_rock else 0.0
	for f in forks: need = maxf(need, float(f.need_rows))
	return {"need_rows": need, "forks": forks, "entry_traps": traps}

## Half-width (columns) the light cone covers `k` rows ahead of the ship.
static func cone_half_width(k: float, ink: Dictionary) -> float:
	var t := clampf(k / float(ink.clear_rows), 0.0, 1.0)
	return lerpf(float(ink.hull_glow_columns), float(ink.cone_far_width_columns) / 2.0, t)

## Problems that keep a chunk out of the ink (empty when fair).
static func problems(rows: Array, rules: Dictionary) -> Array:
	var ink: Dictionary = rules.encounter.ink
	var report := analyze(rows, rules)
	var out: Array = []
	if int(report.entry_traps) > 0: out.append("%d entry cells are already trapped" % int(report.entry_traps))
	if float(report.need_rows) > float(ink.clear_rows) + 1e-6: out.append("needs %.1f clear rows" % float(report.need_rows))
	for f in report.forks:
		if float(f.need_rows) <= float(ink.clear_rows) + 1e-6 and float(f.look) > cone_half_width(float(f.need_rows), ink) + 0.5 + float(f.need_rows) * tan(deg_to_rad(float(ink.tilt_degrees))):
			out.append("fork at row %d col %d hides its dead end %d columns to the side" % [int(f.y), int(f.x), int(f.look)])
	return out
