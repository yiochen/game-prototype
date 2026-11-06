extends RefCounted
## Issue #25 discharge drawing, matching the approved HTML review
## (design/eel-strike-preview): the warned strip (amber fill, diagonal
## hatching, dashed amber edges with an ink outline) that holds steady and
## then flashes a few times just before the strike (no countdown), lightning
## badges, the live strip's white-hot glow and jagged bolts. Everything is
## drawn on `canvas` in screen space; `x0` and `w` are the strip's left edge
## and width in pixels.

const INK := Color("24364d")
const AMBER := Color("ffb52e")
const HATCH := Color("c96a00")

## The strip before it goes live: `t` seconds into a `warn` second windup.
static func warning(canvas: CanvasItem, x0: float, w: float, height: float, cell: float, t: float, d: Dictionary, time: float, reduced: bool) -> void:
	var k := clampf(t / .3, 0.0, 1.0)
	var flash := _flashing(t, d, reduced)
	canvas.draw_rect(Rect2(x0, 0, w, height), Color(1, .667, .118, .3 * k))
	if flash: canvas.draw_rect(Rect2(x0, 0, w, height), Color(1, .84, .47, .45))
	_hatch(canvas, x0, w, height, cell, 0.0 if reduced else time * cell * .5, Color(HATCH, (.95 if flash else .65) * k))
	var u := cell / 55.7
	var dash := 12.0 * u
	var shift := 0.0 if reduced else fposmod(time * 40.0 * u, dash * 1.67)
	for x in [x0, x0 + w]:
		canvas.draw_dashed_line(Vector2(x, -dash * 2 + shift), Vector2(x, height), Color(INK, .7 * k), 6.0 * u, dash, false)
		canvas.draw_dashed_line(Vector2(x, -dash * 2 + shift), Vector2(x, height), Color(AMBER, k), 3.5 * u, dash, false)

## The last `flash_seconds` blink `flashes` times; reduced motion holds bright.
static func _flashing(t: float, d: Dictionary, reduced: bool) -> bool:
	var into := t - (float(d.warn_seconds) - float(d.flash_seconds))
	if into < 0.0: return false
	if reduced: return true
	return int(floor(into / (float(d.flash_seconds) / (int(d.flashes) * 2)))) % 2 == 0

## Diagonal stripes rising to the right, clipped to the strip.
static func _hatch(canvas: CanvasItem, x0: float, w: float, height: float, cell: float, scroll: float, color: Color) -> void:
	var gap := cell * .5
	var thick := cell * .11
	var box := PackedVector2Array([Vector2(x0, 0), Vector2(x0 + w, 0), Vector2(x0 + w, height), Vector2(x0, height)])
	var start := -w - gap + fposmod(scroll, gap)
	var y := start
	while y < height + w:
		var band := PackedVector2Array([Vector2(x0, y + w), Vector2(x0 + w, y), Vector2(x0 + w, y + thick), Vector2(x0, y + w + thick)])
		for piece in Geometry2D.intersect_polygons(band, box): canvas.draw_colored_polygon(piece, color)
		y += gap

## The live strip, and its short afterglow (`k` fades it).
static func live(canvas: CanvasItem, x0: float, w: float, height: float, cell: float, k: float) -> void:
	canvas.draw_rect(Rect2(x0 - cell * .15, 0, w + cell * .3, height), Color(1, .84, .47, .3 * k))
	canvas.draw_rect(Rect2(x0, 0, w, height), Color(1, .87, .51, .55 * k))

## Lightning badge: amber disc, ink rim, white bolt.
static func badge(canvas: CanvasItem, at: Vector2, r: float, cell: float) -> void:
	if r <= .5: return
	var u := cell / 55.7
	canvas.draw_circle(at + Vector2(1.5, 3) * u, r, Color(.02, .12, .27, .3))
	canvas.draw_circle(at, r, AMBER)
	canvas.draw_circle(at + Vector2(-.25, -.3) * r, r * .45, Color("ffd98a"))
	canvas.draw_arc(at, r, 0, TAU, 32, INK, 2.6 * u, true)
	var bolt := PackedVector2Array()
	for p in [Vector2(.18, -.72), Vector2(-.38, .1), Vector2(-.02, .1), Vector2(-.16, .72), Vector2(.4, -.14), Vector2(.04, -.14)]: bolt.append(at + p * r)
	canvas.draw_colored_polygon(bolt, Color("fffdf3"))
	bolt.append(bolt[0])
	canvas.draw_polyline(bolt, INK, 2.0 * u, true)

## A jagged bolt down the middle of the strip, from `from` to `to` (y pixels).
static func bolt_path(rng: RandomNumberGenerator, x0: float, w: float, from: float, to: float, cell: float) -> PackedVector2Array:
	var points := PackedVector2Array()
	var x := x0 + w * rng.randf_range(.3, .7)
	var y := from
	while y <= to + cell * .45:
		points.append(Vector2(x, y))
		x = clampf(x + rng.randf_range(-.5, .5) * w * .55, x0 + w * .15, x0 + w * .85)
		y += cell * .45
	return points

static func bolts(canvas: CanvasItem, paths: Array, cell: float) -> void:
	var u := cell / 55.7
	for i in range(paths.size()):
		var thin := i == paths.size() - 1
		var points: PackedVector2Array = paths[i]
		if points.size() < 2: continue
		canvas.draw_polyline(points, Color(1, .67, .16, .45), (7.0 if thin else 12.0) * u, true)
		canvas.draw_polyline(points, Color("fff1a8"), (3.0 if thin else 5.0) * u, true)
		canvas.draw_polyline(points, Color.WHITE, (1.2 if thin else 2.0) * u, true)
