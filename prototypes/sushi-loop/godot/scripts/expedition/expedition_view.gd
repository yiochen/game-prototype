extends Control
## Expedition playfield (issue #21). Draws the seeded route with the approved
## production pieces over the ground layer, following the HTML review's draw
## order: floor, rock shadow, fish, seabed decor, ship shadow, beds, gold,
## rows north→south (any row whose base is south of the hull's covers it, so the
## ship slips behind rocks it passes north of), particles, light shafts. The screen shows VIEW_COLUMNS of the world
## and follows the ship sideways. Steering is two rounded, translucent arrow
## buttons in the bottom corners: holding one moves the ship that way (each
## half of the screen counts as its button) and letting go runs straight. On
## the preparation screen the first press starts the dive; it steers only
## when it lands on an arrow.
##
## Issue #22: current fields, shield pickups and the portal are drawn on the
## main route; a portal ride switches to that portal's bonus passage (its own
## grid) through a whirlpool transition, during which `transitioning()` holds
## the presentation's travel. Feature drawing lives in feature_art.gd.
##
## Issue #23: the encounter creature is live 3D (creature_view.gd) drawn after
## the seabed and pickups, with soft shadows along its spine. The harpoon and
## its rope draw over the world from the ship's nose; a hook pins the harpoon
## to the struck body part so it rides every animation. `focus_amount` (set by
## the presentation's slow motion) dims the scene outside a closing circle.
const Route = preload("res://scripts/expedition/route.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Art = preload("res://scripts/expedition/feature_art.gd")
const Harpoon = preload("res://scripts/expedition/harpoon_art.gd")
const CreatureView = preload("res://scripts/expedition/creature_view.gd")
const DischargeArt = preload("res://scripts/expedition/discharge_art.gd")
const ShipArt = preload("res://scripts/ship_art.gd")
const WorkshopBook = preload("res://scripts/workshop_book.gd")
## The ImageGen ship (#28): hull 1.04 cells tall, centred 0.21 cells above the ship root.
const SHIP_HULL_CELLS := 1.04
const SHIP_HULL_LIFT := 0.21

signal steered(input: float)
signal pressed_down

var pieces: Dictionary = {}
var textures: Dictionary = {}
var scene: Dictionary = {}
var by_row: Array = []
## Drawn worlds by key: the main route ("main:seed:version") and passages ("passage:seed:portal").
var worlds: Dictionary = {}
var world: Dictionary = {}
var run_state: Dictionary = {}
## The current shield's starting length, so its rim drains from full whether it
## came from a pickup or the launch (presentation only).
var _shield_peak := 0.0
## Arrows dim while the passage current steers.
var controls_disabled := false
const MAX_TILT := 0.3
var _tr: Dictionary = {}
var _outflow: Dictionary = {}
var _bump := 0.0
var ship := Vector2(5.5, 0.0)
var cam_x := 5.5
var time := 0.0
var collected: Dictionary = {}
var protection := 0.0
var steering_enabled := false
var reduced_motion := false
var particles: Array = []
var vents: Dictionary = {}
var fish: Array = []
## Shown on preparation and while travelling; hidden behind overlays.
var controls_visible := false
## Keyboard arrows, mirrored on the buttons.
var key_input := 0.0
var _held: Dictionary = {}  # touch index -> -1 left, 1 right, 0 (dive press off the arrows)
var _stick := 0.0
var _trail := 0.0
var _thrust := 0.0
var _prev_x := 5.5
var _side := 0.0
var _turn := 0.0
var _hit := 0.0
## Hull hit: the damage wobble/red flash (1 -> 0), and the knock-back still to
## slide out (cells, from where the rules put the ship back to where it struck).
var _hurt := 0.0
var _knock := Vector2.ZERO
## Banking into a turn (radians, eased toward the steering velocity).
var _tilt := 0.0
var _bubble: Texture2D
var _glow: Texture2D
var _shade: Texture2D
var _v2: Array = []
var _rng := RandomNumberGenerator.new()
var creature: CreatureView
## Slow-motion focus 0..1 and where it closes (view coordinates).
var focus_amount := 0.0
var focus_at := Vector2.ZERO
var _creature_shown := false
var _hooked_at := -1.0
## Issue #24 endings, played over the frozen last run: seconds since the catch
## (the eel drawn in, rays, the harpoon reeled home) or the escape (cable
## snaps, the eel bursts away north). -1 when not playing.
var catch_t := -1.0
var escape_t := -1.0
var _catch_from := Vector2.ZERO
const RETRACT_START := 0.4
const RETRACT_SECONDS := 1.0
## Issue #25 discharge: the last strike's afterglow, live bolts and screen flash.
var _afterglow := {}
var _last_strike = null
var _bolts: Array = []
var _bolt_t := 0.0
var _strike_flash := 0.0
## Issue #70 ink: a shader layer above the creature (ink.gdshader), and a layer
## above that for what stays visible through the ink: the cable, glowing
## pickups and the steering arrows.
var _ink_layer: ColorRect
var _over_layer: Control
var _ink_material: ShaderMaterial
var _cone_tilt := 0.0
var _lime: Texture2D
var _puff: Texture2D
## Hull losses rising off the ship ({text, age}).
var _losses: Array = []
## Issue #76 reef: when each cell broke (view time; unknown breaks draw settled).
var _reef_broke_at: Dictionary = {}

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE
	accessibility_name = "Expedition. Hold the left or right arrow to steer."
	clip_contents = true
	pieces = JSON.parse_string(FileAccess.get_file_as_string("res://assets/expedition/pieces.json"))
	for id in pieces.objects:
		var o: Dictionary = pieces.objects[id]
		if o.family in ["rock", "ruin", "landmark", "sealife-edge", "sealife-floor"]:
			var entry := {"id": id, "family": o.family}
			if o.has("height"): entry.height = o.height
			_v2.append(entry)
	_bubble = _make_bubble()
	_glow = _radial([Color(1, .89, .47, .55), Color(1, .75, .24, .22), Color(1, .67, .16, 0)], [0.0, .45, 1.0])
	_shade = _radial([Color(.016, .118, .275, .5), Color(.016, .118, .275, .3), Color(.016, .118, .275, 0)], [0.0, .55, 1.0])
	creature = CreatureView.new(self)
	_puff = _radial([Color(.94, .91, .82, .9), Color(.94, .91, .82, 0)], [0.0, 1.0])
	_lime = _radial([Color(.75, 1, .35, .55), Color(.63, 1, .24, .22), Color(.63, 1, .24, 0)], [0.0, .45, 1.0])
	_ink_material = ShaderMaterial.new()
	_ink_material.shader = load("res://scripts/expedition/ink.gdshader")
	_ink_layer = ColorRect.new()
	_ink_layer.material = _ink_material
	_over_layer = Control.new()
	for layer: Control in [_ink_layer, _over_layer]:
		layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
		layer.set_anchors_preset(Control.PRESET_FULL_RECT)
		layer.visible = false
		add_child(layer)
	_over_layer.draw.connect(_draw_over)

static func _radial(colors: Array, offsets: Array) -> Texture2D:
	var gradient := Gradient.new()
	gradient.offsets = PackedFloat32Array(offsets)
	gradient.colors = PackedColorArray(colors)
	var texture := GradientTexture2D.new()
	texture.gradient = gradient; texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(.5, .5); texture.fill_to = Vector2(1, .5); texture.width = 64; texture.height = 64
	return texture

## Bubble: faint body, bright rim and a highlight (matches the review sprite).
static func _make_bubble() -> Texture2D:
	var size := 64
	var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var c := Vector2(size, size) * .5
	for y in range(size):
		for x in range(size):
			var d := (Vector2(x + .5, y + .5) - c).length() / (size * .5 - 2)
			var color := Color(0, 0, 0, 0)
			if d <= 1.0:
				var rim := smoothstep(.72, 1.0, d)
				color = Color(.82, .96, 1.0, lerpf(.08, .85, rim))
			var h := Vector2(x + .5 - size * .36, (y + .5 - size * .33) * 1.5).length() / (size * .14)
			if h < 1.0: color = color.lerp(Color(1, 1, 1, .95), 1.0 - h)
			image.set_pixel(x, y, color)
	return ImageTexture.create_from_image(image)

func texture(path: String) -> Texture2D:
	if not textures.has(path): textures[path] = load("res://assets/expedition/" + path)
	return textures[path]

func set_route(seed_value: int, species := "") -> void:
	_use(_main_world(seed_value, species))

func _main_world(seed_value: int, species := "") -> Dictionary:
	var path := Book.route(seed_value, species)
	var key := "main:%d:%d:%s" % [seed_value, int(path.version), str(path.creature)]
	if not worlds.has(key):
		var w := _make_world(path.rows, seed_value, "main")
		w.path = path
		if not path.reef_zones.is_empty(): _reef_world(w)
		w.streaks = Art.streaks(path.currents, path.rows.size(), seed_value)
		worlds[key] = w
	return worlds[key]

func _passage_world(seed_value: int, portal: int, rows: int) -> Dictionary:
	var key := "passage:%d:%d:%d" % [seed_value, portal, rows]
	if not worlds.has(key):
		var info := Book.passage(seed_value, portal, rows)
		var w := _make_world(info.rows, seed_value * 7 + portal + 11, "passage")
		w.info = info
		w.flow = Art.flow_lines(info.rows.size(), seed_value + portal)
		worlds[key] = w
	return worlds[key]

func _make_world(rows: Array, seed_value: int, kind: String) -> Dictionary:
	var composed := Route.compose_scene(rows, _v2, seed_value)
	var rows_by: Array = []
	rows_by.resize(composed.rows)
	for y in range(composed.rows): rows_by[y] = []
	for o in composed.objects: rows_by[int(o.y)].append(o)
	var r := Route.Mulberry32.new(seed_value * 31)
	var school: Array = []
	for i in range(int(ceil(composed.rows / 13.0))):
		school.append({"y": 4 + i * 13 + r.next() * 6, "speed": .25 + r.next() * .25, "dir": -1 if i % 2 else 1, "phase": r.next() * 20})
	return {"kind": kind, "scene": composed, "by_row": rows_by, "fish": school, "collected": {}}

## Issue #76: in reef chunks every rock is dark (no pale ruins, coral or arches),
## so pale always means breakable; and the reef art starts loading in the background.
func _reef_world(w: Dictionary) -> void:
	var dark: Array = _v2.filter(func(e): return e.family == "rock").map(func(e): return e.id) + ["boulder-underwater", "decor-background-rock"]
	var spans: Array = w.path.reef_zones
	var inside := func(y: int) -> bool: return spans.any(func(z): return y >= int(z.y0) and y <= int(z.y1))
	var pick := func(x: int, y: int) -> String: return dark[int(Route.cell_hash(x, y, 77) * dark.size()) % dark.size()]
	for y in range(w.by_row.size()):
		if not inside.call(y): continue
		var row: Array = []
		for o in w.by_row[y]:
			if int(o.get("w", 1)) > 1:
				for x in [int(o.x), int(o.x) + int(o.w) - 1]: row.append({"x": x, "y": y, "id": pick.call(x, y), "dir": "S"})
			else: row.append({"x": o.x, "y": o.y, "id": pick.call(int(o.x), y), "dir": o.dir})
		w.by_row[y] = row
	for entry in pieces.reef.pieces.values():
		for key in ["static", "break"]:
			if entry[key] == null or textures.has(entry[key]): continue
			var full: String = "res://assets/expedition/" + str(entry[key])
			if ResourceLoader.load_threaded_get_status(full) == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE: ResourceLoader.load_threaded_request(full)

func _reef_texture(path: String) -> Texture2D:
	if not textures.has(path):
		var full := "res://assets/expedition/" + path
		var status := ResourceLoader.load_threaded_get_status(full)
		textures[path] = ResourceLoader.load_threaded_get(full) if status in [ResourceLoader.THREAD_LOAD_IN_PROGRESS, ResourceLoader.THREAD_LOAD_LOADED] else load(full)
	return textures[path]

## Make `w` the drawn world (scene, rows and fish are its aliases).
func _use(w: Dictionary) -> void:
	if w == world: return
	world = w; scene = w.scene; by_row = w.by_row; fish = w.fish; collected = w.collected
	particles.clear(); vents.clear()

## Whirlpool between the main route and a passage. The old world and ship
## position stay on screen until the iris closes; the run is already across.
func begin_transition(kind: String, from_ship: Vector2) -> void:
	_tr = {"kind": kind, "t": 0.0, "ship": from_ship, "switched": false}

func transitioning() -> bool: return not _tr.is_empty()

func _transition_seconds() -> float:
	return .3 if reduced_motion else float(Book.definition().portal_transition_seconds)

## Called each frame by the presentation with the current run snapshot.
func sync(run: Dictionary, delta: float, travelling: bool) -> void:
	run_state = run
	var main := _main_world(int(run.seed), Book.creature_of(run))
	main.collected = _index_set(run.get("collected", []))
	var ride = run.get("passage")
	var target := main
	if ride is Dictionary:
		target = _passage_world(int(run.seed), int(ride.portal), int(Book.gear(run).passage))
		target.collected = _index_set(ride.collected)
		ship = Vector2(float(ride.x), float(ride.y))
	else:
		ship = Vector2(float(run.x), float(run.y))
	time += delta
	_hit = maxf(0.0, _hit - delta * 3.0)
	_bump = maxf(0.0, _bump - delta * 4.0)
	_hurt = maxf(0.0, _hurt - delta * 1.8)
	_knock *= exp(-delta * 14.0)
	var lateral := float(Book.definition().lateral_columns_per_second)
	var bank := clampf(float(run.get("vx", 0.0)) / lateral, -1.0, 1.0) * MAX_TILT if ride == null else 0.0
	_tilt = lerpf(_tilt, bank, minf(1.0, delta * 10.0))
	protection = float(run.protection)
	if _tr.is_empty():
		_use(target)
	else:
		_tr.t = float(_tr.t) + delta / _transition_seconds()
		if float(_tr.t) >= .5 and not _tr.switched:
			_tr.switched = true; _use(target); snap_camera()
			if _tr.kind == "exit": _outflow = {"p": ship, "t": 0.0}
		if float(_tr.t) >= 1.0: _tr = {}
	collected = world.collected
	if not _outflow.is_empty():
		_outflow.t = float(_outflow.t) + delta / 1.6
		if float(_outflow.t) >= 1.0: _outflow = {}
	var half := Route.VIEW_COLUMNS / 2.0
	var shown := _shown_ship()
	var offset := shown.x - cam_x
	var want := shown.x - signf(offset) * .7 if absf(offset) > .7 else cam_x
	cam_x += (clampf(want, half, Route.COLUMNS - half) - cam_x) * minf(1.0, delta * 4.0)
	if travelling and _tr.is_empty() and not reduced_motion: _emit(delta)
	var ending := catch_t >= 0.0 or escape_t >= 0.0
	if ending:
		if catch_t >= 0.0:
			var was := catch_t
			catch_t += delta
			if was < RETRACT_START and catch_t >= RETRACT_START: _release_burst()
		if escape_t >= 0.0: escape_t += delta
	_step_particles(delta if travelling or ending else 0.0, delta)
	for l in _losses: l.age = float(l.age) + delta
	_losses = _losses.filter(func(l): return float(l.age) < .9)
	_sync_discharge(delta if travelling else 0.0)
	_sync_creature(run, delta if travelling or ending else 0.0)
	_sync_ink(run, delta if travelling else 0.0)
	queue_redraw()

## Encounter creature: clip from the rules state, camera on its route cell.
func _sync_creature(run: Dictionary, delta: float) -> void:
	var encounter = run.get("encounter")
	if encounter == null: _hooked_at = -1.0
	_creature_shown = encounter is Dictionary and world.get("kind") == "main" and _tr.is_empty()
	if _creature_shown and encounter.state == "escaped":
		# The escape clip carries it off north; then it is gone.
		_creature_shown = float(encounter.t) - float(encounter.get("escaped_at", encounter.t)) < 1.6
	if not _creature_shown:
		creature.stop_rendering(); return
	creature.use(Book.creature_of(run))
	var rules: Dictionary = Book.definition().encounter
	match str(encounter.state):
		"aiming": creature.play("restless" if float(encounter.t) >= float(rules.window_seconds) - float(rules.restless_seconds) else "swim")
		"hooked":
			# Pursuit: straining forward, thrashing once resistance runs low.
			var low := float(encounter.get("resistance", rules.resistance)) < float(rules.resistance) * .3
			var strike = encounter.get("discharge")
			var blot = encounter.get("ink")
			if catch_t >= 0.0: creature.play("exhausted", .35)
			elif escape_t >= 0.0: creature.play("escape", .15)
			elif strike is Dictionary: creature.play("windup" if strike.phase == "windup" else "attack", .15)
			# Ink: the sac swells through the warning, then the burst as it spreads.
			elif blot is Dictionary and blot.phase == "warn": creature.play("windup", .15)
			elif blot is Dictionary and blot.phase == "spread" and (creature.clip == "windup" or (creature.clip == "attack" and not creature.finished())): creature.play("attack", .1)
			elif creature.clip == "hit":
				if creature.finished(): creature.play("struggle" if low else "hooked")
			elif creature.clip not in ["hooked", "struggle"]:
				# A hook restored from a save starts straight in the chase loop.
				creature.play("hit" if _hooked_at >= 0.0 else "hooked", 0.1)
			else: creature.play("struggle" if low else "hooked")
		"escaped": creature.play("escape", 0.15)
	var cell := _cell()
	var centre := Book.creature_centre(run)
	var root := _origin() + Vector2(centre.x, centre.y + float(creature.profile.row_offset)) * cell
	var grow := 1.0
	var turn := 0.0
	if catch_t >= 0.0:
		# The caught eel is drawn into the upper middle, grows and turns a little.
		if _catch_from == Vector2.ZERO: _catch_from = root
		var k := 1.0 if reduced_motion else smoothstep(0.0, 1.0, catch_t / .9)
		root = _catch_from.lerp(Vector2(size.x * .5, size.y * .4), k)
		grow = 1.0 + .45 * k; turn = -.45 * k
	elif escape_t >= 0.0:
		root.y -= escape_t * escape_t * 6.0 * cell
	# Issue #76: the parrotfish lies along its line (head and tail on it).
	if creature.body != null:
		var path: Dictionary = world.path
		var nose := Book.reef_nose(run)
		var reach := float(Book.species(Book.creature_of(run)).get("nose_rows", 1.0)) * 2.0
		var head = Book._line_at(path, nose)
		var tail = Book._line_at(path, nose + reach)
		var want := atan2(-(float(head) - float(tail)), reach / sin(CreatureView.ELEVATION)) if head != null and tail != null and encounter.state == "hooked" and catch_t < 0.0 else 0.0
		creature.heading = lerpf(creature.heading, want, minf(1.0, delta * 6.0))
	creature.pose(grow, turn)
	creature.frame(delta, root, size, cell, maxf(.001, get_viewport_transform().get_scale().x * get_global_transform().get_scale().x))

## The creature's current discharge, while the chase is on (a catch or escape removes it).
func discharge() -> Variant:
	if not _pursuit() or world.get("kind") != "main": return null
	return run_state.encounter.get("discharge")

## The Inkfin's current ink burst, while the chase is on (a catch or escape removes it).
func ink() -> Variant:
	if not _pursuit() or world.get("kind") != "main": return null
	return run_state.encounter.get("ink")

## Drive the ink layer from the rules state: the cover, the light cone and its
## tilt into the turn, and the warning pulse.
func _sync_ink(run: Dictionary, delta: float) -> void:
	var k: Dictionary = Book.definition().encounter.ink
	var blot = ink()
	var lateral := float(Book.definition().lateral_columns_per_second)
	var want := clampf(float(run.get("vx", 0.0)) / lateral, -1.0, 1.0) * deg_to_rad(float(k.tilt_degrees)) if blot is Dictionary else 0.0
	_cone_tilt = lerpf(_cone_tilt, want, minf(1.0, delta * 8.0)) if blot is Dictionary else 0.0
	_ink_layer.visible = blot is Dictionary
	_over_layer.visible = blot is Dictionary
	if not blot is Dictionary: return
	var cell := _cell()
	var o := _origin()
	var cover := Book.ink_cover(run)
	var pulse := 0.0
	if blot.phase == "warn": pulse = .3 if reduced_motion else .38 * (.5 - .5 * cos(TAU * 3.0 * float(blot.t) / float(k.warn_seconds)))
	var from := creature.to_view(creature.bone_world(str(creature.profile.front))) if _creature_shown else size * Vector2(.5, .35)
	for entry in [["view_size", size], ["cell", cell], ["ship", o + (_shown_ship() + _knock) * cell], ["origin", from], ["scroll", o],
			["cover", cover], ["bloom", 1.0 if blot.phase == "spread" else 0.0], ["warn", pulse], ["tilt", _cone_tilt],
			["clear_rows", float(k.clear_rows)], ["far_half_columns", float(k.cone_far_width_columns) / 2.0], ["glow_columns", float(k.hull_glow_columns)],
			["darkness", float(k.darkness)], ["tint", float(k.light_tint)], ["drift", 0.0 if reduced_motion else time * .033]]:
		_ink_material.set_shader_parameter(entry[0], entry[1])
	_over_layer.queue_redraw()

## Above the ink: pickups glow through it with the dive's lime "good" signal,
## and the cable and the arrows stay as they are.
func _draw_over() -> void:
	if scene.is_empty(): return
	var cell := _cell()
	var o := _origin()
	var cover := Book.ink_cover(run_state)
	var top_row := _top_row()
	for i in range(scene.pickups.size()):
		var p: Dictionary = scene.pickups[i]
		if cover <= 0.0 or collected.has(i) or p.y < top_row - 1.0 or p.y > top_row + size.y / cell + 1.0: continue
		var bob := sin(time * 2.4 + i) * .05
		var g := o + Vector2(p.x, p.y - .15 + bob) * cell
		var pulse := 1.0 if reduced_motion else .85 + .15 * sin(time * 4.0 + i)
		_over_layer.draw_texture_rect(_lime, Rect2(g - Vector2.ONE * cell * .62 * pulse, Vector2.ONE * cell * 1.24 * pulse), false, Color(1, 1, 1, cover))
		var entry: Dictionary = pieces.kit.get("gold-%02d" % (posmod(int(floor(time * 10 + i * 3)), 12)), {})
		if entry.is_empty(): continue
		var s := cell * 1.5 / float(pieces.kitCellPixels)
		var at := o + Vector2(p.x - .75, p.y - .75 + bob - .12) * cell
		_over_layer.draw_texture_rect(texture(str(entry.image)), Rect2(at - Vector2(float(entry.origin[0]), float(entry.origin[1])) * s, Vector2(float(entry.size[0]), float(entry.size[1])) * s), false, Color(1, 1, 1, .85 * cover))
	_draw_harpoon(cell, _over_layer)
	_draw_controls(_over_layer)

func _sync_discharge(delta: float) -> void:
	var strike = discharge()
	# A finished strike leaves a short afterglow; a catch or escape clears everything.
	if strike == null and _last_strike is Dictionary and _last_strike.phase == "strike" and _pursuit():
		_afterglow = {"x0": _last_strike.x0, "w": _last_strike.w, "t": 0.0}
	if not _pursuit(): _afterglow = {}; _bolts = []; _strike_flash = 0.0
	_last_strike = strike.duplicate() if strike is Dictionary else null
	if not _afterglow.is_empty():
		_afterglow.t = float(_afterglow.t) + delta
		if float(_afterglow.t) >= .3: _afterglow = {}
	_strike_flash = maxf(0.0, _strike_flash - delta * 6.0)
	_bolt_t += delta
	if strike is Dictionary and strike.phase == "strike" and (_bolts.is_empty() or _bolt_t > (.2 if reduced_motion else .06)) and delta > 0.0:
		_bolt_t = 0.0
		var cell := _cell()
		var x0 := _origin().x + float(strike.x0) * cell
		var w := float(strike.w) * cell
		var from := clampf(creature.to_view(creature.bone_world(str(creature.profile.front))).y, 0.0, size.y) if _creature_shown else 0.0
		_bolts = [DischargeArt.bolt_path(_rng, x0, w, from, size.y, cell), DischargeArt.bolt_path(_rng, x0, w, from, size.y, cell), DischargeArt.bolt_path(_rng, x0, w, -10.0, from, cell)]
	elif not (strike is Dictionary and strike.phase == "strike"): _bolts = []

## The strike goes live: a soft screen flash and a small shake.
func discharge_strike() -> void:
	_strike_flash = 1.0; _bolts = []
	_hit = maxf(_hit, .6)

## Lightning hit: the red hull tint and electric sparks, without knock-back.
func zap(at: Vector2) -> void:
	_hurt = 1.0
	if reduced_motion: return
	for i in range(18):
		var a := _rng.randf() * TAU
		particles.append({"kind": "spark", "p": at + Vector2(_rng.randf_range(-.25, .25), -.3 - _rng.randf() * .4), "v": Vector2(cos(a), sin(a)) * (1.2 + _rng.randf() * 2.4), "r": .03 + _rng.randf() * .03, "life": .35 + _rng.randf() * .3, "age": 0.0, "drag": 4.0, "color": Color(.75, .96, 1) if i % 3 else Color(1, .96, .72)})

## The presentation reports a fresh hook (the hit reaction and flash ring play).
func hooked() -> void:
	_hooked_at = time

func _pursuit() -> bool:
	var encounter = run_state.get("encounter")
	return encounter is Dictionary and encounter.state == "hooked" and catch_t < 0.0 and escape_t < 0.0

## Issue #24 endings over the frozen last run (the rules have already ended it).
func start_catch() -> void:
	catch_t = 0.0; _catch_from = Vector2.ZERO
	_clear_discharge()
	var c := Book.creature_centre(run_state)
	if reduced_motion: return
	for i in range(26):
		_bubble_at(c.x + _rng.randf_range(-1.0, 1.0), c.y + _rng.randf_range(-.6, 1.4), _rng.randf_range(-.6, .6), -.6 - _rng.randf(), .04 + _rng.randf() * .05, 1.6 + _rng.randf(), .6)

func start_escape() -> void:
	escape_t = 0.0
	_clear_discharge()

## A catch or escape removes any warned strip, lightning or afterglow at once (#25),
## and any ink (#70).
func _clear_discharge() -> void:
	_afterglow = {}; _bolts = []; _strike_flash = 0.0; _last_strike = null
	_ink_layer.visible = false; _over_layer.visible = false; _cone_tilt = 0.0

func end_outro() -> void:
	catch_t = -1.0; escape_t = -1.0; _catch_from = Vector2.ZERO
	creature.pose(1.0, 0.0)

## The harpoon pulls free of the caught eel: a small spark and bubble puff.
func _release_burst() -> void:
	if reduced_motion or not _creature_shown: return
	var at := (hook_point() - _origin()) / _cell()
	for i in range(8):
		var a := _rng.randf() * TAU
		particles.append({"kind": "spark", "color": Color(1, .95, .77), "p": at, "v": Vector2(cos(a), sin(a)) * (.8 + _rng.randf() * 1.4), "r": .035 + _rng.randf() * .03, "life": .45 + _rng.randf() * .3, "age": 0.0, "drag": 3.5})
	for i in range(6): _bubble_at(at.x + _rng.randf_range(-.15, .15), at.y, _rng.randf_range(-.5, .5), -.4 - _rng.randf() * .4, .03 + _rng.randf() * .03, 1.0, .5)

## Where the ship's harpoon leaves the hull (view coordinates).
## The rope leaves from the hull's nose hatch (#28 ImageGen hull).
func muzzle() -> Vector2:
	var cell := _cell()
	var centre := _origin() + _shown_ship() * cell - Vector2(0, cell * SHIP_HULL_LIFT)
	return centre + ShipArt.nose_offset(cell * SHIP_HULL_CELLS, Book.gear(run_state).tiers)

## The pinned harpoon on the creature (view coordinates).
func hook_point() -> Vector2:
	var hook: Dictionary = run_state.encounter.hook
	return creature.hook_point(float(hook.along), float(hook.across))

static func _index_set(values: Array) -> Dictionary:
	var out := {}
	for i in values: out[int(i)] = true
	return out

## Before the iris closes, the old world's ship position stays on screen.
func _shown_ship() -> Vector2:
	return _tr.ship if not _tr.is_empty() and not _tr.switched else ship

## Shield pickup sparkle, and the shield's flash when it bumps rock.
func shield_burst(at: Vector2) -> void:
	if reduced_motion: return
	for i in range(16):
		var a := _rng.randf() * TAU
		var s := .6 + _rng.randf() * 1.4
		particles.append({"kind": "spark", "color": Color(.62, .96, 1), "p": at + Vector2(0, -.12), "v": Vector2(cos(a), sin(a)) * s, "r": .035 + _rng.randf() * .03, "life": .45 + _rng.randf() * .3, "age": 0.0, "drag": 3.5})

func shield_bump(at: Vector2) -> void:
	_bump = 1.0
	if reduced_motion: return
	for i in range(6):
		var a := _rng.randf() * TAU
		particles.append({"kind": "spark", "color": Color(.78, .98, 1), "p": at + Vector2(0, -.3), "v": Vector2(cos(a), sin(a)) * 1.2, "r": .03, "life": .4, "age": 0.0, "drag": 3.5})

func snap_camera() -> void:
	cam_x = clampf(_shown_ship().x, Route.VIEW_COLUMNS / 2.0, Route.COLUMNS - Route.VIEW_COLUMNS / 2.0)

# ------------------------------------------------------------ particles

func _emit(delta: float) -> void:
	var steer := (ship.x - _prev_x) / maxf(delta, .0001)
	_prev_x = ship.x
	_trail += delta * 24
	while _trail >= 1:
		_trail -= 1
		_bubble_at(ship.x + _rng.randf_range(-.06, .06), ship.y + .62, -steer * .25 + _rng.randf_range(-.15, .15), 1.4 + _rng.randf() * .6, .03 + _rng.randf() * .045, 1.3 + _rng.randf() * .8, .4)
	_thrust += delta * (5 + minf(40, absf(steer) * 18))
	while _thrust >= 1:
		_thrust -= 1
		var side := -1.0 if _rng.randf() < .5 else 1.0
		_bubble_at(ship.x + side * .4, ship.y + .38, side * .35 - steer * .3, .9 + _rng.randf() * .4, .02 + _rng.randf() * .03, .8 + _rng.randf() * .5, .4)
	# Steering: side thrusters jet bubbles and wake streaks away from the turn.
	_turn = lerpf(_turn, steer, minf(1.0, delta * 12.0))
	var turn := clampf(absf(_turn) - .25, 0.0, 5.0)
	_side += delta * minf(90.0, turn * 55.0)
	while _side >= 1:
		_side -= 1
		var away := -signf(_turn)
		var at := Vector2(ship.x + away * .4, ship.y + _rng.randf_range(0.0, .32))
		_bubble_at(at.x, at.y, away * (1.8 + _rng.randf() * 1.8), _rng.randf_range(-.25, .3), .032 + _rng.randf() * .04, .6 + _rng.randf() * .5, .3)
		if _rng.randf() < .7 and particles.size() < 260:
			particles.append({"kind": "streak", "p": at, "v": Vector2(away * (2.6 + _rng.randf() * 1.2), _rng.randf_range(-.1, .2)), "r": .16 + _rng.randf() * .16, "life": .35 + _rng.randf() * .2, "age": 0.0, "drag": 4.0})
	# Speed lines while shielded or riding the passage current.
	if (world.kind == "passage" or _pursuit()) and _rng.randf() < delta * 30.0 and particles.size() < 260:
		var side := -1.0 if _rng.randf() < .5 else 1.0
		particles.append({"kind": "line", "p": Vector2(ship.x + side * (.7 + _rng.randf() * 1.6), ship.y - 3.0 - _rng.randf() * 3.0), "v": Vector2(0, 7 + _rng.randf() * 3), "len": .5 + _rng.randf() * .5, "life": .35, "age": 0.0, "drag": 0.0})
	var top := _top_row()
	for v in scene.vents:
		if float(v.y) < top - 1 or float(v.y) > top + size.y / _cell() + 1: continue
		var key := "%s,%s" % [v.x, v.y]
		var s: Dictionary = vents.get(key, {"wait": _rng.randf() * 3, "left": 0, "gap": 0.0})
		if int(s.left) > 0:
			s.gap = float(s.gap) - delta
			if float(s.gap) <= 0:
				_bubble_at(float(v.x) + _rng.randf_range(-.1, .1), float(v.y), 0, -.2, .025 + _rng.randf() * .035, 2.2 + _rng.randf(), .35)
				s.left = int(s.left) - 1; s.gap = .08 + _rng.randf() * .12
		else:
			s.wait = float(s.wait) - delta
			if float(s.wait) <= 0: s.left = 3 + _rng.randi() % 5; s.wait = 1.5 + _rng.randf() * 2.5
		vents[key] = s

func _bubble_at(x: float, y: float, vx: float, vy: float, r: float, life: float, rise: float) -> void:
	if particles.size() > 260: return
	particles.append({"kind": "bubble", "p": Vector2(x, y), "v": Vector2(vx, vy), "r": r, "life": life, "age": 0.0, "rise": rise, "drag": 2.2,
		"grow": .25 + _rng.randf() * .25, "wob": .03 + _rng.randf() * .05, "freq": 3 + _rng.randf() * 4, "phase": _rng.randf() * TAU})

## Gold collected: the nugget swells and flashes into a four-point sparkle
## that spins away, with sparks and a small bubble splash.
func burst(at: Vector2) -> void:
	particles.append({"kind": "collect", "p": at, "v": Vector2.ZERO, "life": .2 if reduced_motion else .6, "age": 0.0, "drag": 0.0, "frame": posmod(int(floor(time * 10)), 12)})
	if reduced_motion: return
	for i in range(10):
		var a := _rng.randf() * TAU
		var s := .6 + _rng.randf() * 1.4
		particles.append({"kind": "spark", "p": at + Vector2(0, -.15), "v": Vector2(cos(a), sin(a)) * s + Vector2(0, -.3), "r": .035 + _rng.randf() * .03, "life": .45 + _rng.randf() * .3, "age": 0.0, "drag": 3.5})
	for i in range(6):
		_bubble_at(at.x + _rng.randf_range(-.15, .15), at.y, _rng.randf_range(-.4, .4), _rng.randf_range(-.3, .3), .02 + _rng.randf() * .03, .9 + _rng.randf() * .5, .4)

## Bubbles freeze with the run; pickup sparkles and sparks always finish.
func _step_particles(dt: float, effect_dt: float) -> void:
	for p in particles:
		var step := effect_dt if p.kind in ["collect", "spark", "chip", "shard", "puff"] else dt
		p.age = float(p.age) + step
		p.v = p.v * exp(-float(p.drag) * step)
		if p.kind == "bubble": p.v = Vector2(p.v.x, p.v.y - float(p.rise) * step * 1.6)
		p.p += p.v * step
	particles = particles.filter(func(p): return float(p.age) < float(p.life))

# ------------------------------------------------------------ drawing

func _cell() -> float: return size.x / Route.VIEW_COLUMNS
func _shielded() -> bool: return float(run_state.get("shield", 0.0)) > 0.0 and world.get("kind") == "main"
## The ship rides low on screen; the view stops at both ends of the route.
func _top_row() -> float:
	var visible_rows := size.y / _cell()
	return clampf(_shown_ship().y - size.y * .74 / _cell(), 0.0, maxf(0.0, float(scene.get("rows", 0)) - visible_rows))
func _origin() -> Vector2: return Vector2(size.x * .5 - cam_x * _cell(), -_top_row() * _cell()) + _shake()

## Draw a clip frame with its ground root at the footprint centre (or at `at` when `at_root`).
func piece(id: String, dir: String, at: Vector2, cell: float, clip := 0, salt := 0.0, at_root := false, scale := 1.0, alpha := 1.0, tint := Color.WHITE) -> void:
	var o: Dictionary = pieces.objects.get(id, {})
	if o.is_empty(): return
	var c: Dictionary = o.clips[clip]
	var d: Dictionary = c.directions.get(dir, c.directions.values()[0])
	var frame := 0
	if int(c.frames) > 1: frame = int(c.frameOrder[posmod(int(floor(time * float(c.fps) + salt)), c.frameOrder.size())])
	var r: Array = d.rects[frame]
	var s := cell / 128.0 * scale
	var root := at if at_root else at + Vector2(float(o.footprint[0]), float(o.footprint[1])) * cell * .5
	var dest := Rect2(root - Vector2(float(o.root[0]), float(o.root[1])) * s, Vector2(float(o.frameSize[0]), float(o.frameSize[1])) * s)
	draw_texture_rect_region(texture(str(d.image)), dest, Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])), Color(tint.r, tint.g, tint.b, alpha * tint.a))

func kit(name: String, at: Vector2, cell: float) -> void:
	var entry: Dictionary = pieces.kit.get(name, {})
	if entry.is_empty(): return
	var s := cell / float(pieces.kitCellPixels)
	draw_texture_rect(texture(str(entry.image)), Rect2(at - Vector2(float(entry.origin[0]), float(entry.origin[1])) * s, Vector2(float(entry.size[0]), float(entry.size[1])) * s), false)

func _draw() -> void:
	if scene.is_empty(): return
	var cell := _cell()
	var o := _origin()
	var top_row := _top_row()
	var top := maxi(0, int(floor(top_row)) - 1)
	var bottom := mini(scene.rows - 1, int(ceil(top_row + size.y / cell)) + 3)
	var x0 := maxi(0, int(floor((-o.x) / cell)) - 1)
	var x1 := mini(scene.columns - 1, int(ceil((size.x - o.x) / cell)) + 1)
	draw_rect(Rect2(Vector2.ZERO, size), Color("0b2f63"))
	for y in range(top, bottom + 1):
		for x in range(x0, x1 + 1): piece("floor-underwater", "S", o + Vector2(x, y) * cell, cell + .5, 0, 0.0)
	var seam := Color(.745, .96, 1, .22)
	for x in range(x0, x1 + 2): draw_line(o + Vector2(x, top) * cell, o + Vector2(x, bottom + 1) * cell, seam, maxf(1, cell / 60))
	for y in range(top, bottom + 2): draw_line(o + Vector2(x0, y) * cell, o + Vector2(x1 + 1, y) * cell, seam, maxf(1, cell / 60))
	# Same seabed, deeper water: the bonus passage reads as a sheltered grotto.
	if world.kind == "passage": draw_rect(Rect2(Vector2.ZERO, size), Color(.086, .133, .43, .32))
	if world.kind == "main": Art.wash(self, world.path.currents, o, cell, top, bottom, time)
	# Soft rock shadow on the seabed, cast slightly south-east.
	for b in scene.collision:
		if b.y < top or b.y > bottom or b.x < x0 or b.x > x1: continue
		draw_texture_rect(_shade, Rect2(o + (Vector2(b) + Vector2(.1 - .35, .16 - .35)) * cell, Vector2.ONE * cell * 1.7), false, Color(1, 1, 1, .55))
	for f in fish:
		var span: float = scene.columns + 4.0
		var head := fposmod(float(f.phase) + time * float(f.speed), span) - 2.0
		var fx: float = head if f.dir > 0 else scene.columns - head
		piece("decor-background-fish", "E" if f.dir > 0 else "W", o + Vector2(fx, float(f.y)) * cell, cell, 0, float(f.phase) * 7, true)
	for d in scene.seabed:
		if d.y >= top and d.y <= bottom: piece(d.id, d.dir, o + (Vector2(d.x, d.y) + Vector2(.5, .5)) * cell, cell, 0, 0.0, true, float(d.get("scale", 1.0)))
	_draw_features(o, cell, top, bottom)
	# The hull floats: its soft shadow lands below and slightly behind it.
	var shown := _shown_ship()
	var shrink := _ship_scale()
	if shrink > .05:
		draw_set_transform(o + (shown + Vector2(.06, .42)) * cell, 0, Vector2(shrink, .5 * shrink))
		draw_texture_rect(_shade, Rect2(-Vector2.ONE * cell * .62, Vector2.ONE * cell * 1.24), false)
		draw_set_transform(Vector2.ZERO)
	for b in scene.beds:
		if b.y >= top and b.y <= bottom: kit(b.sprite, o + Vector2(b.x, b.y) * cell, cell)
	for i in range(scene.pickups.size()):
		var p: Dictionary = scene.pickups[i]
		if collected.has(i) or p.y < top or p.y > bottom + 1: continue
		var bob := sin(time * 2.4 + i) * .05
		var g := o + Vector2(p.x, p.y - .15 + bob) * cell
		var pulse := .75 + .25 * sin(time * 3.2 + i * 1.7)
		draw_texture_rect(_glow, Rect2(g - Vector2.ONE * cell * .62 * pulse, Vector2.ONE * cell * 1.24 * pulse), false)
		kit("gold-%02d" % (posmod(int(floor(time * 10 + i * 3)), 12)), o + Vector2(p.x - .75, p.y - .75 + bob - .12) * cell, cell * 1.5)
	if world.kind == "main":
		var taken: Array = run_state.get("shields_taken", [])
		for i in range(world.path.shields.size()):
			var b: Vector2 = world.path.shields[i]
			if i in taken or b.y < top or b.y > bottom + 1: continue
			Art.shield_pickup(self, o + b * cell, cell, 0.0 if reduced_motion else time, i * 1.3)
	var ship_drawn := false
	var reef: bool = world.kind == "main" and not world.path.reef_cells.is_empty()
	var cracks: Dictionary = Book.reef_cracks(run_state) if reef else {}
	# Depth by base: a row whose base (its south edge) is below the hull's covers it.
	var ship_base := shown.y + SHIP_HULL_CELLS * .5 - SHIP_HULL_LIFT
	for y in range(top, bottom + 1):
		if not ship_drawn and y + 1.0 > ship_base:
			_draw_ship(o, cell); ship_drawn = true
		if reef: _draw_reef_row(o, cell, y, x0, x1, cracks)
		for item in by_row[y]: piece(item.id, item.dir, o + Vector2(item.x, item.y) * cell, cell, 0, item.x * 5 + item.y * 3)
	_draw_particles(o, cell)
	if not ship_drawn: _draw_ship(o, cell)
	_draw_losses(o, cell)
	# The creature swims above the terrain, so the chase always reads.
	if catch_t >= 0.0: _draw_catch_rays()
	_draw_strip(o, cell)
	if _creature_shown: _draw_creature()
	for s in scene.shafts:
		if s.y >= top - 2 and s.y <= bottom: piece(s.id, s.dir, o + Vector2(s.x, s.y) * cell, cell * 1.6, 0, float(s.y))
	Harpoon.focus(self, focus_at, size, cell, focus_amount)
	# Under the ink, the cable and the arrows draw on the layer above it instead.
	if not _ink_layer.visible: _draw_harpoon(cell)
	_draw_discharge_marks(o, cell)
	_draw_iris(o, cell)
	if not _ink_layer.visible: _draw_controls()

## Issue #76: one row of reef. A standing cell draws its piece for its neighbour
## mask (rounded where a neighbour broke) and slab pattern, or the crack stage
## spreading over it; a broken cell plays its break frames at 12 fps from the
## piece it was when it broke, and its last frame is the rubble it keeps.
func _draw_reef_row(o: Vector2, cell: float, y: int, x0: int, x1: int, cracks: Dictionary) -> void:
	var cells: Dictionary = world.path.reef_cells
	var rows := Book.solid_rows(run_state)
	var spec: Dictionary = pieces.reef
	for x in range(x0, x1 + 1):
		var index := y * Route.COLUMNS + x
		if not cells.has(index): continue
		var at := o + Vector2(x + .5, y + .5) * cell
		if index in run_state.get("reef_broken", []):
			var info: Dictionary = _reef_broke_at.get(index, {})
			var id: String = info.get("id", _reef_id(rows, x, y))
			var last: int = spec.break.frames.size() - 1
			var frame := last if info.is_empty() else mini(last, int(spec.break.crackFrames) + int(floor((time - float(info.t)) * float(spec.break.fps))))
			_reef_frame(id, at, cell, frame)
			continue
		var id := _reef_id(rows, x, y)
		var k := float(cracks.get(index, 0.0))
		if k > 0.0:
			var jit := sin(time * 70.0 + Route.cell_hash(x, y, 76) * 40.0) * cell * .02 * k if k > .55 and not reduced_motion else 0.0
			_reef_frame(id, at + Vector2(jit, 0), cell, mini(int(spec.break.crackFrames) - 1, int(floor(k * float(spec.break.crackFrames)))))
		else:
			var entry: Dictionary = spec.pieces.get(id, {})
			if entry.is_empty(): continue
			var s := cell / float(spec.static.pixelsPerCell)
			draw_texture_rect(_reef_texture(str(entry.static)), Rect2(at - Vector2(float(spec.static.root[0]), float(spec.static.root[1])) * s, Vector2(float(spec.static.size[0]), float(spec.static.size[1])) * s), false)

## Frame `frame` of a piece's crack/break sheet, root on `at`.
func _reef_frame(id: String, at: Vector2, cell: float, frame: int) -> void:
	var entry: Dictionary = pieces.reef.pieces.get(id, {})
	if entry.is_empty() or entry.break == null: return
	var b: Dictionary = pieces.reef.break
	var s := cell / float(b.pixelsPerCell)
	var size_px := Vector2(float(b.frame[0]), float(b.frame[1]))
	draw_texture_rect_region(_reef_texture(str(entry.break)), Rect2(at - Vector2(float(b.root[0]), float(b.root[1])) * s, size_px * s), Rect2(Vector2(frame * size_px.x, 0), size_px))

## Piece for a reef cell: neighbour mask (N=1, E=2, S=4, W=8; rock, standing reef
## and the canyon walls count) and one of three slab patterns.
func _reef_id(rows: Array, x: int, y: int) -> String:
	var solid := func(cx: int, cy: int) -> bool: return cx < 0 or cx >= Route.COLUMNS or (cy >= 0 and cy < rows.size() and str(rows[cy])[cx] == "#")
	var mask := (1 if solid.call(x, y - 1) else 0) | (2 if solid.call(x + 1, y) else 0) | (4 if solid.call(x, y + 1) else 0) | (8 if solid.call(x - 1, y) else 0)
	return "reef-%02d-%s" % [mask, "abc"[mini(2, int(Route.cell_hash(x, y, 76) * 3.0))]]

## Reef cells just broke (by the parrotfish or the hull): each plays its break
## from the piece it was drawn as, with a dust puff, a few shards and bubbles.
func reef_broke(cells: Array, power: float) -> void:
	var rows := Book.solid_rows(run_state)
	for c in cells:
		var x := int(c.x)
		var y := int(c.y)
		# The piece it was before this break (neighbours that broke with it still count as standing).
		var before := rows.duplicate()
		for other in cells: before[int(other.y)] = str(before[int(other.y)]).substr(0, int(other.x)) + "#" + str(before[int(other.y)]).substr(int(other.x) + 1)
		_reef_broke_at[y * Route.COLUMNS + x] = {"t": time, "id": _reef_id(before, x, y)}
		_reef_debris(Vector2(x + .5, y + .5), power)

func _reef_debris(at: Vector2, power: float) -> void:
	particles.append({"kind": "puff", "p": at, "v": Vector2.ZERO, "life": .7, "age": 0.0, "drag": 0.0})
	if reduced_motion: return
	for i in range(2):
		var a := _rng.randf() * TAU
		particles.append({"kind": "shard", "p": at + Vector2(_rng.randf_range(-.3, .3), _rng.randf_range(-.3, .3)), "v": Vector2.from_angle(a) * (.8 + _rng.randf() * 1.8) * power,
			"r": .07 + _rng.randf() * .09, "life": .9 + _rng.randf() * .6, "age": 0.0, "drag": 4.0, "spin": _rng.randf_range(-7.0, 7.0), "tone": _rng.randf()})
	for i in range(4):
		_bubble_at(at.x + _rng.randf_range(-.4, .4), at.y, _rng.randf_range(-.5, .5), -.3 - _rng.randf() * .5, .03 + _rng.randf() * .04, 1.2, .45)

## Issue #25: the warned or live strip over the terrain, under the creature.
func _draw_strip(o: Vector2, cell: float) -> void:
	var strike = discharge()
	var d: Dictionary = Book.definition().encounter.discharge
	if strike is Dictionary:
		var x0 := o.x + float(strike.x0) * cell
		var w := float(strike.w) * cell
		if strike.phase == "windup": DischargeArt.warning(self, x0, w, size.y, cell, float(strike.t), d, time, reduced_motion)
		else: DischargeArt.live(self, x0, w, size.y, cell, 1.0 - .4 * (float(strike.t) - float(d.warn_seconds)) / float(d.active_seconds))
	elif not _afterglow.is_empty():
		DischargeArt.live(self, o.x + float(_afterglow.x0) * cell, float(_afterglow.w) * cell, size.y, cell, .6 * (1.0 - float(_afterglow.t) / .3))

## Over the creature: lightning badges while warned, bolts and flash while live.
func _draw_discharge_marks(o: Vector2, cell: float) -> void:
	var strike = discharge()
	if not strike is Dictionary: return
	var centre := o.x + (float(strike.x0) + float(strike.w) / 2.0) * cell
	if strike.phase == "windup":
		var pop := 1.0 if reduced_motion else minf(1.0, float(strike.t) / .18) * (1.0 + .15 * sin(minf(1.0, float(strike.t) / .3) * PI))
		# Clear of the HUD row, and again just below the ship.
		DischargeArt.badge(self, Vector2(centre, cell * 2.5), cell * .32 * pop, cell)
		DischargeArt.badge(self, Vector2(centre, minf(size.y - cell * .55, o.y + (_shown_ship().y + 1.5) * cell)), cell * .26 * pop, cell)
		return
	DischargeArt.bolts(self, _bolts, cell)
	if _strike_flash > 0.0 and not reduced_motion: draw_rect(Rect2(Vector2.ZERO, size), Color(1, .96, .84, .18 * _strike_flash))

## Catch cutscene backdrop: the scene dims and warm rays turn slowly behind the
## creature (code-drawn, as in design/pursuit-preview).
func _draw_catch_rays() -> void:
	var k := 1.0 if reduced_motion else clampf(catch_t / .5, 0.0, 1.0)
	var centre := creature.to_view(creature.bone_world(str(creature.profile.centre))) if _creature_shown else size * Vector2(.5, .4)
	draw_rect(Rect2(Vector2.ZERO, size), Color(.016, .08, .19, .5 * k))
	var far := size.length()
	var spin := 0.0 if reduced_motion else catch_t * deg_to_rad(12.0)
	for i in range(16):
		var a := spin + i * TAU / 16.0
		draw_colored_polygon(PackedVector2Array([centre, centre + Vector2.from_angle(a) * far, centre + Vector2.from_angle(a + deg_to_rad(8.0)) * far]), Color(1, .94, .75, .2 * k))
	draw_texture_rect(_glow, Rect2(centre - Vector2.ONE * size.x * .55, Vector2.ONE * size.x * 1.1), false, Color(1, 1, 1, .9 * k))

## Creature: soft blobs under its spine, then the live 3D render.
func _draw_creature() -> void:
	var cell := _cell()
	if catch_t < 0.0:
		var blob := cell * float(creature.profile.shadow)
		for p in creature.ground_points():
			draw_texture_rect(_shade, Rect2(p - Vector2.ONE * blob * .5, Vector2.ONE * blob), false, Color(1, 1, 1, .6))
	draw_texture_rect(creature.texture(), Rect2(Vector2.ZERO, size), false)

## The harpoon in flight, reeling back, or pinned to the creature, with its rope.
func _draw_harpoon(cell: float, c: CanvasItem = null) -> void:
	if c == null: c = self
	var encounter = run_state.get("encounter")
	if not encounter is Dictionary or not encounter.harpoon is Dictionary or world.get("kind") != "main": return
	var shot: Dictionary = encounter.harpoon
	var nose := muzzle()
	var tier := int(Book.gear(run_state).tiers.get("harpoon", 1))
	var reach := cell * Harpoon.length(tier)
	var rules: Dictionary = Book.definition().encounter
	if shot.state == "attached":
		if escape_t >= 0.0:
			# The cable parts in the middle; the ship's half falls slack and fades.
			var fade := maxf(0.0, 1.0 - escape_t / .9)
			if fade <= 0.0 or not _creature_shown: return
			var mid := nose.lerp(hook_point(), .5) + Vector2(-cell * .6 * escape_t, cell * 2.0 * escape_t)
			Harpoon.rope(c, nose, mid, cell, .9, time, fade, tier)
			return
		if not _creature_shown: return
		var pin := hook_point()
		if catch_t >= 0.0:
			# Caught: the harpoon pulls free and reels home into the nose, then is stowed.
			var k := clampf((catch_t - RETRACT_START) / RETRACT_SECONDS, 0.0, 1.0)
			if k >= 1.0: return
			var at := pin.lerp(nose, smoothstep(0.0, 1.0, k))
			var away := (at - nose).angle()
			var tail := at - Vector2.from_angle(away) * reach
			if tail.distance_to(nose) > 2.0: Harpoon.rope(c, nose, tail, cell, .5 * (1.0 - k), time, 1.0, tier)
			Harpoon.harpoon(c, at, away, cell, k > 0.0, tier)
			return
		var angle := (pin - nose).angle()
		Harpoon.rope(c, nose, pin - Vector2.from_angle(angle) * reach, cell, .06, time, 1.0, tier)
		Harpoon.harpoon(c, pin, angle, cell, false, tier)
		if _hooked_at >= 0.0: Harpoon.hook_ring(c, pin, cell, time - _hooked_at)
		return
	var o := _origin()
	var d := float(shot.d)
	# Reeling drifts the harpoon back over to the ship's column as it comes home.
	var x := float(shot.x) if shot.state == "flying" else lerpf(_shown_ship().x, float(shot.x), clampf(d / float(rules.harpoon_range_rows), 0.0, 1.0))
	var tip := o + Vector2(x, _shown_ship().y - float(rules.nose_rows) - d) * cell
	var angle := -PI / 2 if shot.state == "flying" else (tip - nose).angle()
	var tail := tip - Vector2.from_angle(angle) * reach
	Harpoon.rope(c, nose, tail, cell, .35 if shot.state == "flying" else .9, time, 1.0, tier)
	Harpoon.harpoon(c, tip, angle, cell, true, tier)

## Portals (whirlpool under the stone ring), passage end whirlpools, the rejoin
## outflow, current flow lines and the passage's forward flow.
func _draw_features(o: Vector2, cell: float, top: int, bottom: int) -> void:
	var t := 0.0 if reduced_motion else time
	if world.kind == "main":
		var used: Array = run_state.get("portals_used", [])
		for i in range(world.path.portals.size()):
			var portal: Dictionary = world.path.portals[i]
			if float(portal.y) < top - 1 or float(portal.y) > bottom + 1: continue
			# Until the iris closes on entry, the portal still looks open.
			var spent: bool = i in used and not (not _tr.is_empty() and not _tr.switched and _tr.kind == "enter")
			var at := o + Vector2(float(portal.x), float(portal.y)) * cell
			Art.portal_pool(self, at, cell, t, spent, WorkshopBook.tier_color(int(Book.gear(run_state).tiers.get("passage", 1))))
			piece("portal-ring", "S", at, cell, 0, 0.0, true)
		if not _outflow.is_empty():
			Art.swirl(self, o + _outflow.p * cell, cell * .45 * (1.0 - float(_outflow.t)), -t, 1.0 - float(_outflow.t))
		Art.draw_streaks(self, world.streaks, o, cell, t, float(Book.definition().current_columns_per_second), top, bottom)
	else:
		var info: Dictionary = world.info
		var rows := float(info.rows_count)
		var ride := float(Book.definition().passage_ride_rows)
		Art.swirl(self, o + Vector2(Book.passage_centre(info, rows - ride), rows - ride) * cell, cell * .45, t)
		Art.swirl(self, o + Vector2(Book.passage_centre(info, ride), ride) * cell, cell * .45, -t)
		Art.draw_flow(self, world.flow, info, func(y): return Book.passage_centre(info, y), o, cell, t, float(Book.definition().passage_forward_rows_per_second) * 1.7, top, bottom, WorkshopBook.tier_color(int(Book.gear(run_state).tiers.get("passage", 1))))

## Ship size through a whirlpool: it spins down into the first and rises out of the next.
func _ship_scale() -> float:
	if _tr.is_empty(): return 1.0
	var k := float(_tr.t) / .5 if float(_tr.t) < .5 else (1.0 - float(_tr.t)) / .5
	return 1.0 - minf(1.0, k * 1.15)

## Iris: closes on the whirlpool, opens on the next one.
func _draw_iris(o: Vector2, cell: float) -> void:
	if _tr.is_empty(): return
	var t := float(_tr.t)
	var k := 1.0 - t / .5 if t < .5 else (t - .5) / .5
	var reach := size.length()
	var r := k * k * reach
	var at := o + _shown_ship() * cell - Vector2(0, 6)
	draw_arc(at, r + reach, 0, TAU, 72, Color("041530"), reach * 2.0)
	if r > 4: draw_arc(at, r, 0, TAU, 72, Color(.63, .96, 1, .8), 4.0, true)

## Arrow buttons: rounded translucent triangles that brighten while held.
func _draw_controls(c: CanvasItem = null) -> void:
	if not controls_visible: return
	if c == null: c = self
	var held := 0.0 if controls_disabled else (_stick if _stick != 0.0 else key_input)
	# The passage ride dims the arrows to a third.
	var dim := .32 if controls_disabled else 1.0
	for side: float in [-1.0, 1.0]:
		var box := _button_rect(side)
		var down := held * side > 0.0
		var points := _rounded_triangle(box.get_center(), box.size.x * .5, side, box.size.x * .12)
		# A faint navy drop keeps the pale arrow readable over bright water.
		var drop := PackedVector2Array()
		for point in points: drop.append(point + Vector2(0, box.size.x * .05))
		c.draw_colored_polygon(drop, Color(.02, .12, .27, .22 * dim))
		c.draw_colored_polygon(points, Color(1, 1, 1, (.62 if down else .34) * dim))
		points.append(points[0])
		c.draw_polyline(points, Color(1, 1, 1, (.95 if down else .7) * (.65 if controls_disabled else 1.0) * dim), maxf(2.0, box.size.x * .04), true)

## Bottom corner square holding one arrow, clear of the ship's lane.
func _button_rect(side: float) -> Rect2:
	var edge := minf(_cell() * 1.6, size.y * .18)
	var margin := edge * .22
	var x := margin if side < 0 else size.x - margin - edge
	return Rect2(Vector2(x, size.y - margin * 1.6 - edge), Vector2.ONE * edge)

## Triangle pointing toward `side`, corners rounded by `round_radius`.
static func _rounded_triangle(centre: Vector2, radius: float, side: float, round_radius: float) -> PackedVector2Array:
	var corners: Array[Vector2] = []
	for i in range(3):
		var angle := (0.0 if side > 0 else PI) + i * TAU / 3.0
		corners.append(centre + Vector2(cos(angle), sin(angle)) * (radius - round_radius * 2.0))
	var points := PackedVector2Array()
	for i in range(3):
		var corner := corners[i]
		var start := (corner - centre).angle() - PI / 3.0
		for step in range(7): points.append(corner + Vector2.from_angle(start + step * TAU / 3.0 / 6.0) * round_radius)
	return points

func _draw_ship(o: Vector2, cell: float) -> void:
	var shown := _shown_ship()
	var shrink := _ship_scale()
	if shrink <= .05: return
	# Hit protection plays the impact clip and blinks, readable without knockback;
	# shield bumps and the passage ride never do.
	var hurt: bool = protection > 0.0 and not _shielded() and world.kind == "main" and _tr.is_empty()
	var alpha := 1.0 if not hurt or reduced_motion else (.45 if int(time * 12) % 2 else 1.0)
	var root := o + (shown + _knock) * cell
	# Banks into turns, and wobbles after a hit; the whirlpool spins it down.
	var pivot := root - Vector2(0, cell * .35)
	var spin := _tilt
	if shrink < 1.0 and not reduced_motion: spin += (1.0 - shrink) * PI * (2.5 if _tr.kind == "enter" else -2.0)
	if not reduced_motion: spin += sin(_hurt * 26.0) * _hurt * _hurt * .35
	draw_set_transform_matrix(Transform2D(spin, Vector2(shrink, shrink), 0.0, pivot) * Transform2D(0.0, -pivot))
	var red := _hurt * _hurt
	var tiers: Dictionary = Book.gear(run_state).tiers
	ShipArt.draw(self, root - Vector2(0, cell * SHIP_HULL_LIFT), cell * SHIP_HULL_CELLS, tiers, Color(1, 1 - .55 * red, 1 - .6 * red, alpha))
	draw_set_transform(Vector2.ZERO)
	var shield_left := float(run_state.get("shield", 0.0))
	if shield_left <= 0.0: _shield_peak = 0.0
	elif shield_left > _shield_peak: _shield_peak = shield_left
	if _shielded() and _tr.is_empty():
		Art.shield_bubble(self, root, cell, shield_left / maxf(_shield_peak, 0.001), time, _bump, WorkshopBook.tier_color(int(tiers.get("shield", 1))))

func _draw_particles(o: Vector2, cell: float) -> void:
	for p in particles:
		var t := float(p.age) / float(p.life)
		if p.kind == "bubble":
			var r := float(p.r) * (1 + float(p.grow) * t) * cell
			var at := o + Vector2(p.p.x + sin(float(p.age) * float(p.freq) + float(p.phase)) * float(p.wob), p.p.y) * cell
			draw_texture_rect(_bubble, Rect2(at - Vector2.ONE * r, Vector2.ONE * r * 2), false, Color(1, 1, 1, minf(1, float(p.age) * 8) * (1 - t * t)))
		elif p.kind == "line":
			var head: Vector2 = o + p.p * cell
			draw_line(head, head - Vector2(0, float(p.len) * cell), Color(.91, .99, 1, .7 * sin(PI * t)), maxf(1.5, cell * .035), true)
		elif p.kind == "streak":
			var at: Vector2 = o + p.p * cell
			var tail := Vector2(p.v).normalized() * float(p.r) * cell * (1 - t * .4)
			draw_line(at - tail, at + tail * .3, Color(.94, 1, 1, .85 * (1 - t)), maxf(1.5, cell * .04))
		elif p.kind == "collect":
			_draw_collect(o + p.p * cell, cell, t, int(p.frame))
		elif p.kind == "shard":
			# Reef shards: pale limestone flakes that hop and fade (cosmetic, never collide).
			var at: Vector2 = o + p.p * cell
			var r := float(p.r) * cell
			var a := float(p.age) * float(p.spin)
			var lift := sin(minf(1.0, t * 1.6) * PI) * cell * .25
			var c := (Color("efe4c9") if float(p.tone) < .5 else Color("cdb78f"))
			c.a = (1.0 - t) / .25 if t > .75 else 1.0
			var flake := PackedVector2Array([at + Vector2(0, -lift) + Vector2.from_angle(a) * r, at + Vector2(0, -lift) + Vector2.from_angle(a + 2.2) * r * .8, at + Vector2(0, -lift) + Vector2.from_angle(a + 4.0) * r * .9])
			draw_colored_polygon(flake, c)
		elif p.kind == "puff":
			var r := cell * (.5 + t * .9)
			draw_texture_rect(_puff, Rect2(o + p.p * cell - Vector2.ONE * r, Vector2.ONE * r * 2), false, Color(1, 1, 1, .45 * (1.0 - t)))
		elif p.kind == "chip":
			# Hull chips: small yellow-paint flakes tumbling away from the dent.
			var at: Vector2 = o + p.p * cell
			var r := float(p.r) * cell
			var a := float(p.age) * float(p.spin)
			var flake := PackedVector2Array([at + Vector2.from_angle(a) * r, at + Vector2.from_angle(a + 2.3) * r * .7, at + Vector2.from_angle(a + 3.9) * r * .9])
			draw_colored_polygon(flake, Color(1, .78, .2, 1 - t * t))
		else:
			_star(o + p.p * cell, float(p.r) * cell * 1.6 * (1 - t * .5), float(p.age) * 6.0, Color(p.get("color", Color(1, .93, .6)), 1 - t))

## Collect: swell and brighten (first third), then shrink into a spinning star.
func _draw_collect(at: Vector2, cell: float, t: float, frame: int) -> void:
	if reduced_motion: t = 1.0
	var swell := clampf(t / .3, 0.0, 1.0)
	var fade := clampf((t - .3) / .7, 0.0, 1.0)
	var gold := (1.0 + .3 * swell) * (1.0 - fade) ** 2
	var g := at + Vector2(0, -.12 - .35 * t) * cell
	if gold > .01:
		var bright := 1.0 + .9 * swell
		var gc := cell * 1.5 * gold
		_kit_tinted("gold-%02d" % frame, g - Vector2.ONE * gc * .5, gc, Color(bright, bright, bright * .8))
	var flare := sin(clampf((t - .15) / .85, 0.0, 1.0) * PI)
	if flare > 0:
		draw_texture_rect(_glow, Rect2(g - Vector2.ONE * cell * .9 * flare, Vector2.ONE * cell * 1.8 * flare), false, Color(1, 1, 1, flare))
		_star(g, cell * .62 * flare, t * 2.4, Color(1, .98, .82, flare))
		_star(g, cell * .34 * flare, t * 2.4 + PI / 4, Color(1, .86, .45, flare * .8))

func _kit_tinted(name: String, at: Vector2, cell: float, color: Color) -> void:
	var entry: Dictionary = pieces.kit.get(name, {})
	if entry.is_empty(): return
	var s := cell / float(pieces.kitCellPixels)
	draw_texture_rect(texture(str(entry.image)), Rect2(at - Vector2(float(entry.origin[0]), float(entry.origin[1])) * s, Vector2(float(entry.size[0]), float(entry.size[1])) * s), false, color)

## Four-point sparkle with thin rays.
func _star(at: Vector2, radius: float, angle: float, color: Color) -> void:
	if radius <= .5: return
	var points := PackedVector2Array()
	for i in range(8):
		var a := angle + i * PI / 4
		points.append(at + Vector2(cos(a), sin(a)) * (radius if i % 2 == 0 else radius * .2))
	draw_colored_polygon(points, color)

## A hull loss: the amount rises off the ship in red.
func hull_loss(amount: int) -> void:
	_losses.append({"text": "−%d" % amount, "age": 0.0, "p": _shown_ship() + Vector2(0, -.9)})

func _draw_losses(o: Vector2, cell: float) -> void:
	var font := get_theme_default_font()
	var size_px := int(cell * .42)
	for l in _losses:
		var t := float(l.age) / .9
		var at: Vector2 = o + (l.p + Vector2(0, -.6 * t)) * cell
		var w := font.get_string_size(str(l.text), HORIZONTAL_ALIGNMENT_LEFT, -1, size_px).x
		var a := 1.0 - t * t
		draw_string_outline(font, at - Vector2(w / 2, 0), str(l.text), HORIZONTAL_ALIGNMENT_LEFT, -1, size_px, maxi(2, int(cell * .07)), Color(.2, .02, .02, a))
		draw_string(font, at - Vector2(w / 2, 0), str(l.text), HORIZONTAL_ALIGNMENT_LEFT, -1, size_px, Color(1, .27, .2, a))

## Impact: a short, decaying shake of the playfield (skipped for reduced motion).
func hit() -> void:
	_hit = 1.0

## A new dive: drop any shake, hit wobble or knock-back left from the last one.
func clear_feedback() -> void:
	_hit = 0.0; _hurt = 0.0; _knock = Vector2.ZERO; _reef_broke_at.clear(); _losses.clear()

## Hull damage: the ship slides back from `from` (where it struck) to where the
## rules left it, wobbles and flashes red, and sparks, hull chips and bubbles
## burst at the contact point.
func damage(from: Vector2, to: Vector2) -> void:
	_hurt = 1.0
	knock(from, to)
	var away := (from - to).normalized() if from.distance_to(to) > .01 else Vector2.UP
	var at := from + away * .35 - Vector2(0, .2)
	if reduced_motion: return
	for i in range(14):
		var a := away.angle() + _rng.randf_range(-1.3, 1.3)
		var speed := 1.6 + _rng.randf() * 2.6
		particles.append({"kind": "spark", "p": at, "v": Vector2.from_angle(a) * speed, "r": .03 + _rng.randf() * .03, "life": .3 + _rng.randf() * .25, "age": 0.0, "drag": 5.0, "color": Color(1, .55 + _rng.randf() * .35, .25)})
	for i in range(6):
		var a := (-away).angle() + _rng.randf_range(-1.1, 1.1)
		particles.append({"kind": "chip", "p": at, "v": Vector2.from_angle(a) * (1.0 + _rng.randf() * 1.4) + Vector2(0, -.4), "r": .05 + _rng.randf() * .04, "life": .6 + _rng.randf() * .3, "age": 0.0, "drag": 2.5, "spin": _rng.randf_range(-12.0, 12.0)})
	for i in range(8):
		_bubble_at(at.x + _rng.randf_range(-.2, .2), at.y + _rng.randf_range(-.1, .2), _rng.randf_range(-.6, .6), _rng.randf_range(-.5, .3), .025 + _rng.randf() * .04, .8 + _rng.randf() * .5, .45)

## A bump without damage (rock touched during hit protection): only the slide.
func knock(from: Vector2, to: Vector2) -> void:
	if reduced_motion: return
	_knock += from - to

func _shake() -> Vector2:
	if reduced_motion or _hit <= 0.0: return Vector2.ZERO
	return Vector2(sin(time * 71.0), cos(time * 53.0)) * _hit * _cell() * .08

# ------------------------------------------------------------ steering

func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and not _held.has(event.index):
			var first := _held.is_empty()
			var side := _side_at(event.position)
			# The press that starts the dive steers only when it lands on an arrow.
			if not steering_enabled and not _button_rect(side).grow(_cell() * .3).has_point(event.position): side = 0.0
			_held[event.index] = side
			accept_event()
			if first: pressed_down.emit()
			_update_stick()
		elif not event.pressed and _held.has(event.index):
			_held.erase(event.index); accept_event(); _update_stick()
	elif event is InputEventScreenDrag and _held.has(event.index):
		# A thumb sliding across the middle switches arrows.
		if _held[event.index] != 0.0: _held[event.index] = _side_at(event.position)
		accept_event(); _update_stick()

## Each half of the screen is its arrow, so a thumb near the button never misses.
func _side_at(position: Vector2) -> float:
	return -1.0 if position.x < size.x * .5 else 1.0

func _update_stick() -> void:
	var value := 0.0
	for side: float in _held.values(): value += side
	_stick = clampf(value, -1.0, 1.0)
	if steering_enabled: steered.emit(_stick)
	queue_redraw()

## Re-send held arrows (used when the resume countdown ends).
func resume_controls() -> void:
	_update_stick()

func release_controls() -> void:
	_held.clear(); _stick = 0.0; queue_redraw()
