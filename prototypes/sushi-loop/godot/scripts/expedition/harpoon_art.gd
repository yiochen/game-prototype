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

## Harpoon with its tip at `tip`, pointing along `angle`. Returns the tail
## (where the rope ties on). `head` false hides the head (buried in the body).
static func harpoon(canvas: CanvasItem, tip: Vector2, angle: float, cell: float, head := true) -> Vector2:
	var u := cell / 55.7
	var length := cell * 0.95
	var dir := Vector2.from_angle(angle)
	var side := dir.orthogonal()
	var tail := tip - dir * length
	var shaft_from := tip - dir * 8.0 * u
	canvas.draw_line(shaft_from, tail, INK, 5.2 * u + 4.4 * u)
	canvas.draw_line(shaft_from, tail, SHAFT, 5.2 * u)
	var collar_a := tail + dir * 6.0 * u
	var collar_b := tail + dir * 13.0 * u
	canvas.draw_line(collar_a, collar_b, INK, 8.4 * u + 4.4 * u)
	canvas.draw_line(collar_a, collar_b, COLLAR, 8.4 * u)
	if head:
		var points := PackedVector2Array([
			tip + dir * 3.0 * u,
			tip - dir * 14.0 * u + side * 8.0 * u, tip - dir * 12.0 * u + side * 3.0 * u, tip - dir * 16.0 * u + side * 2.6 * u,
			tip - dir * 16.0 * u - side * 2.6 * u, tip - dir * 12.0 * u - side * 3.0 * u, tip - dir * 14.0 * u - side * 8.0 * u])
		canvas.draw_colored_polygon(points, HEAD)
		var outline := points.duplicate(); outline.append(points[0])
		canvas.draw_polyline(outline, INK, 2.2 * u, true)
	return tail

## Braided rope from `from` to `to`. `slack` 0 is taut; flying shots trail a
## little wave, reeling ones sag.
static func rope(canvas: CanvasItem, from: Vector2, to: Vector2, cell: float, slack: float, time: float) -> void:
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
	canvas.draw_polyline(shadow, Color(.02, .12, .27, .25), 7.0 * u)
	canvas.draw_polyline(points, ROPE_OUT, 5.0 * u)
	canvas.draw_polyline(points, ROPE, 2.8 * u)
	# Braid ticks drift along the rope.
	var spacing := 6.6 * u
	var walked := fposmod(time * 40.0 * u, spacing)
	for i in range(points.size() - 1):
		var a := points[i]; var b := points[i + 1]
		var piece := a.distance_to(b)
		while walked < piece:
			var at := a.lerp(b, walked / piece)
			var along := (b - a) / piece
			canvas.draw_line(at - along * 1.1 * u, at + along * 1.1 * u, ROPE_TICK, 2.8 * u)
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
