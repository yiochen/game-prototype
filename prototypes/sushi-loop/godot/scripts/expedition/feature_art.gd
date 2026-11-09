extends RefCounted
## Issue #22 feature drawing, shared by the expedition view and the gallery:
## current fields (seabed wash and drifting flow lines), the shield pickup and
## the shielded hull's bubble, whirlpools (portal, passage ends, outflow) and
## the passage's forward flow. Matches the approved HTML review
## (design/expedition-currents-preview). Everything is drawn on `canvas` in
## screen space; `o` is the world origin and `cell` the cell size in pixels.

const FLOW := Color(.94, 1, 1)
static var _soft: Texture2D
static var _core: Texture2D
static var _halo: Texture2D
static var _bubble: Texture2D
static var _glow: Texture2D
## #28: things the ship can use carry one signal (lime halo, keylined ring,
## pulse); red is reserved for harmful things. Power-up looks are colours.
const SIGNAL_GOOD := Color("b4ff2e")
const SIGNAL_BAD := Color("ff3b3b")
const KEYLINE := Color(.04, .19, .28, .5)

static func _radial(colors: Array, offsets: Array) -> Texture2D:
	var gradient := Gradient.new()
	gradient.offsets = PackedFloat32Array(offsets)
	gradient.colors = PackedColorArray(colors)
	var texture := GradientTexture2D.new()
	texture.gradient = gradient; texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(.5, .5); texture.fill_to = Vector2(1, .5); texture.width = 64; texture.height = 64
	return texture

static func _textures() -> void:
	if _soft != null: return
	_soft = _radial([Color(.84, .98, 1, 1), Color(.84, .98, 1, .55), Color(.84, .98, 1, 0)], [0.0, .5, 1.0])
	_core = _radial([Color(.012, .1, .26, .95), Color(.047, .36, .59, .75), Color(.35, .86, 1, 0)], [0.0, .55, 1.0])
	_halo = _radial([Color(.43, .94, 1, .45), Color(.24, .78, 1, 0)], [0.0, 1.0])
	_glow = _radial([Color(1, 1, 1, .5), Color(1, 1, 1, .22), Color(1, 1, 1, 0)], [0.0, .55, 1.0])
	_bubble = _radial([Color(.63, .96, 1, .05), Color(.63, .96, 1, .22), Color(.86, .99, 1, .5), Color(.86, .99, 1, 0)], [0.0, .8, .94, 1.0])

# ------------------------------------------------------------ currents

## Flow lines for every run of same-direction current cells in a row.
static func streaks(currents: Dictionary, rows: int, seed_value: int) -> Array:
	var rng := RandomNumberGenerator.new(); rng.seed = seed_value * 13 + 5
	var out: Array = []
	for y in range(rows):
		var x := 0
		while x < 11:
			var dir := int(currents.get(Vector2i(x, y), 0))
			if dir == 0: x += 1; continue
			var b := x
			while int(currents.get(Vector2i(b + 1, y), 0)) == dir: b += 1
			var width := b - x + 1
			for n in range(maxi(1, int(round(width * 1.2)))):
				out.append({"a": float(x), "b": float(b + 1), "y": y + .12 + rng.randf() * .76, "dir": dir, "phase": rng.randf() * width,
					"len": .55 + rng.randf() * .5, "wave": rng.randf() * 6.0, "head": rng.randf() < .6})
			x = b + 1
	return out

## Pale seabed wash under current cells: overlapping soft blobs make one band.
static func wash(canvas: CanvasItem, currents: Dictionary, o: Vector2, cell: float, top: int, bottom: int, time: float) -> void:
	_textures()
	var alpha := .3 + .05 * sin(time * 1.7)
	for key in currents:
		var c: Vector2i = key
		if c.y < top or c.y > bottom: continue
		canvas.draw_texture_rect(_soft, Rect2(o + (Vector2(c) + Vector2(.5, .5)) * cell - Vector2.ONE * cell * .85, Vector2.ONE * cell * 1.7), false, Color(1, 1, 1, alpha))

## Tapered flow lines drifting at the current's real speed, some with a chevron head.
static func draw_streaks(canvas: CanvasItem, list: Array, o: Vector2, cell: float, time: float, speed: float, top: int, bottom: int) -> void:
	var width := maxf(2.0, cell * .055)
	for s in list:
		if float(s.y) < top - 1 or float(s.y) > bottom + 1: continue
		var span := float(s.b) - float(s.a)
		var travel := fposmod(float(s.phase) + time * speed, span)
		var head := float(s.a) + travel if int(s.dir) > 0 else float(s.b) - travel
		var alpha := pow(sin(PI * travel / span), .7) * .95
		var tail := head - int(s.dir) * float(s.len)
		var y := o.y + (float(s.y) + sin(time * 2.0 + float(s.wave) + head) * .04) * cell
		var points := PackedVector2Array(); var colors := PackedColorArray()
		for i in range(6):
			var u := i / 5.0
			var x := lerpf(tail, head, u)
			# Gentle quadratic bow from the tail (slightly low) to the head.
			points.append(Vector2(o.x + x * cell, y + cell * ((1.0 - u) * (1.0 - u) * .03 - 2.0 * u * (1.0 - u) * .05)))
			colors.append(Color(FLOW, alpha * u))
		canvas.draw_polyline_colors(points, colors, width, true)
		if s.head:
			var tip := points[5]; var k := cell * .11
			canvas.draw_polyline(PackedVector2Array([tip + Vector2(-int(s.dir) * k, -k), tip, tip + Vector2(-int(s.dir) * k, k)]), Color(FLOW, alpha), maxf(2.0, cell * .06), true)

# ------------------------------------------------------------ whirlpools

## Seen from above: a dark core with three bright arms turning inward.
static func swirl(canvas: CanvasItem, at: Vector2, radius: float, time: float, strength := 1.0, arms := Color(.75, .98, 1)) -> void:
	if radius <= .5 or strength <= 0.0: return
	_textures()
	canvas.draw_texture_rect(_core, Rect2(at - Vector2.ONE * radius, Vector2.ONE * radius * 2.0), false, Color(1, 1, 1, strength))
	for arm in range(3):
		var points := PackedVector2Array()
		for i in range(25):
			var u := i / 24.0
			var a := arm * TAU / 3.0 - time * 2.6 + u * 3.2
			points.append(at + Vector2(cos(a), sin(a)) * radius * (.95 - u * .8))
		canvas.draw_polyline(points, Color(arms, .8 * strength), maxf(1.5, radius * .11), true)

## The shared "good, interactable" signal (#28): a soft halo, a steady ring with
## a dark keyline and a ring that pulses outward.
static func signal_glow(canvas: CanvasItem, at: Vector2, radius: float, time: float, color := SIGNAL_GOOD) -> void:
	_textures()
	canvas.draw_texture_rect(_glow, Rect2(at - Vector2.ONE * radius * 1.35, Vector2.ONE * radius * 2.7), false, Color(color, .9))
	canvas.draw_arc(at, radius, 0, TAU, 48, KEYLINE, maxf(2.0, radius * .12), true)
	canvas.draw_arc(at, radius, 0, TAU, 48, color, maxf(1.5, radius * .07), true)
	var pulse := fposmod(time / 1.3, 1.0)
	canvas.draw_arc(at, radius * (.85 + pulse * .5), 0, TAU, 48, Color(color, 1.0 - pulse), maxf(1.0, radius * .05), true)

## Portal under the ring: open portals carry the signal glow and a whirlpool in
## the Passage tier colour; spent ones lie still and dim.
static func portal_pool(canvas: CanvasItem, at: Vector2, cell: float, time: float, used: bool, arms := Color(.75, .98, 1)) -> void:
	_textures()
	if used:
		canvas.draw_circle(at, cell * .3, Color(.016, .12, .27, .45), true, -1.0, true)
		return
	signal_glow(canvas, at, cell * .62, time)
	swirl(canvas, at, cell * .36, time, 1.0, arms)

## Passage current: flow lines rushing forward (up the screen) between the walls.
static func draw_flow(canvas: CanvasItem, flow: Array, info: Dictionary, centre: Callable, o: Vector2, cell: float, time: float, speed: float, top: int, bottom: int, tint := FLOW) -> void:
	var rows := float(info.rows_count)
	for f in flow:
		var y := fposmod(float(f.y) - time * speed, rows)
		if y < top - 1 or y > bottom + 1 or y < 1.0 or y > rows - 2.0: continue
		var x: float = centre.call(y) + float(f.dx)
		var alpha := .8 * minf(1.0, minf((y - 1.0) / 2.0, (rows - 2.0 - y) / 2.0))
		var head := o + Vector2(x, y) * cell
		var tail := o + Vector2(x, y + float(f.len)) * cell
		canvas.draw_polyline_colors(PackedVector2Array([tail, head]), PackedColorArray([Color(tint, 0), Color(tint, alpha)]), maxf(2.0, cell * .05), true)
		if f.head:
			var k := cell * .1
			canvas.draw_polyline(PackedVector2Array([head + Vector2(-k, k), head, head + Vector2(k, k)]), Color(tint, alpha), maxf(2.0, cell * .05), true)

static func flow_lines(rows: int, seed_value: int) -> Array:
	var rng := RandomNumberGenerator.new(); rng.seed = seed_value * 17 + 9
	var out: Array = []
	for i in range(rows * 2): out.append({"y": rng.randf() * rows, "dx": (rng.randf() - .5) * 2.4, "len": .6 + rng.randf() * .6, "head": rng.randf() < .5})
	return out

# ------------------------------------------------------------ shield

## Shield pickup: a navy-rimmed heater shield with a blue face, white inner rim,
## sheen and highlight, floating in a cool halo with a pulsing ring.
static func shield_pickup(canvas: CanvasItem, at: Vector2, cell: float, time: float, salt := 0.0) -> void:
	_textures()
	var r := cell * .3
	var c := at + Vector2(0, -cell * .12 + sin(time * 2.2 + salt) * .05 * cell)
	signal_glow(canvas, c, cell * .42, time + salt)
	var outer := _shield_shape(c, r)
	canvas.draw_colored_polygon(outer, Color("0d3f78"))
	var rim := outer.duplicate(); rim.append(outer[0])
	canvas.draw_polyline(rim, Color("082a52"), maxf(2.0, cell * .04), true)
	var face := _shield_shape(c, r * .8)
	var colors := PackedColorArray()
	for p in face:
		var u := clampf(((p.x - c.x) + (p.y - c.y)) / (r * 2.4) + .5, 0.0, 1.0)
		colors.append(Color("8fe3ff").lerp(Color("2f9be8"), minf(1.0, u * 2.2)).lerp(Color("1559b8"), maxf(0.0, u * 2.0 - 1.0)))
	canvas.draw_polygon(face, colors)
	# Left-half sheen.
	var sheen := PackedVector2Array()
	for p in face:
		if p.x <= c.x + .5: sheen.append(p)
	if sheen.size() > 2: canvas.draw_colored_polygon(sheen, Color(1, 1, 1, .26))
	var inner := face.duplicate(); inner.append(face[0])
	canvas.draw_polyline(inner, Color(1, 1, 1, .95), maxf(1.5, cell * .03), true)
	canvas.draw_set_transform(c + Vector2(-r * .38, -r * .45), -.7, Vector2(1, .58))
	canvas.draw_circle(Vector2.ZERO, r * .12, Color(1, 1, 1, .9), true, -1.0, true)
	canvas.draw_set_transform(Vector2.ZERO)

static func _shield_shape(c: Vector2, r: float) -> PackedVector2Array:
	var w := r * .95; var h := r * 1.15; var top := c.y - h * .82
	var points := PackedVector2Array()
	var quad := func(a: Vector2, b: Vector2, d: Vector2, n: int):
		for i in range(1, n + 1):
			var t := i / float(n); points.append(a.lerp(b, t).lerp(b.lerp(d, t), t))
	var cubic := func(a: Vector2, b: Vector2, d: Vector2, e: Vector2, n: int):
		for i in range(1, n + 1):
			var t := i / float(n); var u := 1.0 - t
			points.append(a * u * u * u + b * 3 * u * u * t + d * 3 * u * t * t + e * t * t * t)
	var start := Vector2(c.x, top + h * .08)
	points.append(start)
	quad.call(start, Vector2(c.x + w * .5, top - h * .06), Vector2(c.x + w, top + h * .06), 6)
	cubic.call(Vector2(c.x + w, top + h * .06), Vector2(c.x + w * 1.02, c.y + h * .25), Vector2(c.x + w * .62, c.y + h * .72), Vector2(c.x, c.y + h * .98), 10)
	cubic.call(Vector2(c.x, c.y + h * .98), Vector2(c.x - w * .62, c.y + h * .72), Vector2(c.x - w * 1.02, c.y + h * .25), Vector2(c.x - w, top + h * .06), 10)
	quad.call(Vector2(c.x - w, top + h * .06), Vector2(c.x - w * .5, top - h * .06), start, 5)
	points.remove_at(points.size() - 1)
	return points

## Shielded hull: a bubble whose bright rim drains with the time left.
## `tint` is the Shield track's look colour (#28): white, violet, gold.
static func shield_bubble(canvas: CanvasItem, ship: Vector2, cell: float, fraction: float, time: float, bump: float, tint := Color(.94, 1, 1)) -> void:
	_textures()
	var r := cell * (.66 + bump * .08)
	var c := ship + Vector2(0, -cell * .28)
	canvas.draw_texture_rect(_bubble, Rect2(c - Vector2.ONE * r * 1.06, Vector2.ONE * r * 2.12), false, Color(1, 1, 1).lerp(tint, .6))
	canvas.draw_arc(c, r, 0, TAU, 48, Color(tint, .4), maxf(1.5, cell * .03), true)
	if fraction > 0.0:
		canvas.draw_arc(c, r, -PI / 2, -PI / 2 + TAU * fraction, 48, Color(tint, .8 + .2 * sin(time * 12.0)), maxf(2.5, cell * .06), true)
