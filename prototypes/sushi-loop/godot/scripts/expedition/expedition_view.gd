extends Control
## Expedition playfield (issue #21). Draws the seeded route with the approved
## production pieces over the ground layer, following the HTML review's draw
## order: floor, rock shadow, fish, seabed decor, ship shadow, beds, gold,
## rows north→south (a landmark at or south of the ship covers it as it passes
## under), particles, light shafts. The screen shows VIEW_COLUMNS of the world
## and follows the ship sideways. Steering is a floating joystick: sliding a
## held finger sideways from where it landed sets a lateral input (the ship
## keeps moving while held off-centre) and lifting it runs straight. On the
## preparation screen the first press starts the dive and becomes the stick.
const Route = preload("res://scripts/expedition/route.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")

signal steered(input: float)
signal pressed_down

var pieces: Dictionary = {}
var textures: Dictionary = {}
var scene: Dictionary = {}
var by_row: Array = []
var route_seed := -1
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
var _drag_index := -1
var _drag_anchor := 0.0
var _drag_last := Vector2.ZERO
var _stick := 0.0
var _trail := 0.0
var _thrust := 0.0
var _prev_x := 5.5
var _side := 0.0
var _turn := 0.0
var _hit := 0.0
var _bubble: Texture2D
var _glow: Texture2D
var _shade: Texture2D
var _v2: Array = []
var _rng := RandomNumberGenerator.new()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE
	accessibility_name = "Expedition. Drag sideways anywhere to steer."
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

func set_route(seed_value: int) -> void:
	if seed_value == route_seed: return
	route_seed = seed_value
	scene = Route.compose_scene(Book.route(seed_value).rows, _v2, seed_value)
	by_row = []
	by_row.resize(scene.rows)
	for y in range(scene.rows): by_row[y] = []
	for o in scene.objects: by_row[int(o.y)].append(o)
	particles.clear(); vents.clear(); collected.clear()
	var r := Route.Mulberry32.new(seed_value * 31)
	fish = []
	for i in range(int(ceil(scene.rows / 13.0))):
		fish.append({"y": 4 + i * 13 + r.next() * 6, "speed": .25 + r.next() * .25, "dir": -1 if i % 2 else 1, "phase": r.next() * 20})

## Called each frame by the presentation with the current run snapshot.
func sync(run: Dictionary, delta: float, travelling: bool) -> void:
	set_route(int(run.seed))
	time += delta
	_hit = maxf(0.0, _hit - delta * 3.0)
	ship = Vector2(float(run.x), float(run.y))
	protection = float(run.protection)
	collected.clear()
	for i in run.collected: collected[int(i)] = true
	var half := Route.VIEW_COLUMNS / 2.0
	var offset := ship.x - cam_x
	var want := ship.x - signf(offset) * .7 if absf(offset) > .7 else cam_x
	cam_x += (clampf(want, half, Route.COLUMNS - half) - cam_x) * minf(1.0, delta * 4.0)
	if travelling and not reduced_motion: _emit(delta)
	_step_particles(delta if travelling else 0.0, delta)
	queue_redraw()

func snap_camera() -> void:
	cam_x = clampf(ship.x, Route.VIEW_COLUMNS / 2.0, Route.COLUMNS - Route.VIEW_COLUMNS / 2.0)

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
		var step := effect_dt if p.kind in ["collect", "spark"] else dt
		p.age = float(p.age) + step
		p.v = p.v * exp(-float(p.drag) * step)
		if p.kind == "bubble": p.v = Vector2(p.v.x, p.v.y - float(p.rise) * step * 1.6)
		p.p += p.v * step
	particles = particles.filter(func(p): return float(p.age) < float(p.life))

# ------------------------------------------------------------ drawing

func _cell() -> float: return size.x / Route.VIEW_COLUMNS
## The ship rides low on screen; the view stops at both ends of the route.
func _top_row() -> float:
	var visible_rows := size.y / _cell()
	return clampf(ship.y - size.y * .74 / _cell(), 0.0, maxf(0.0, float(scene.get("rows", 0)) - visible_rows))
func _origin() -> Vector2: return Vector2(size.x * .5 - cam_x * _cell(), -_top_row() * _cell()) + _shake()

## Draw a clip frame with its ground root at the footprint centre (or at `at` when `at_root`).
func piece(id: String, dir: String, at: Vector2, cell: float, clip := 0, salt := 0.0, at_root := false, scale := 1.0, alpha := 1.0) -> void:
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
	draw_texture_rect_region(texture(str(d.image)), dest, Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])), Color(1, 1, 1, alpha))

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
	# The hull floats: its soft shadow lands below and slightly behind it.
	draw_set_transform(o + (ship + Vector2(.06, .42)) * cell, 0, Vector2(1, .5))
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
	var ship_drawn := false
	for y in range(top, bottom + 1):
		if not ship_drawn and y >= int(floor(ship.y)) and by_row[y].any(func(item): return int(item.get("w", 1)) > 1):
			_draw_ship(o, cell); ship_drawn = true
		for item in by_row[y]: piece(item.id, item.dir, o + Vector2(item.x, item.y) * cell, cell, 0, item.x * 5 + item.y * 3)
	_draw_particles(o, cell)
	if not ship_drawn: _draw_ship(o, cell)
	for s in scene.shafts:
		if s.y >= top - 2 and s.y <= bottom: piece(s.id, s.dir, o + Vector2(s.x, s.y) * cell, cell * 1.6, 0, float(s.y))
	_draw_stick(cell)

## Held stick: a faint sideways track under the finger and the knob's offset.
func _draw_stick(cell: float) -> void:
	if _drag_index < 0 or not steering_enabled: return
	var reach := _reach()
	var at := Vector2(_drag_anchor, _drag_last.y)
	var h := cell * .3
	draw_rect(Rect2(at - Vector2(reach + h * .5, h * .5), Vector2(reach * 2 + h, h)), Color(1, 1, 1, .16))
	for side in [-1.0, 1.0]: draw_circle(at + Vector2(side * reach, 0), h * .5, Color(1, 1, 1, .16))
	draw_circle(at, h * .16, Color(1, 1, 1, .4))
	var knob := at + Vector2(_stick * reach, 0)
	draw_circle(knob, h * .62, Color(1, 1, 1, .45))
	draw_arc(knob, h * .62, 0, TAU, 32, Color(1, 1, 1, .85), maxf(1.5, cell * .02), true)

func _draw_ship(o: Vector2, cell: float) -> void:
	# Hit protection plays the impact clip and blinks, readable without knockback.
	var hurt := protection > 0.0
	var alpha := 1.0 if not hurt or reduced_motion else (.45 if int(time * 12) % 2 else 1.0)
	piece("submarine-yellow", "S", o + ship * cell, cell, 1 if hurt else 0, 0.0, true, 1.0, alpha)

func _draw_particles(o: Vector2, cell: float) -> void:
	for p in particles:
		var t := float(p.age) / float(p.life)
		if p.kind == "bubble":
			var r := float(p.r) * (1 + float(p.grow) * t) * cell
			var at := o + Vector2(p.p.x + sin(float(p.age) * float(p.freq) + float(p.phase)) * float(p.wob), p.p.y) * cell
			draw_texture_rect(_bubble, Rect2(at - Vector2.ONE * r, Vector2.ONE * r * 2), false, Color(1, 1, 1, minf(1, float(p.age) * 8) * (1 - t * t)))
		elif p.kind == "streak":
			var at: Vector2 = o + p.p * cell
			var tail := Vector2(p.v).normalized() * float(p.r) * cell * (1 - t * .4)
			draw_line(at - tail, at + tail * .3, Color(.94, 1, 1, .85 * (1 - t)), maxf(1.5, cell * .04))
		elif p.kind == "collect":
			_draw_collect(o + p.p * cell, cell, t, int(p.frame))
		else:
			_star(o + p.p * cell, float(p.r) * cell * 1.6 * (1 - t * .5), float(p.age) * 6.0, Color(1, .93, .6, 1 - t))

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

## Impact: a short, decaying shake of the playfield (skipped for reduced motion).
func hit() -> void:
	_hit = 1.0

func _shake() -> Vector2:
	if reduced_motion or _hit <= 0.0: return Vector2.ZERO
	return Vector2(sin(time * 71.0), cos(time * 53.0)) * _hit * _cell() * .08

# ------------------------------------------------------------ steering

## Full deflection: about a cell of slide, so a thumb reaches it without leaving the side.
func _reach() -> float: return _cell() * 1.0

func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and _drag_index < 0:
			# The stick centres wherever the finger lands.
			_drag_index = event.index; _drag_anchor = event.position.x; _drag_last = event.position; _stick = 0.0
			accept_event(); pressed_down.emit(); queue_redraw()
		elif not event.pressed and event.index == _drag_index:
			_drag_index = -1; _set_stick(0.0); accept_event()
	elif event is InputEventScreenDrag and event.index == _drag_index:
		_drag_last = event.position
		var offset: float = event.position.x - _drag_anchor
		# Floating centre: sliding past full deflection drags the centre along,
		# so reversing direction responds at once.
		var reach := _reach()
		if absf(offset) > reach:
			_drag_anchor = event.position.x - signf(offset) * reach; offset = signf(offset) * reach
		var dead := reach * .12
		# A gentle curve keeps small slides fine-grained; full slide is full speed.
		_set_stick(signf(offset) * pow(clampf((absf(offset) - dead) / (reach - dead), 0.0, 1.0), 1.3))
		accept_event()

func _set_stick(value: float) -> void:
	_stick = value
	if steering_enabled: steered.emit(value)
	queue_redraw()

## Re-centre a held touch (used when the resume countdown ends).
func reanchor() -> void:
	if _drag_index >= 0: _drag_anchor = _drag_last.x; _stick = 0.0

func cancel_drag() -> void:
	_drag_index = -1; _stick = 0.0
