extends Control
## #62 tea pour sheet, approved from design/tea-pour-preview/ (2026-11-08).
## A compact cream sheet over the live restaurant: the requested cup, the
## ImageGen teapot pivoting on its spout lip, and a curved tilt handle. One
## pour: once tea flows, easing back or letting go ends it, the drops land and
## the result is graded (features/tea.gd). The restaurant keeps running behind
## it; the full-rect shield keeps pour gestures off the scene.
## Geometry is in design px of the 390-wide prototype, scaled by `unit`.
const Tea = preload("res://scripts/features/tea.gd")
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const TEAPOT := preload("res://assets/ui/tea/teapot.png")

signal cancelled(customer_id: String)
signal finished(customer_id: String, grade: Dictionary)
signal closed(customer_id: String, grade: Dictionary)

const SHEET_HEIGHT := 452.0
const HEADER := 60.0
const CUP_X := 128.0
const CUP_FLOOR := 306.0
const ARC_CENTER := Vector2(292, 316)
const ARC_RADIUS := 70.0
const ARC_SWEEP := 80.0
const POT_SIZE := Vector2(158, 101)
const POT_TIP := Vector2(4.8, 32.7)
const SPOUT_GAP := 72.0
const RESULT_SECONDS := 1.5
const OUTLINE := Color("5a3a24")
const INK := Color("633b21")
const MUTED := Color("8a6a4c")
const TEA_TOP := Color("c5e47f")
const TEA_BOTTOM := Color("6c9c3c")
const VERDICTS := {"ideal": "Perfect pour!", "good": "Nice pour", "under": "A bit light…", "full": "Brimming!", "overflow": "Overflow!"}

var reduced_motion := false
var customer_id := ""
var cup: Dictionary = {}
var pour: Dictionary = {}
var tilt := 0.0
var shown_tilt := 0.0
var held := false
var result: Dictionary = {}
var result_age := 0.0
var opened_age := 0.0
var unit := 1.0
var sheet := Rect2()
var drops: Array = []
var spills: Array = []
var last_spill := 0.0
var clock := 0.0
var _drag_pointer := -2
var _drag_start_angle := 0.0
var _drag_start_tilt := 0.0
var title: Label
var subtitle: Label
var hint: Label
var close_button: Button
var _shapes: Dictionary = {}
var _verdict_font: Font

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_ALL
	accessibility_name = "Pour tea"
	title = _label(950, INK)
	subtitle = _label(700, MUTED)
	hint = _label(800, MUTED)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	close_button = Button.new()
	close_button.text = "×"
	close_button.accessibility_name = "Cancel pouring"
	var font := Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 850}
	close_button.add_theme_font_override("font", font)
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]: close_button.add_theme_color_override(key, INK)
	close_button.pressed.connect(cancel)
	add_child(close_button)
	_verdict_font = Typography.body()
	_verdict_font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 950}
	hide()

func _label(weight: int, color: Color) -> Label:
	var label := Label.new()
	var font := Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): weight}
	label.add_theme_font_override("font", font)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	add_child(label)
	return label

func open(id: String, cup_id: String, guest_label: String) -> void:
	customer_id = id
	cup = Tea.cup(cup_id)
	pour = Tea.new_pour(cup_id)
	tilt = 0.0; shown_tilt = 0.0; held = false; _drag_pointer = -2
	result = {}; result_age = 0.0; opened_age = 0.0
	drops.clear(); spills.clear(); last_spill = 0.0
	title.text = "Tea for %s" % guest_label
	subtitle.text = str(cup.name)
	hint.text = "One pour: drag the handle down the arc"
	close_button.show()
	_shapes = _cup_shapes()
	move_to_front()
	show()
	grab_focus()
	queue_redraw()

func is_open() -> bool:
	return visible and not customer_id.is_empty()

## Closed before any tea flowed: the request goes back to waiting.
func cancel() -> void:
	if not is_open() or not result.is_empty() or pour.poured: return
	var id := customer_id
	_close()
	cancelled.emit(id)

func _close() -> void:
	customer_id = ""
	hide()

func layout(area: Rect2) -> void:
	unit = area.size.x / 390.0
	var height := minf(SHEET_HEIGHT * unit, area.size.y * 0.62)
	unit = minf(unit, height / SHEET_HEIGHT)
	var width := 390.0 * unit
	sheet = Rect2(Vector2(area.position.x + (area.size.x - width) * 0.5, area.end.y - SHEET_HEIGHT * unit), Vector2(width, SHEET_HEIGHT * unit))
	var physical := maxf(0.001, get_viewport_transform().get_scale().x)
	PopupSkin.close_button(close_button, maxf(44 * unit, 44.01 / physical) / 96.0, physical)
	title.add_theme_font_size_override("font_size", int(17 * unit))
	subtitle.add_theme_font_size_override("font_size", int(12.5 * unit))
	hint.add_theme_font_size_override("font_size", int(14 * unit))
	title.size = Vector2(sheet.size.x - 90 * unit, 24 * unit)
	subtitle.size = title.size
	hint.size = Vector2(sheet.size.x - 28 * unit, 44 * unit)
	_place_labels()
	queue_redraw()

## The sheet slides up on opening; its labels and X ride with it.
func _slide() -> float:
	return 0.0 if reduced_motion else pow(1.0 - clampf(opened_age / 0.26, 0.0, 1.0), 3.0) * sheet.size.y

func _place_labels() -> void:
	var top := sheet.position + Vector2(0, _slide())
	close_button.position = top + Vector2(sheet.size.x - 14 * unit - close_button.size.x, 10 * unit)
	title.position = top + Vector2(14, 12) * unit
	subtitle.position = top + Vector2(14, 36) * unit
	hint.position = top + Vector2(14, SHEET_HEIGHT - 58) * unit

# ---------------------------------------------------------------- frame

func update(delta: float, audio = null) -> void:
	if not is_open(): return
	clock += delta
	opened_age += delta
	if result.is_empty():
		Tea.step(pour, delta, tilt, held)
		# Easing back to upright while still holding also ends the pour.
		if pour.poured and float(pour.flow) == 0.0 and held:
			held = false; tilt = 0.0; _drag_pointer = -2
		if Tea.done(pour): _finish()
		else:
			close_button.visible = not pour.poured
			hint.text = "Ease back or let go to serve" if pour.poured else "Tilt further to pour" if held else "One pour: drag the handle down the arc"
	else:
		result_age += delta
		if result_age >= (0.9 if reduced_motion else RESULT_SECONDS):
			var id := customer_id
			var graded := result
			_close()
			closed.emit(id, graded)
	var k := 1.0 if held else minf(1.0, delta / float(Tea.definition().pour.return_seconds) * 3.0)
	shown_tilt += (tilt - shown_tilt) * (minf(1.0, delta * 30.0) if held else k)
	_step_particles(delta)
	_place_labels()
	if audio != null: audio.set_pour(float(pour.flow) + (0.15 if float(pour.drip) > 0.0 else 0.0) if result.is_empty() else 0.0)
	queue_redraw()

func _finish() -> void:
	result = Tea.grade(pour)
	result_age = 0.0
	close_button.hide()
	var words := {"ideal": "Tip chance up", "good": "Tip chance up", "under": "Too little tea for the tip bonus" if not result.qualifies else "Served", "full": "Served", "overflow": "Served, a little messy"}
	hint.text = str(words[result.id])
	finished.emit(customer_id, result)

func _step_particles(delta: float) -> void:
	var tip := _tip()
	if float(pour.drip) > 0.0 and randf() < delta * 14.0: drops.append({"p": tip + Vector2(randf_range(-1, 1), 2), "vy": 30.0})
	if float(pour.spilled) > last_spill + 1.0:
		last_spill = float(pour.spilled)
		if spills.size() < 60 and randf() < 0.5:
			var side := -1.0 if randf() < 0.5 else 1.0
			var top_r := Tea.radius_at(cup, float(cup.height)) + float(cup.wall)
			spills.append({"p": Vector2(CUP_X + Tea.shift_at(cup, float(cup.height)) + side * top_r, CUP_FLOOR - float(cup.height)), "v": Vector2(side * randf_range(10, 40), randf_range(-20, 10))})
	var surface := CUP_FLOOR - Tea.level(pour)
	for drop in drops:
		drop.vy += 900.0 * delta
		drop.p.y += drop.vy * delta
	drops = drops.filter(func(d): return d.p.y < surface)
	for item in spills:
		item.v.y += 700.0 * delta
		item.p += item.v * delta
	spills = spills.filter(func(s): return s.p.y < CUP_FLOOR + float(cup.base) + 14.0)

func _tip() -> Vector2:
	return Vector2(CUP_X + Tea.shift_at(cup, float(cup.height)), CUP_FLOOR - float(cup.height) - SPOUT_GAP)

# ---------------------------------------------------------------- input (relative drag on the arc)

## Touch and mouse alike: the GUI may deliver a touch as either.
func _gui_input(event: InputEvent) -> void:
	if not is_open(): return
	accept_event()
	var pointer_id := -1
	var pressed := false
	var moved := false
	if event is InputEventScreenTouch: pointer_id = event.index; pressed = event.pressed
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT: pointer_id = 100; pressed = event.pressed
	elif event is InputEventScreenDrag: pointer_id = event.index; moved = true
	elif event is InputEventMouseMotion: pointer_id = 100; moved = true
	else: return
	var at := _stage(event.position)
	if moved:
		if pointer_id == _drag_pointer and held:
			tilt = clampf(_drag_start_tilt + (_angle(at) - _drag_start_angle) / ARC_SWEEP, 0.0, 1.0)
	elif pressed:
		if _drag_pointer == -2 and result.is_empty() and not pour.poured and _on_control(at):
			_drag_pointer = pointer_id
			_drag_start_angle = _angle(at)
			_drag_start_tilt = tilt
			held = true
	elif pointer_id == _drag_pointer:
		_release()

func _release() -> void:
	_drag_pointer = -2
	held = false
	tilt = 0.0

## Interrupted touches (focus loss, backgrounding) release the pot.
func interrupt() -> void:
	if held: _release()

func _unhandled_key_input(event: InputEvent) -> void:
	if not is_open() or not event is InputEventKey: return
	if event.keycode in [KEY_SPACE, KEY_DOWN]:
		if event.pressed and result.is_empty() and (held or not pour.poured):
			held = true
			tilt = minf(1.0, (tilt if tilt > 0.0 else 0.3) + (0.04 if event.echo else 0.0))
		elif not event.pressed and _drag_pointer == -2: _release()
		get_viewport().set_input_as_handled()
	elif event.pressed and event.keycode == KEY_UP and held:
		tilt = maxf(0.0, tilt - 0.08)
		get_viewport().set_input_as_handled()

func _stage(position_value: Vector2) -> Vector2:
	return (position_value - sheet.position) / unit - Vector2(0, HEADER)

func _angle(at: Vector2) -> float:
	var degrees := rad_to_deg(atan2(at.x - ARC_CENTER.x, -(at.y - ARC_CENTER.y)))
	return degrees + 360.0 if degrees < -120.0 else degrees

func _on_control(at: Vector2) -> bool:
	if at.distance_to(_arc_point(tilt * ARC_SWEEP)) <= 40.0: return true
	var degrees := _angle(at)
	return absf(at.distance_to(ARC_CENTER) - ARC_RADIUS) <= 40.0 and degrees >= -25.0 and degrees <= ARC_SWEEP + 25.0

func _arc_point(degrees: float) -> Vector2:
	var angle := deg_to_rad(degrees)
	return ARC_CENTER + Vector2(sin(angle), -cos(angle)) * ARC_RADIUS

# ---------------------------------------------------------------- drawing

func _cup_shapes() -> Dictionary:
	var left: PackedVector2Array = []
	var right: PackedVector2Array = []
	var outer_left: PackedVector2Array = []
	var outer_right: PackedVector2Array = []
	var height := float(cup.height)
	var wall := float(cup.wall)
	var y := 0.0
	while true:
		var r := Tea.radius_at(cup, y)
		var dx := Tea.shift_at(cup, y)
		left.append(Vector2(CUP_X + dx - r, CUP_FLOOR - y)); right.append(Vector2(CUP_X + dx + r, CUP_FLOOR - y))
		outer_left.append(Vector2(CUP_X + dx - r - wall, CUP_FLOOR - y)); outer_right.append(Vector2(CUP_X + dx + r + wall, CUP_FLOOR - y))
		if y >= height: break
		y = minf(height, y + 2.0)
	var interior: PackedVector2Array = left.duplicate(); interior.reverse(); interior.append_array(right)
	var bottom := CUP_FLOOR + float(cup.base)
	var base_dx := Tea.shift_at(cup, 0.0)
	var base_r := Tea.radius_at(cup, 0.0) + wall
	var outer: PackedVector2Array = outer_left.duplicate(); outer.reverse()
	outer.append_array([Vector2(CUP_X + base_dx - base_r, bottom - 6), Vector2(CUP_X + base_dx - base_r + 6, bottom), Vector2(CUP_X + base_dx + base_r - 6, bottom), Vector2(CUP_X + base_dx + base_r, bottom - 6)])
	outer.append_array(outer_right)
	var widest := 0.0
	for point in outer: widest = maxf(widest, absf(point.x - CUP_X))
	return {"interior": interior, "outer": outer, "bottom": bottom, "widest": widest}

func _draw() -> void:
	if not is_open(): return
	draw_rect(get_rect(), Color(0.04, 0.10, 0.17, 0.13))
	var origin := sheet.position + Vector2(0, _slide())
	# Sheet: cream with a maple top edge and rounded top corners.
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color("fbedd3")
	panel.border_color = Color("c98a4a")
	panel.border_width_top = int(6 * unit)
	panel.set_corner_radius(CORNER_TOP_LEFT, int(26 * unit)); panel.set_corner_radius(CORNER_TOP_RIGHT, int(26 * unit))
	panel.shadow_color = Color(0, 0, 0, 0.3); panel.shadow_size = int(16 * unit)
	draw_style_box(panel, Rect2(origin, sheet.size + Vector2(0, 2)))
	draw_set_transform_matrix(_stage_transform())
	_draw_cup()
	_draw_liquid()
	_draw_marks()
	_draw_stream()
	_draw_control()
	_draw_pot()
	_draw_feedback()
	draw_set_transform(Vector2.ZERO)
	_draw_verdict(origin)

func _glaze(points: PackedVector2Array) -> PackedColorArray:
	var colors: PackedColorArray = []
	var top := Color(str(cup.glaze[0]))
	var side := Color(str(cup.glaze[1]))
	for point in points: colors.append(side.lerp(top, 1.0 - pow(clampf(absf(point.x - CUP_X - 6) / maxf(1.0, float(_shapes.widest)), 0.0, 1.0), 1.2)))
	return colors

func _draw_cup() -> void:
	var glaze_top := Color(str(cup.glaze[0]))
	var glaze_side := Color(str(cup.glaze[1]))
	var bottom := float(_shapes.bottom)
	if int(cup.foot) > 0:
		var width := (Tea.radius_at(cup, 0.0) + float(cup.wall)) * 0.72
		var foot := Rect2(CUP_X + Tea.shift_at(cup, 0.0) - width, bottom - 4, width * 2, float(cup.foot) + 4)
		draw_rect(foot, glaze_side)
		draw_rect(foot, OUTLINE, false, 4.0)
	for handle in cup.get("handles", []):
		var side := float(handle.side)
		var y0 := float(handle.y0); var y1 := float(handle.y1)
		var a := Vector2(CUP_X + Tea.shift_at(cup, y0) + side * (Tea.radius_at(cup, y0) + float(cup.wall) - 2), CUP_FLOOR - y0)
		var b := Vector2(CUP_X + Tea.shift_at(cup, y1) + side * (Tea.radius_at(cup, y1) + float(cup.wall) - 2), CUP_FLOOR - y1)
		var bulge := (maxf(a.x * side, b.x * side) + 22.0) * side
		var curve: PackedVector2Array = []
		for step in range(17):
			var t := step / 16.0
			curve.append(a.bezier_interpolate(Vector2(bulge, a.y + 4), Vector2(bulge, b.y - 4), b, t))
		draw_polyline(curve, OUTLINE, 13.0, true)
		draw_polyline(curve, glaze_side, 6.0, true)
	for knob in cup.get("knobs", []):
		var at := Vector2(CUP_X + Tea.shift_at(cup, float(knob.y)) + float(knob.side) * (Tea.radius_at(cup, float(knob.y)) + float(cup.wall) + 4), CUP_FLOOR - float(knob.y))
		draw_circle(at, 8, glaze_side); draw_arc(at, 8, 0, TAU, 20, OUTLINE, 4.0, true)
	var outer: PackedVector2Array = _shapes.outer
	draw_polygon(outer, _glaze(outer))
	# Glaze band near the base and a thin line higher up, clipped to the body.
	for stripe in [[CUP_FLOOR - 16, 9.0, 0.85], [CUP_FLOOR - float(cup.height) * 0.62, 3.0, 0.5]]:
		_fill_clipped(outer, Rect2(CUP_X - 140, stripe[0], 280, stripe[1]), Color(str(cup.band), stripe[2]))
	_outline(outer, OUTLINE, 4.0)
	var interior: PackedVector2Array = _shapes.interior
	var cavity: PackedColorArray = []
	for point in interior: cavity.append(Color("fffaf0").lerp(Color("ead9bb"), clampf((point.y - (CUP_FLOOR - float(cup.height))) / float(cup.height), 0.0, 1.0)))
	draw_polygon(interior, cavity)
	_outline(interior, Color(OUTLINE, 0.75), 2.5)
	var rim := CUP_FLOOR - float(cup.height)
	var top_r := Tea.radius_at(cup, float(cup.height)); var top_dx := Tea.shift_at(cup, float(cup.height))
	for side in [-1.0, 1.0]:
		draw_line(Vector2(CUP_X + top_dx + side * top_r, rim), Vector2(CUP_X + top_dx + side * (top_r + float(cup.wall)), rim), OUTLINE, 5.0, true)
		draw_circle(Vector2(CUP_X + top_dx + side * top_r, rim), 2.5, OUTLINE)
		draw_circle(Vector2(CUP_X + top_dx + side * (top_r + float(cup.wall)), rim), 2.5, OUTLINE)

func _draw_liquid() -> void:
	var level := Tea.level(pour)
	if level <= 0.05: return
	var surface := CUP_FLOOR - level
	for polygon in Geometry2D.intersect_polygons(_shapes.interior, _rect_polygon(Rect2(0, surface, 390, level + 4))):
		var colors: PackedColorArray = []
		for point in polygon: colors.append(TEA_TOP.lerp(TEA_BOTTOM, clampf((point.y - surface) / maxf(30.0, level), 0.0, 1.0)))
		draw_polygon(polygon, colors)
	_fill_clipped(_shapes.interior, Rect2(0, surface - 1, 390, 2.5), Color("e9f8c4"))

## The acceptance zone on the cup itself: green good band, gold ideal band, dashed line.
func _draw_marks() -> void:
	var bands: Dictionary = Tea.definition().grade
	var line := CUP_FLOOR - float(cup.target_height)
	var good := float(bands.good_band) * float(cup.height)
	var ideal := float(bands.ideal_band) * float(cup.height)
	_fill_clipped(_shapes.outer, Rect2(0, line - good, 390, good * 2), Color("7ed15a", 0.32))
	_fill_clipped(_shapes.outer, Rect2(0, line - ideal, 390, ideal * 2), Color("ffc91c", 0.75))
	for edge in [line - good, line + good]: _fill_clipped(_shapes.outer, Rect2(0, edge - 1, 390, 2), Color("3f8a32", 0.8))
	var r := Tea.radius_at(cup, float(cup.target_height)); var dx := Tea.shift_at(cup, float(cup.target_height))
	draw_dashed_line(Vector2(CUP_X + dx - r + 1, line), Vector2(CUP_X + dx + r - 1, line), OUTLINE, 2.0, 6.0, true)

func _draw_stream() -> void:
	var tip := _tip()
	var flow := float(pour.flow)
	var surface := CUP_FLOOR - Tea.level(pour) + 2.0
	if flow > 0.0:
		var w := 2.0 + flow * 7.0
		var wobble := sin(clock * 40.0) * 0.4
		var stream := PackedVector2Array([tip + Vector2(-w * 0.5, 0), tip + Vector2(w * 0.5, 0), Vector2(tip.x + w * 0.4 + wobble, surface), Vector2(tip.x - w * 0.4 + wobble, surface)])
		draw_polygon(stream, PackedColorArray([Color("8dbb4d"), Color("8dbb4d"), Color("d4ee98"), Color("d4ee98")]))
	for drop in drops: draw_circle(drop.p, 2.6, Color("8dbb4d"))
	for item in spills: draw_circle(item.p, 3.5, Color("8dbb4d"))
	var puddle := minf(60.0, float(pour.spilled) / float(cup.capacity) * 300.0)
	if puddle > 0.0:
		draw_set_transform_matrix(_stage_transform() * Transform2D(0.0, Vector2(1.0, (4.0 + puddle / 10.0) / (float(_shapes.widest) + puddle)), 0.0, Vector2(CUP_X, float(_shapes.bottom) + 12)))
		draw_circle(Vector2.ZERO, float(_shapes.widest) + puddle, Color("9fcb5c", 0.8))
		draw_set_transform_matrix(_stage_transform())

func _stage_transform() -> Transform2D:
	return Transform2D(0.0, Vector2.ONE * unit, 0.0, sheet.position + Vector2(0, _slide() + HEADER * unit))

func _draw_control() -> void:
	var start := -PI * 0.5
	draw_arc(ARC_CENTER, ARC_RADIUS, start, start + deg_to_rad(ARC_SWEEP), 40, Color("e6d2ae"), 18.0, true)
	draw_circle(_arc_point(0), 9, Color("e6d2ae")); draw_circle(_arc_point(ARC_SWEEP), 9, Color("e6d2ae"))
	if tilt > 0.005:
		var color := Color("d8c3a2") if tilt <= float(Tea.definition().pour.dead_zone) else Color("8fbf5a")
		draw_arc(ARC_CENTER, ARC_RADIUS, start, start + deg_to_rad(tilt * ARC_SWEEP), 40, color, 10.0, true)
	var knob := _arc_point(tilt * ARC_SWEEP)
	draw_circle(knob + Vector2(0, 3), 25, Color(0, 0, 0, 0.2))
	draw_circle(knob, 25, Color.WHITE if held else Color("fff3dc"))
	draw_arc(knob, 25, 0, TAU, 40, OUTLINE, 4.0, true)
	var mini := Transform2D(-deg_to_rad(shown_tilt * float(Tea.definition().pour.max_tilt_degrees)), Vector2.ONE * 0.2, 0.0, knob + Vector2(-16, -4))
	draw_set_transform_matrix(_stage_transform() * mini)
	draw_texture_rect(TEAPOT, Rect2(-POT_TIP, POT_SIZE), false)
	draw_set_transform_matrix(_stage_transform())

func _draw_pot() -> void:
	var rotation := -deg_to_rad(shown_tilt * float(Tea.definition().pour.max_tilt_degrees))
	draw_set_transform_matrix(_stage_transform() * Transform2D(rotation, _tip()))
	draw_texture_rect(TEAPOT, Rect2(-POT_TIP, POT_SIZE), false)
	draw_set_transform_matrix(_stage_transform())

func _draw_feedback() -> void:
	if result.is_empty() or not result.id in ["ideal", "good"]: return
	var rim := CUP_FLOOR - float(cup.height)
	var x0 := CUP_X + Tea.shift_at(cup, float(cup.height))
	var strong: bool = result.id == "ideal"
	var count := 4 if strong else 3
	for index in range(count):
		var t := fmod(result_age / 1.3 + index * 0.12, 1.0) if not reduced_motion else 0.5
		var x := x0 + (index - (count - 1) * 0.5) * 14.0
		var steam: PackedVector2Array = []
		for step in range(9):
			var s := step / 8.0
			steam.append(Vector2(x + sin(s * TAU) * 5.0, rim - 6 - s * 40 + 6 - t * 32))
		draw_polyline(steam, Color(1, 1, 1, 0.85 * sin(PI * t)), 5.0, true)
	if strong and not reduced_motion:
		var t := clampf(result_age / 0.9, 0.0, 1.0)
		for index in range(8):
			var a := index / 8.0 * TAU
			var at := Vector2(x0, rim - 40) + Vector2(cos(a) * 70, sin(a) * 50) * t
			var size := 4.0 + 5.0 * t
			draw_colored_polygon(PackedVector2Array([at + Vector2(0, -size), at + Vector2(size * 0.35, 0), at + Vector2(0, size), at + Vector2(-size * 0.35, 0)]), Color("ffc91c", 1.0 - t))

func _draw_verdict(origin: Vector2) -> void:
	if result.is_empty(): return
	var text := str(VERDICTS[result.id])
	var size := int((22.0 if result.id in ["under", "full"] else 30.0) * unit)
	var pop := 1.0 if reduced_motion else minf(1.0, 0.5 + result_age / 0.38 * 0.6)
	size = maxi(1, int(size * pop))
	var width := _verdict_font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var at := origin + (Vector2(CUP_X, HEADER + CUP_FLOOR - float(cup.height) - 84) * unit) - Vector2(width * 0.5, 0)
	at.x = clampf(at.x, origin.x + 8 * unit, origin.x + sheet.size.x - width - 8 * unit)
	draw_string_outline(_verdict_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, int(7 * unit), OUTLINE)
	draw_string(_verdict_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color.WHITE)

func _outline(points: PackedVector2Array, color: Color, width: float) -> void:
	var closed := points.duplicate()
	closed.append(points[0])
	draw_polyline(closed, color, width, true)

func _fill_clipped(shape: PackedVector2Array, rect: Rect2, color: Color) -> void:
	for polygon in Geometry2D.intersect_polygons(shape, _rect_polygon(rect)): draw_colored_polygon(polygon, color)

static func _rect_polygon(rect: Rect2) -> PackedVector2Array:
	return PackedVector2Array([rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)])
