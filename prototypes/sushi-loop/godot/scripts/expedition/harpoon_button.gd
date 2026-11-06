extends Control
## Issue #23 contextual Harpoon button, centred between the steering arrows
## on their row (user-approved revision of the lower-right placement). A cream
## disc with the brown harpoon glyph matches the round Pause control; the ring
## around it fills while reloading (no countdown text) and turns green when
## ready. It fires on a fresh press only: holding never repeats, and its touch
## is independent of the steering touches handled by the playfield.
## Approved composition: design/harpoon-preview.
signal fired

const CREAM := Color("ffe8bc")
const CREAM_DOWN := Color("f5d39e")
const CREAM_MUTED := Color("f2dfbd")
const RIM := Color("d9a868")
const INK := Color("633b21")
const READY := Color("6cbf4b")
const RELOAD := Color("ffb02e")

## ready | reloading | paused
var state := "ready":
	set(value):
		if value == state: return
		state = value; _refresh_accessibility(); queue_redraw()
## Reload progress 0..1 (1 when ready).
var progress := 1.0:
	set(value):
		if is_equal_approx(value, progress): return
		progress = value; queue_redraw()
var held := false
var _touches: Dictionary = {}

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE
	accessibility_name = "Harpoon"
	_refresh_accessibility()

func _refresh_accessibility() -> void:
	accessibility_description = {"ready": "Ready to fire", "reloading": "Reloading", "paused": "Unavailable while paused"}.get(state, "")

## Touches only, like the playfield (desktop mouse arrives as emulated touch).
func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and not _touches.has(event.index):
			_touches[event.index] = true; accept_event(); _press()
		elif not event.pressed and _touches.has(event.index):
			_touches.erase(event.index); accept_event(); _release()

func _press() -> void:
	held = true; queue_redraw()
	if state == "ready": fired.emit()

func _release() -> void:
	if not _touches.is_empty(): return
	held = false; queue_redraw()

## Cancel a held press without firing (pause, backgrounding, focus loss).
func release() -> void:
	_touches.clear(); held = false; queue_redraw()

func _draw() -> void:
	var unit := size.x / 76.0
	var centre := size * 0.5
	var radius := size.x * 0.5
	var down := held and state != "paused"
	var lift := (1.0 if down else 5.0) * unit
	var press := (4.0 if down else 0.0) * unit
	var alpha := 0.5 if state == "paused" else 1.0
	# Soft drop shadow and the warm rim below the disc.
	draw_circle(centre + Vector2(0, 9 * unit), radius, Color(.02, .12, .27, .28 * alpha))
	draw_circle(centre + Vector2(0, lift + press), radius, Color(RIM, alpha))
	var face := CREAM_DOWN if down else (CREAM_MUTED if state == "reloading" else CREAM)
	draw_circle(centre + Vector2(0, press), radius, Color(face, alpha))
	# Ring: full green when ready, amber filling while reloading.
	var ring := radius + 3.5 * unit
	var width := 6.3 * unit
	var at := centre + Vector2(0, press)
	if state == "ready":
		draw_arc(at, ring, 0, TAU, 64, READY, width, true)
	else:
		draw_arc(at, ring, 0, TAU, 64, Color(INK, .28 * alpha), width, true)
		if progress > 0.0: draw_arc(at, ring, -PI / 2, -PI / 2 + TAU * progress, 64, Color(RELOAD, alpha), width, true)
	_glyph(at, unit, Color(INK, (1.0 if state == "ready" else .35) * alpha))

## Barbed head pointing up, shaft and rope loop (the review's SVG glyph).
func _glyph(at: Vector2, unit: float, color: Color) -> void:
	var s := size.x * 0.56 / 48.0
	var o := at - Vector2(24, 25) * s
	var head := PackedVector2Array([Vector2(24, 4), Vector2(33, 17), Vector2(27.5, 16), Vector2(27.5, 34), Vector2(20.5, 34), Vector2(20.5, 16), Vector2(15, 17)])
	for i in range(head.size()): head[i] = o + head[i] * s
	draw_colored_polygon(head, color)
	var outline := head.duplicate(); outline.append(head[0])
	draw_polyline(outline, color, 2.5 * s, true)
	# Two small lobes under the shaft: a rope loop.
	draw_arc(o + Vector2(20.5, 42.5) * s, 3.6 * s, 0, TAU, 20, color, 3.0 * s, true)
	draw_arc(o + Vector2(27.5, 42.5) * s, 3.6 * s, 0, TAU, 20, color, 3.0 * s, true)
	draw_line(o + Vector2(24, 34) * s, o + Vector2(24, 39) * s, color, 3.0 * s, true)
