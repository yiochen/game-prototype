extends RefCounted
## Issue #25 creature discharges: which strikes are fair in a creature chunk.
##
## A creature chunk (route.gd kind "creature") names its species and the
## `attack_rows` where a strike may be live (chunk rows, counted from the top).
## For every strike row in that window and every cell-aligned strip, a strike is
##   - meaningful when the strip lies over `min_open_columns` of open water, and
##   - fair when every position the ship could hold as the windup starts (and
##     would get through the terrain alone from) can still come through: out of
##     the strip, `lane_slack_columns` clear of it, while it is live, without
##     touching rock, after `reaction_seconds` and at `reach_margin` of the real
##     sideways speed. Rock uses the travel collision shapes.
## A chunk is accepted when every strike row offers `min_choices` fair strips.
##
## The search is too slow to run when a dive starts on a phone, so
## tools/discharge_tables.gd stores each chunk's table in its document
## (`chunk.discharge`) with a key over the rows and these rules. The library
## leaves out a creature chunk whose table is missing, stale or rejected, and
## the creature only ever picks from its table. The reference for this review
## is design/eel-strike-preview/fairness.js.

const Route = preload("res://scripts/expedition/route.gd")
const LO := 0.4
const SUB := 6
const SLIDE := 3

## Chase speed once the pursuit ramp is done, in rows per second.
static func chase_rows_per_second(rules: Dictionary) -> float:
	return float(rules.forward_rows_per_second) * float(rules.encounter.pursuit_speed_multiplier)

## Every strip the discharge can choose: [x0, w] pairs, cell-aligned.
static func strips(discharge: Dictionary) -> Array:
	var out: Array = []
	for w in discharge.width_columns:
		for x0 in range(1, Route.COLUMNS - int(w)): out.append([x0, int(w)])
	return out

## Strike rows sampled for a chunk: the row the ship is on as the strike goes
## live. The whole live window lies inside attack_rows and the windup starts
## inside the chunk.
static func strike_rows(rows: Array, attack: Array, rules: Dictionary) -> Array:
	var d: Dictionary = rules.encounter.discharge
	var fwd := chase_rows_per_second(rules)
	var out: Array = []
	var r := float(attack[1])
	while r - float(d.active_seconds) * fwd >= float(attack[0]) - 1e-6:
		if r + float(d.warn_seconds) * fwd <= rows.size() - 0.5: out.append(snappedf(r, 0.001))
		r -= float(d.fairness.row_step)
	return out

## Key over everything the table depends on; a stored table must match it.
static func key(rows: Array, attack: Array, rules: Dictionary) -> String:
	var d: Dictionary = rules.encounter.discharge
	var inputs := [rows, attack, d.width_columns, d.warn_seconds, d.active_seconds, d.fairness, rules.forward_rows_per_second, rules.encounter.pursuit_speed_multiplier,
		rules.lateral_columns_per_second, rules.ship_radius, rules.rock_inset, rules.rock_corner_radius]
	return JSON.stringify(inputs).md5_text()

## {key, strikes: [{row, fair: [[x0, w]…], unfair: [[x0, w]…]}], accepted, problems}.
## `blocked(x, y)` is the travel collision test against these rows.
static func analyze(rows: Array, attack: Array, rules: Dictionary, blocked: Callable) -> Dictionary:
	var d: Dictionary = rules.encounter.discharge
	var f: Dictionary = d.fairness
	var fwd := chase_rows_per_second(rules)
	var dt := 1.0 / (fwd * SUB)
	# Positions are spaced so the ship slides exactly SLIDE positions per step at its reduced speed.
	var step_x := float(rules.lateral_columns_per_second) * float(f.reach_margin) * dt / SLIDE
	var hi := Route.COLUMNS - LO
	var n := int(floor((hi - LO) / step_x)) + 1
	var end := float(d.warn_seconds) + float(d.active_seconds) + float(f.reaction_seconds)
	var steps := int(ceil(end / dt))
	var strikes := strike_rows(rows, attack, rules)
	var problems: Array = []
	if strikes.is_empty(): return {"key": key(rows, attack, rules), "strikes": [], "accepted": false, "problems": ["attack_rows leave no room for a strike"]}
	# Strike rows are row_step apart, a whole number of sub-steps, so every
	# search samples one shared lattice of rows: clear[j] at base - j / SUB.
	var base := float(strikes[0]) + float(d.warn_seconds) * fwd
	var lattice: Array = []
	var last_row := float(strikes[strikes.size() - 1]) + float(d.warn_seconds) * fwd - steps * dt * fwd
	var count := int(round((base - last_row) * SUB)) + 1
	for j in range(count):
		var y := base - float(j) / SUB
		var clear := PackedByteArray(); clear.resize(n)
		for i in range(n): clear[i] = 0 if blocked.call(LO + i * step_x, y) else 1
		lattice.append(clear)
	var half_extra := float(rules.ship_radius) + float(f.lane_slack_columns)
	var out: Array = []
	var bad: Array = []
	for strike in strikes:
		var j0 := int(round((base - (float(strike) + float(d.warn_seconds) * fwd)) * SUB))
		var terrain := _survivors(lattice, j0, steps, n, dt, d, f, -1.0, 0.0, LO, step_x)
		var fair: Array = []
		var unfair: Array = []
		for strip in strips(d):
			if _open_columns(rows, strip, float(strike)) < float(f.min_open_columns): continue
			var centre := float(strip[0]) + float(strip[1]) / 2.0
			var struck := _survivors(lattice, j0, steps, n, dt, d, f, centre, float(strip[1]) / 2.0 + half_extra, LO, step_x)
			var ok := true
			for i in range(n):
				if terrain[i] == 1 and struck[i] == 0: ok = false; break
			(fair if ok else unfair).append(strip)
		out.append({"row": strike, "fair": fair, "unfair": unfair})
		if fair.size() < int(f.min_choices): bad.append(strike)
	if not bad.is_empty(): problems.append("fewer than %d fair strips at rows %s–%s" % [int(f.min_choices), bad.min(), bad.max()])
	return {"key": key(rows, attack, rules), "strikes": out, "accepted": problems.is_empty(), "problems": problems}

## Backwards from the end of the window: which start positions come through.
## `centre` < 0 means no strike (terrain only).
static func _survivors(lattice: Array, j0: int, steps: int, n: int, dt: float, d: Dictionary, f: Dictionary, centre: float, half: float, lo: float, step_x: float) -> PackedByteArray:
	var good: PackedByteArray = lattice[j0 + steps].duplicate()
	var sums := PackedInt32Array(); sums.resize(n + 1)
	var warn := float(d.warn_seconds)
	var live_end := warn + float(d.active_seconds)
	var reaction := float(f.reaction_seconds)
	for k in range(steps - 1, -1, -1):
		var t := k * dt
		var live := centre >= 0.0 and t >= warn and t <= live_end
		var s := 0 if t < reaction else SLIDE
		sums[0] = 0
		for i in range(n): sums[i + 1] = sums[i] + good[i]
		var clear: PackedByteArray = lattice[j0 + k]
		var next := PackedByteArray(); next.resize(n)
		for i in range(n):
			if clear[i] == 0: continue
			if live and absf(lo + i * step_x - centre) < half: continue
			if sums[mini(n, i + s + 1)] - sums[maxi(0, i - s)] > 0: next[i] = 1
		good = next
	return good

static func _open_columns(rows: Array, strip: Array, strike: float) -> float:
	var row: String = rows[clampi(int(floor(strike)), 0, rows.size() - 1)]
	var open := 0
	var x := float(strip[0]) + 0.05
	while x < float(strip[0]) + float(strip[1]):
		if not Route.is_rock(row[int(floor(x))]): open += 1
		x += 0.1
	return open * 0.1

## A stored table is usable when it matches the chunk and rules and was accepted.
static func table_problems(chunk: Dictionary, table: Variant, rules: Dictionary) -> Array:
	if not table is Dictionary or not table.get("strikes") is Array: return ["no discharge table (run tools/discharge_tables.gd)"]
	if str(table.get("key")) != key(chunk.rows, chunk.attack_rows, rules): return ["discharge table is out of date (run tools/discharge_tables.gd)"]
	if not table.get("accepted", false): return ["discharge rejected: %s" % "; ".join(table.get("problems", []))]
	return []
