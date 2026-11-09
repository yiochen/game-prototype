extends RefCounted
## Issue #23 harpoon drawing, shared by the expedition view and the gallery:
## the steel harpoon (barbed head, red collar), its braided rope from the
## ship's nose, and the slow-motion focus that closes on the strike. Code-drawn
## to match the approved HTML review (design/harpoon-preview). The rope draws
## over the world, so it never hides behind rocks.
const INK := Color("24364d")
const SHAFT := Color("c9d4df")
const HEAD := Color("eef3f7")
const COLLAR := Color("e2553f")
const ROPE_OUT := Color("6b4526")
const ROPE := Color("f3dcae")
const ROPE_TICK := Color("a77a4b")
const CREAM := Color("fff6df")
## #28: the Harpoon track changes the fired harpoon, never the ship. Tier 1 is
## the approved harpoon above; Lv 3 is longer with a double barb, brass collar
## and red rope; MAX is gold with three barbs, a teal glowing collar and gold rope.
## (Prototype: design/workshop-preview/harpoon.js.)
const TIERS := [
	{"length": .95, "shaft": SHAFT, "head": HEAD, "collar": COLLAR, "barbs": 1, "rope": [ROPE_OUT, ROPE, ROPE_TICK]},
	{"length": 1.08, "shaft": SHAFT, "head": HEAD, "collar": Color("d9a43a"), "barbs": 2, "rope": [Color("7a2a22"), Color("e2553f"), Color("ffb3a3")]},
	{"length": 1.2, "shaft": Color("f1d27a"), "head": Color("ffd552"), "collar": Color("3cc6c0"), "barbs": 3, "glow": Color("6ff3ea"), "rope": [Color("7a5418"), Color("ffd552"), Color("fff1b0")]},
]

static func style(tier: int) -> Dictionary: return TIERS[clampi(tier, 1, 3) - 1]
static func length(tier: int) -> float: return float(style(tier).length)

## Harpoon with its tip at `tip`, pointing along `angle`. Returns the tail
## (where the rope ties on). `head` false hides the head (buried in the body).
static func harpoon(canvas: CanvasItem, tip: Vector2, angle: float, cell: float, head := true, tier := 1) -> Vector2:
	var t := style(tier)
	var u := cell / 55.7
	var length := cell * float(t.length)
	var dir := Vector2.from_angle(angle)
	var side := dir.orthogonal()
	var tail := tip - dir * length
	var shaft_from := tip - dir * 8.0 * u
	canvas.draw_line(shaft_from, tail, INK, 5.2 * u + 4.4 * u)
	if t.has("glow"): canvas.draw_line(shaft_from, tail, Color(t.glow, .3), 20.0 * u)
	canvas.draw_line(shaft_from, tail, t.shaft, 5.2 * u)
	var collar_a := tail + dir * 6.0 * u
	var collar_b := tail + dir * 13.0 * u
	canvas.draw_line(collar_a, collar_b, INK, 8.4 * u + 4.4 * u)
	canvas.draw_line(collar_a, collar_b, t.collar, 8.4 * u)
	if t.has("glow"): canvas.draw_circle(collar_a.lerp(collar_b, .5), 3.0 * u, Color(1, 1, 1, .85))
	if head:
		# Extra barb pairs sit behind the head, each a little smaller.
		for i in range(int(t.barbs) - 1, -1, -1):
			var k := (1.15 if t.has("glow") else 1.0) if i == 0 else 1.0 - i * .12
			var at := tip - dir * i * 9.0 * u
			var points := PackedVector2Array([
				at + dir * 3.0 * u * k,
				at - dir * 14.0 * u * k + side * 8.0 * u * k, at - dir * 12.0 * u * k + side * 3.0 * u * k, at - dir * 16.0 * u * k + side * 2.6 * u * k,
				at - dir * 16.0 * u * k - side * 2.6 * u * k, at - dir * 12.0 * u * k - side * 3.0 * u * k, at - dir * 14.0 * u * k - side * 8.0 * u * k])
			canvas.draw_colored_polygon(points, t.head)
			var outline := points.duplicate(); outline.append(points[0])
			canvas.draw_polyline(outline, INK, 2.2 * u, true)
	return tail

## Braided rope from `from` to `to`. `slack` 0 is taut; flying shots trail a
## little wave, reeling ones sag.
static func rope(canvas: CanvasItem, from: Vector2, to: Vector2, cell: float, slack: float, time: float, alpha := 1.0, tier := 1) -> void:
	var colors: Array = style(tier).rope
	var u := cell / 55.7
	var delta := to - from
	var distance := maxf(delta.length(), 0.001)
	var normal := Vector2(-delta.y, delta.x) / distance
	var sag := slack * minf(distance * 0.18, cell * 0.8) * sin(time * 9.0)
	var control := (from + to) * 0.5 + normal * sag + Vector2(cell * 0.15 * slack, 0.0)
	var points := PackedVector2Array()
	var steps := maxi(6, int(distance / (6.0 * u)))
	for i in range(steps + 1):
		var t := float(i) / steps
		points.append(from.lerp(control, t).lerp(control.lerp(to, t), t))
	var shadow := PackedVector2Array()
	for p in points: shadow.append(p + Vector2(0, 2.5 * u))
	canvas.draw_polyline(shadow, Color(.02, .12, .27, .25 * alpha), 7.0 * u)
	canvas.draw_polyline(points, Color(colors[0], alpha), 5.0 * u)
	canvas.draw_polyline(points, Color(colors[1], alpha), 2.8 * u)
	# Braid ticks drift along the rope.
	var spacing := 6.6 * u
	var walked := fposmod(time * 40.0 * u, spacing)
	for i in range(points.size() - 1):
		var a := points[i]; var b := points[i + 1]
		var piece := a.distance_to(b)
		while walked < piece:
			var at := a.lerp(b, walked / piece)
			var along := (b - a) / piece
			canvas.draw_line(at - along * 1.1 * u, at + along * 1.1 * u, Color(colors[2], alpha), 2.8 * u)
			walked += spacing
		walked -= piece

## Slow-motion focus: dim the view outside a circle closing on `at` as `k`
## rises 0 → 1, with a bright ring on its edge.
static func focus(canvas: CanvasItem, at: Vector2, size: Vector2, cell: float, k: float) -> void:
	if k <= 0.01: return
	var e := k * k * (3.0 - 2.0 * k)
	var far := size.length()
	var radius := lerpf(far, cell * 1.5, e)
	var u := cell / 55.7
	# A very wide arc stroke darkens everything outside the circle.
	canvas.draw_arc(at, radius + far, 0, TAU, 96, Color(.016, .078, .19, .5 * e), far * 2.0)
	canvas.draw_arc(at, radius, 0, TAU, 96, Color(CREAM, .9 * e), 3.0 * u, true)
	canvas.draw_arc(at, radius * 1.18 + cell * .2, 0, TAU, 96, Color(CREAM, .45 * e), 1.5 * u, true)

## The hit flash: a ring expanding from the hook for `age` < 0.35 s.
static func hook_ring(canvas: CanvasItem, at: Vector2, cell: float, age: float) -> void:
	if age >= 0.35: return
	canvas.draw_arc(at, cell * (0.2 + age * 1.6), 0, TAU, 48, Color(CREAM, 1.0 - age / 0.35), 3.0 * cell / 55.7, true)
