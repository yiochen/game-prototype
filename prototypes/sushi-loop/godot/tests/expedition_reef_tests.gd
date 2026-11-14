extends SceneTree
## Issue #76 rules: the Boulderhead Parrotfish's broken path, through the public
## command/time/save boundary with a controlled clock. Covers the reef chunks'
## fair-line tables, reef as rock to travel until broken, the parrotfish ramming
## its line open (cracks first, collision gone on the smash), crashing through
## reef off the path (damage, hit protection, slowdown, no knock-back), bedrock
## staying solid, the escape opening every line, the catch and save/restore.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
const Reef = preload("res://scripts/expedition/reef.gd")
const PARROT := "boulderhead-parrotfish"
const SEED := 24
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func run_of(s) -> Variant: return s.snapshot().expedition.run
func live(s) -> Dictionary: return s._state.expedition.run
func types(events: Array) -> Array: return events.map(func(e): return e.type)

func advance(s, seconds: float) -> Array:
	var events: Array = []
	var t := 0.0
	while t < seconds - 0.0001 and run_of(s) != null:
		events.append_array(s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 2000.0 + t}).get("events", []))
		t += 0.05
	return events

func copy(s):
	var restored = Session.new()
	restored.restore(JSON.parse_string(JSON.stringify(s.save_data(), "", true, true)))
	return restored

## A parrotfish run hooked in the arena, at full chase speed.
func hooked(route_seed := SEED):
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": route_seed, "creature": PARROT})
	var r: Dictionary = live(s)
	r.y = float(Book.run_route(r).encounter_start) + 0.02; r.x = 5.5; r.vx = 0.0; r.steer = 0.0
	advance(s, 0.1)
	advance(s, float(Book.definition().encounter.arrive_seconds))
	for shot in range(6):
		live(s).x = Book.creature_centre(live(s)).x; live(s).vx = 0.0
		s.command({"type": "expedition_fire"})
		for i in range(60):
			if "hooked" in types(advance(s, 0.05)): return s
			if live(s).encounter.harpoon == null and float(live(s).encounter.cooldown) <= 0.0: break
	return s

## Hooked, a few rows before the run's `which` reef zone, the creature kept alive.
func at_zone(route_seed: int, which: int):
	var s = hooked(route_seed)
	advance(s, float(Book.definition().encounter.pursuit_ramp_seconds) + 0.1)
	var r: Dictionary = live(s)
	var zone: Dictionary = Book.run_route(r).reef_zones[which]
	r.y = float(zone.y1) + 1.2; r.x = float(zone.xs[0]); r.vx = 0.0
	r.encounter.resistance = 1e6
	return s

## Steer like a careful player: follow the open breach just ahead.
func follow(s, seconds: float) -> Array:
	var events: Array = []
	var t := 0.0
	while t < seconds and run_of(s) != null:
		var r: Dictionary = live(s)
		r.encounter.resistance = 1e6
		var path := Book.run_route(r)
		var zone = Book.reef_zone_at(path, float(r.y))
		if zone != null:
			r.x = Reef.line_at(zone.xs, int(zone.bottom) - int(zone.y0), float(r.y) - float(zone.y0)); r.vx = 0.0
		events.append_array(advance(s, 0.05)); t += 0.05
	return events

func run() -> void:
	var rules := Book.definition()
	var r: Dictionary = rules.encounter.reef

	# --- tables
	var reef_chunks: Array = Book.library().filter(func(c): return c.kind == "creature" and str(c.get("creature")) == PARROT)
	check(reef_chunks.size() == 4, "all four reef chunks join the library with accepted tables")
	for chunk in reef_chunks:
		check(chunk.reef.lines.size() >= int(r.min_lines), "%s keeps at least %d fair lines" % [chunk.id, int(r.min_lines)])
		for xs in chunk.reef.lines:
			check(Reef.fly_line(chunk.rows, xs, rules, 5.5, Book._collides) == null, "%s: the bot follows every stored line" % chunk.id)
	var stale: Dictionary = reef_chunks[0].duplicate(true)
	stale.rows[5] = "#bbbbbbbbb#"
	check(not Reef.table_problems(stale, {"key": "x", "accepted": true, "lines": []}, rules).is_empty(), "a stale table leaves a chunk out")
	check(Book.route(SEED, "storm-eel").reef_zones.is_empty() and Book.route(SEED, "inkfin-cuttlefish").reef_zones.is_empty(), "only the parrotfish's dives meet reef")
	var path := Book.route(SEED, PARROT)
	check(path.reef_zones.size() == 3, "the parrotfish's route has three reef chunks")

	# --- reef is rock to travel until broken; the route treats it as water
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED, "creature": PARROT})
	var zone: Dictionary = path.reef_zones[0]
	var cell: int = int(zone.bottom) * Route.COLUMNS + Reef.breach_cells(float(zone.xs[0]), 2.0)[0]
	check(path.reef_cells.has(cell) and str(path.rows[int(zone.bottom)]).contains("b"), "brittle reef is 'b' in route rows")
	check(str(Book.solid_rows(live(s))[int(zone.bottom)]).count("#") == 11 - str(path.rows[int(zone.bottom)]).count("."), "travel sees standing reef as rock")

	# --- the parrotfish rams its line open
	s = at_zone(SEED, 0)
	var smashes: Array = []
	var cracked := false
	var t := 0.0
	while t < 12.0 and run_of(s) != null:
		var cracks := Book.reef_cracks(live(s))
		for c in cracks:
			if float(cracks[c]) > 0.5: cracked = true
		for e in follow(s, 0.05):
			if e.type == "reef_smash": smashes.append(e)
			check(e.type not in ["impact", "reef_crash"], "following the breach never hits reef or rock (%s)" % e.type)
		if float(live(s).y) < float(zone.top) - 1.0: break
		t += 0.05
	check(cracked, "cracks spread on breach cells before the smash")
	check(not smashes.is_empty() and smashes[0].first and smashes[0].banner, "the first wall is the big entrance, with the banner")
	var line_cells := 0
	for y in range(int(zone.bottom), int(zone.top) - 1, -1): line_cells += Reef.breach_cells(float(zone.xs[int(zone.bottom) - y]), 2.0).size()
	check(live(s).reef_broken.size() == line_cells, "the whole breach is open and nothing else (%d of %d)" % [live(s).reef_broken.size(), line_cells])
	var open := true
	for smash in smashes:
		for c in smash.cells:
			if str(Book.solid_rows(live(s))[int(c.y)])[int(c.x)] != ".": open = false
	check(open, "smashed cells lose collision at once")

	# --- crashing through reef off the path
	s = at_zone(SEED, 0)
	var rr: Dictionary = live(s)
	var off := 1.6 if float(zone.xs[0]) > 5.5 else 9.4
	rr.y = float(zone.bottom) + 1.25; rr.x = off; rr.protection = 0.0
	var hull := float(rr.hull)
	var crash: Array = advance(s, 0.3).filter(func(e): return e.type == "reef_crash")
	check(crash.size() >= 1 and crash[0].hurt and is_equal_approx(float(live(s).hull), hull - float(r.damage)), "ramming reef costs reef damage")
	check(float(live(s).reef_slow) > 0.0 and Book.reef_slowdown(live(s)) < 1.0, "ramming reef slows the ship")
	check(absf(float(live(s).x) - off) < 0.01, "ramming reef has no knock-back")
	var before := float(live(s).hull)
	advance(s, 0.3)
	check(is_equal_approx(float(live(s).hull), before), "hit protection keeps the next crash free")
	live(s).y = float(zone.y1) + 1.2; live(s).x = 5.5
	advance(s, float(r.slow_seconds))
	check(is_equal_approx(Book.reef_slowdown(live(s)), 1.0), "the slowdown wears off")

	# --- bedrock stays solid
	var bed := -1
	var bed_y := -1
	for y in range(int(zone.top), int(zone.bottom) + 1):
		for x in range(1, Route.COLUMNS - 1):
			if str(path.rows[y])[x] == "#" and bed < 0: bed = x; bed_y = y
	check(bed >= 0 and str(Book.solid_rows(live(s))[bed_y])[bed] == "#" and not path.reef_cells.has(bed_y * Route.COLUMNS + bed), "bedrock is never brittle")

	# --- save/restore mid-reef
	s = at_zone(SEED, 0)
	follow(s, 3.0)
	live(s).encounter.resistance = 50.0; live(s).protection = 1.0
	var restored = copy(s)
	check(run_of(restored) != null and live(restored).reef_broken == live(s).reef_broken, "broken reef survives save and restore")
	var data = JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))
	var stored = _find(data, "reef_broken")
	stored.reef_broken.append(0)
	check(not Session.new().restore(data), "a save breaking a non-reef cell is refused")

	# --- escape: the lines are already open
	var e = Session.new_session(7)
	e.command({"type": "expedition_start", "now": 1000.0, "seed": SEED, "creature": PARROT})
	var er: Dictionary = live(e)
	er.y = float(Book.run_route(er).encounter_start) + 0.02; er.x = 1.0; er.vx = 0.0
	var escaped := false
	for i in range(int((float(rules.encounter.window_seconds) + 2.0) / 0.05)):
		live(e).x = 1.0; live(e).protection = 5.0
		if "creature_escaped" in types(advance(e, 0.05)): escaped = true; break
	var total := 0
	for z in path.reef_zones:
		for y in range(int(z.bottom), int(z.top) - 1, -1): total += Reef.breach_cells(float(z.xs[int(z.bottom) - y]), 2.0).size()
	check(escaped and live(e).reef_broken.size() == total, "an escaped parrotfish leaves every line open")

	# --- the catch
	s = at_zone(SEED, 0)
	live(s).encounter.resistance = 0.5
	var caught := advance(s, 0.5)
	check("caught" in types(caught) and "budai_sashimi" in s._state.recipe_book.discovered, "the catch discovers Budai sashimi")

	print("Expedition reef tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() > 0 else 0)

## The dictionary holding `field` somewhere in a save (the run).
func _find(value: Variant, field: String) -> Variant:
	if value is Dictionary:
		if value.has(field): return value
		for v in value.values():
			var found = _find(v, field)
			if found != null: return found
	elif value is Array:
		for v in value:
			var found = _find(v, field)
			if found != null: return found
	return null
