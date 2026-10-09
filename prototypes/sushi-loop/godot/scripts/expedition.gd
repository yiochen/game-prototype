class_name DiveScene
extends Control
## A finite, touch-first expedition. All simulation state is JSON-safe and saved.

signal finished(result: Dictionary)
signal sound_requested(id: String)
signal state_changed

const W := 720.0
const H := 1280.0
const SHIP_Y := 936.0
const FOLLOW_HALF := 104.0
const SHOT_COOLDOWN := 0.75
const INK := Color("182e3a")
const CREAM := Color("fff3d6")
const MINT := Color("96decb")
const GOLD := Color("f5c653")
const CORAL := Color("f08f78")
const ROUTES := ["Lantern Reef", "Ribbon Current", "Midnight Trench"]
const SPECIES := ["salmon", "shrimp", "eel"]
const CREATURE_NAMES := {"salmon": "Sunset Salmon", "shrimp": "Ribbon Shrimp", "eel": "Lantern Eel"}
const TRAVEL_TIMES := [47.0, 57.0, 67.0]

var route := 0
var equipment: Dictionary = {}
var tuning: Dictionary = {}
var upgrade_stats: Dictionary = {}
var route_data: Dictionary = {}
var route_name := "Lantern Reef"
var travel_duration := 47.0
var follow_half_width := 104.0
var cooldown_duration := 0.75
var protected_lesson := false
var species := "salmon"
var phase := "travel"
var elapsed := 0.0
var travel := 0.0
var sea_scroll := 0.0
var ship_x := 360.0
var hull := 100.0
var max_hull := 100.0
var pickups := 0
var resistance := 100.0
var creature_x := 360.0
var creature_clock := 0.0
var aim_left := 11.0
var grace := 0.0
var invulnerable := 0.0
var boost := 0.0
var bonus_ride := 0.0
var exit_left := 0.0
var shot_cooldown := 0.0
var attack_clock := 0.0
var attack_warning := 0.0
var attack_active := 0.0
var attack_x := 360.0
var attack_width := 62.0
var caught := false
var paused := false
var confirm_return := false
var resume_countdown := 0.0
var lesson := ""
var lesson_step := 0
var event_index := 0
var schedule: Array = []
var objects: Array = []
var shots: Array = []
var particles: Array = []
var notice := ""
var notice_left := 0.0
var ui_clock := 0.0
var ended := false
var pointer := -1
var pointer_x := 0.0
var mouse_drag := false
var font: Font
var display_font: Font
var textures: Dictionary = {}
var _configured := false
var reduced_motion := false
var paper_region := Rect2()
var headlight: ColorRect

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	font = ThemeDB.fallback_font
	display_font = font
	if ResourceLoader.exists("res://assets/fonts/Body.ttf"):
		font = load("res://assets/fonts/Body.ttf")
	elif ResourceLoader.exists("res://assets/Body.ttf"):
		font = load("res://assets/Body.ttf")
	var readable_font := FontVariation.new()
	readable_font.base_font = font
	readable_font.variation_opentype = {2003265652:600.0}
	font = readable_font
	if ResourceLoader.exists("res://assets/fonts/Display.ttf"):
		display_font = load("res://assets/fonts/Display.ttf")
	elif ResourceLoader.exists("res://assets/Display.ttf"):
		display_font = load("res://assets/Display.ttf")
	for asset in ["submarine", "creature_salmon", "creature_shrimp", "creature_eel", "rock", "gear", "portal"]:
		var path: String = "res://assets/%s.svg" % asset
		if ResourceLoader.exists(path):
			textures[asset] = load(path)
	# Painted production art replaces the earlier vector placeholders as available.
	for asset in ["ocean_environment", "expedition_card", "submarine", "creature_salmon", "creature_shrimp", "creature_eel", "rock", "gear", "portal", "kelp"]:
		var path: String = "res://assets/v2/%s.png" % asset
		if ResourceLoader.exists(path):
			textures[asset] = load(path)
	if textures.has("expedition_card"):
		# The generated sprite has faint alpha dust beyond its actual ink border.
		# These measured >25%-alpha bounds keep that padding out of nine slices.
		paper_region = Rect2(10, 212, 1760, 467)
	_create_headlight()
	if not _configured:
		setup(0, {})
	queue_redraw()

func _create_headlight() -> void:
	headlight = ColorRect.new()
	headlight.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lamp_shader := Shader.new()
	lamp_shader.code = """shader_type canvas_item;
render_mode blend_add, unshaded;
void fragment() {
 float width = (1.0 - UV.y) * 0.48 + 0.028;
 float edge = 1.0 - smoothstep(width * 0.55, width, abs(UV.x - 0.5));
 float depth = smoothstep(0.0, 0.65, UV.y);
 float glow = edge * depth * 0.30;
 COLOR = vec4(1.0, 0.76, 0.25, glow);
}"""
	var lamp_material := ShaderMaterial.new()
	lamp_material.shader = lamp_shader
	headlight.material = lamp_material
	add_child(headlight)

func _update_headlight() -> void:
	if headlight == null:
		return
	var drawing_scale := _drawing_scale()
	headlight.position = Vector2(ship_x - 135, _world_y(SHIP_Y) - 424) * drawing_scale
	headlight.size = Vector2(270, 330) * drawing_scale
	headlight.visible = not paused and lesson.is_empty() and resume_countdown <= 0.0 and not ended

func setup(route_index: int, upgrades: Dictionary, first_lesson: bool = false, restored: Dictionary = {}) -> void:
	_configured = true
	route = clampi(route_index, 0, 2)
	equipment = upgrades.duplicate(true)
	reduced_motion = bool(equipment.get("reduced_motion", false))
	protected_lesson = first_lesson
	if FileAccess.file_exists("res://expedition_routes.json"):
		var routes: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://expedition_routes.json"))
		if routes is Dictionary and routes.get("routes", []).size() > route:
			route_data = routes.routes[route]
	if FileAccess.file_exists("res://balance.json"):
		var config: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://balance.json"))
		if config is Dictionary:
			tuning = config.get("expedition", {})
			upgrade_stats = config.get("equipment", {})
			var charts: Array = config.get("routes", [])
			if charts.size() > route:
				route_name = str(charts[route].get("name", ROUTES[route]))
	travel_duration = float(tuning.get("travel_seconds", TRAVEL_TIMES)[route]) if tuning.has("travel_seconds") else float(route_data.get("travel_seconds", TRAVEL_TIMES[route]))
	follow_half_width = float(tuning.get("follow_half_width", FOLLOW_HALF))
	cooldown_duration = float(tuning.get("shot_cooldown", SHOT_COOLDOWN))
	species = str(equipment.get("species", SPECIES[route]))
	if not species in SPECIES:
		species = str(SPECIES[route])
	max_hull = _equipment_value("hull", 100.0, 25.0)
	hull = max_hull
	_build_schedule()
	if not restored.is_empty():
		_restore(restored)
	elif protected_lesson:
		lesson = "steer"
		lesson_step = 1
	else:
		_show_notice("Drag anywhere to steer", 4.0)

func _equipment_value(track: String, base: float, gain: float) -> float:
	var stat: Dictionary = upgrade_stats.get(track, {})
	return float(stat.get("base", base)) + float(equipment.get(track, 0)) * float(stat.get("gain", gain))

func _build_schedule() -> void:
	schedule.clear()
	# Each route has a composed, alternating safe line rather than random walls.
	var lanes: Array = route_data.get("salvage_lanes", [350, 240, 460, 490, 210, 360, 470, 280, 390])
	for i in range(lanes.size()):
		var at := 1.0 + i * float(route_data.get("section_spacing", 3.7))
		if at > travel_duration - 5.0:
			break
		for j in range(3):
			schedule.append({"at": at + j * 0.28, "kind": "salvage", "x": float(lanes[i]) + sin(j * 1.2) * 25.0, "value": 2})
		var side := 545.0 if float(lanes[i]) < 360.0 else 175.0
		schedule.append({"at": at + 0.5, "kind": "rock", "x": side, "radius": float(route_data.get("rock_radius", 48.0))})
		if bool(route_data.get("extra_rocks", false)) and i % 3 == 2:
			schedule.append({"at": at + 1.5, "kind": "rock", "x": 340.0, "radius": 36.0})
	schedule.append({"at": float(route_data.get("boost_at", 8.0)), "kind": "boost", "x": float(route_data.get("boost_x", 475.0))})
	schedule.append({"at": float(route_data.get("portal_at", 18.0)), "kind": "portal", "x": float(route_data.get("portal_x", 175.0))})
	schedule.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a.at) < float(b.at))

func snapshot() -> Dictionary:
	return {
		"version": 1, "route": route, "equipment": equipment.duplicate(true),
		"protected_lesson": protected_lesson, "species": species, "phase": phase,
		"elapsed": elapsed, "travel": travel, "sea_scroll": sea_scroll, "ship_x": ship_x,
		"hull": hull, "max_hull": max_hull, "pickups": pickups, "resistance": resistance,
		"creature_x": creature_x, "creature_clock": creature_clock, "aim_left": aim_left,
		"grace": grace, "invulnerable": invulnerable, "boost": boost, "bonus_ride": bonus_ride,
		"exit_left": exit_left, "shot_cooldown": shot_cooldown, "attack_clock": attack_clock,
		"attack_warning": attack_warning, "attack_active": attack_active,
		"attack_x": attack_x, "attack_width": attack_width, "caught": caught,
		"lesson": lesson, "lesson_step": lesson_step, "event_index": event_index,
		"objects": objects.duplicate(true), "shots": shots.duplicate(true),
		"notice": notice, "notice_left": notice_left,
	}

func _restore(saved: Dictionary) -> void:
	for key in snapshot().keys():
		if key == "version" or not saved.has(key):
			continue
		set(key, saved[key])
	route = clampi(route, 0, 2)
	_build_schedule()
	paused = true
	pointer = -1
	mouse_drag = false
	resume_countdown = 0.0

func suspend() -> void:
	if ended:
		return
	paused = true
	confirm_return = false
	resume_countdown = 0.0
	pointer = -1
	mouse_drag = false
	state_changed.emit()
	queue_redraw()

func _process(delta: float) -> void:
	ui_clock += delta
	if resume_countdown > 0.0:
		resume_countdown = maxf(0.0, resume_countdown - delta)
		if resume_countdown == 0.0:
			state_changed.emit()
	elif not paused and lesson.is_empty() and not ended:
		_tick(minf(delta, 0.05))
	if not paused and lesson.is_empty() and resume_countdown <= 0.0:
		_tick_particles(delta)
	_update_headlight()
	queue_redraw()

func _tick(delta: float) -> void:
	if ended or paused or resume_countdown > 0.0 or not lesson.is_empty():
		return
	elapsed += delta
	creature_clock += delta
	invulnerable = maxf(0.0, invulnerable - delta)
	shot_cooldown = maxf(0.0, shot_cooldown - delta)
	notice_left = maxf(0.0, notice_left - delta)
	boost = maxf(0.0, boost - delta)
	var keyboard := Input.get_axis("ui_left", "ui_right")
	if bonus_ride <= 0.0:
		ship_x = clampf(ship_x + keyboard * 390.0 * delta, 90.0, 630.0)
	var speed := 260.0 * (1.65 if boost > 0.0 else 1.0)
	sea_scroll += speed * delta
	if phase == "travel":
		_tick_travel(delta)
	elif phase == "aim" or phase == "pursuit":
		_tick_creature(delta)
	elif phase == "exit":
		exit_left -= delta
		if exit_left <= 0.0:
			_finish("complete")
	if ended:
		return
	_move_objects(delta, speed)
	if not ended:
		_tick_shots(delta)

func _tick_travel(delta: float) -> void:
	if bonus_ride > 0.0:
		bonus_ride = maxf(0.0, bonus_ride - delta)
		ship_x = lerpf(ship_x, 360.0 + sin(elapsed * 1.6) * 135.0, delta * 3.0)
		if int(bonus_ride * 2.0) != int((bonus_ride + delta) * 2.0):
			_collect(3)
		if bonus_ride == 0.0:
			_show_notice("Back on course", 2.4)
		return
	travel += delta * (1.4 if boost > 0.0 else 1.0)
	if _current_active():
		ship_x = clampf(ship_x + _current_direction() * float(route_data.get("current_strength", 49.0)) * delta, 90.0, 630.0)
	while event_index < schedule.size() and float(schedule[event_index].at) <= travel:
		var item: Dictionary = schedule[event_index].duplicate()
		item["y"] = -80.0
		objects.append(item)
		event_index += 1
	if travel >= travel_duration:
		objects.clear()
		boost = 0.0
		_start_aim()

func _current_active() -> bool:
	return route > 0 and phase == "travel" and int(travel / 8.0) % 2 == 1 and bonus_ride <= 0.0

func _current_direction() -> float:
	return 1.0 if int(travel / 8.0) % 4 == 1 else -1.0

func _move_objects(delta: float, speed: float) -> void:
	var surviving: Array = []
	for object in objects:
		if ended:
			break
		object["y"] = float(object.y) + speed * delta
		var pos := Vector2(float(object.x), float(object.y))
		var distance := pos.distance_to(Vector2(ship_x, SHIP_Y))
		var removed := false
		if bonus_ride > 0.0:
			removed = true
		elif object.kind == "salvage":
			var reach := _equipment_value("collector", 60.0, 14.0)
			if distance < reach:
				_collect(int(object.get("value", 2)))
				removed = true
		elif object.kind == "rock" and distance < float(object.get("radius", 45.0)) + 33.0:
			if boost > 0.0:
				_spark(pos, MINT, 8)
			else:
				_damage(float(tuning.get("collision_damage", 24.0)))
			removed = true
		elif object.kind == "boost" and distance < 76.0:
			boost = 4.5
			_show_notice("Smooth sailing • shield + speed", 3.0)
			sound_requested.emit("boost")
			_spark(pos, GOLD, 14)
			removed = true
		elif object.kind == "portal" and distance < 83.0:
			bonus_ride = 5.5
			_show_notice("Secret current! Enjoy the ride", 4.0)
			sound_requested.emit("portal")
			removed = true
		if not removed and float(object.y) < H + 100.0:
			surviving.append(object)
	objects = surviving

func _start_aim() -> void:
	phase = "aim"
	creature_clock = 0.0
	creature_x = 360.0
	aim_left = 12.0 if protected_lesson else float(tuning.get("aim_seconds", 10.5))
	resistance = 100.0
	attack_clock = 0.0
	_show_notice("A curious visitor… line up your shot!", 3.5)
	sound_requested.emit("sonar")
	if protected_lesson and lesson_step < 2:
		lesson = "shoot"
		lesson_step = 2
	state_changed.emit()

func _tick_creature(delta: float) -> void:
	var frequency := 0.55 + route * 0.12
	var amplitude := 145.0 + route * 17.0
	# Smooth, readable paths remain identical during the escape warning.
	creature_x = 360.0 + sin(creature_clock * frequency) * amplitude
	if species == "shrimp":
		creature_x = 360.0 + sin(creature_clock * 0.7) * 145.0 + sin(creature_clock * 1.4) * 22.0
	if phase == "aim":
		aim_left -= delta
		if aim_left <= 0.0:
			if protected_lesson:
				aim_left = 12.0
				_show_notice("Try again • steer underneath, then tap", 4.0)
			else:
				_escape()
		return
	var following := absf(ship_x - creature_x) <= follow_half_width
	if following:
		grace = 0.0
		resistance = maxf(0.0, resistance - _equipment_value("harpoon", 8.5, 2.0) * delta)
	else:
		grace += delta
		if grace >= float(tuning.get("grace_seconds", 2.7)):
			if protected_lesson:
				phase = "aim"
				aim_left = 12.0
				grace = 0.0
				attack_warning = 0.0
				attack_active = 0.0
				resistance = 100.0
				_show_notice("Cable slipped! You can try another shot", 4.0)
			else:
				_escape()
			return
	if resistance <= 0.0:
		caught = true
		sound_requested.emit("catch")
		_finish("complete")
		return
	_tick_attack(delta)

func _tick_attack(delta: float) -> void:
	attack_clock += delta
	if attack_warning > 0.0:
		attack_warning = maxf(0.0, attack_warning - delta)
		if attack_warning == 0.0:
			attack_active = 0.45
			sound_requested.emit("warning")
	elif attack_active > 0.0:
		attack_active = maxf(0.0, attack_active - delta)
		if absf(ship_x - attack_x) < attack_width * 0.5 + 24.0:
			_damage(18.0 if route == 0 else 23.0)
	elif attack_clock > 4.5:
		attack_clock = 0.0
		# The strip is fixed at windup and leaves at least 110 px of usable following band.
		attack_x = creature_x + (52.0 if int(creature_clock / 4.5) % 2 == 0 else -52.0)
		attack_width = 55.0 if species != "eel" else 65.0
		attack_warning = 1.5
		sound_requested.emit("sonar")

func _fire() -> void:
	if phase != "aim" or shot_cooldown > 0.0 or paused or resume_countdown > 0.0 or not lesson.is_empty():
		return
	shot_cooldown = cooldown_duration
	shots.append({"x": ship_x, "y": SHIP_Y - 75.0})
	sound_requested.emit("shot")
	_spark(Vector2(ship_x, SHIP_Y - 74.0), CREAM, 5)

func _tick_shots(delta: float) -> void:
	var live: Array = []
	for shot in shots:
		var previous_y := float(shot.y)
		shot["y"] = previous_y - delta * float(tuning.get("shot_speed", 1250.0))
		if phase == "aim" and previous_y >= 375.0 and float(shot.y) <= 430.0 and absf(float(shot.x) - creature_x) < 75.0:
			phase = "pursuit"
			grace = 0.0
			attack_clock = 0.0
			sound_requested.emit("hook")
			_spark(Vector2(creature_x, 392.0), GOLD, 18)
			_show_notice("Hooked! Stay in the glowing strip", 3.5)
			if protected_lesson and lesson_step < 3:
				lesson = "follow"
				lesson_step = 3
			state_changed.emit()
		elif float(shot.y) > -40.0 and phase == "aim":
			live.append(shot)
	shots = live

func _damage(amount: float) -> void:
	if invulnerable > 0.0 or boost > 0.0 or bonus_ride > 0.0 or ended:
		return
	hull = maxf(1.0 if protected_lesson else 0.0, hull - amount)
	invulnerable = float(tuning.get("hit_invulnerability", 1.45))
	if phase == "pursuit":
		resistance = minf(100.0, resistance + 6.0)
	sound_requested.emit("hit")
	_spark(Vector2(ship_x, SHIP_Y), CORAL, 15)
	if hull <= 0.0:
		_finish("failed")
	state_changed.emit()

func _collect(amount: int) -> void:
	pickups += amount
	sound_requested.emit("pickup")
	_spark(Vector2(ship_x, SHIP_Y - 40.0), GOLD, 6)

func _escape() -> void:
	phase = "exit"
	exit_left = 3.0
	attack_warning = 0.0
	attack_active = 0.0
	_show_notice("The visitor slipped away. Homeward bound!", 3.0)
	state_changed.emit()

func _finish(outcome: String) -> void:
	if ended:
		return
	ended = true
	pointer = -1
	mouse_drag = false
	phase = "ended"
	finished.emit({"outcome": outcome, "pickups": pickups, "completion_bonus": tuning.get("completion_bonus", [20, 28, 36])[route] if outcome == "complete" else 0, "caught": caught, "species": species, "route": route, "elapsed": elapsed})

func _show_notice(message: String, seconds: float) -> void:
	notice = message
	notice_left = seconds

func _spark(at: Vector2, color: Color, count: int) -> void:
	if reduced_motion:
		return
	for i in range(count):
		var angle := i * TAU / maxf(1.0, count)
		particles.append({"x": at.x, "y": at.y, "vx": cos(angle) * (90.0 + i * 5.0), "vy": sin(angle) * 100.0, "life": 0.6, "color": color})

func _tick_particles(delta: float) -> void:
	var remaining: Array = []
	for p in particles:
		p.life = float(p.life) - delta
		p.x = float(p.x) + float(p.vx) * delta
		p.y = float(p.y) + float(p.vy) * delta
		if float(p.life) > 0.0:
			remaining.append(p)
	particles = remaining

func _drawing_scale() -> Vector2:
	# Only width determines artwork/text size. Extra phone height adds water and
	# spacing, never elongates the submarine, buttons, or handwritten typography.
	var factor := size.x / W if size.x > 0.0 else 1.0
	return Vector2.ONE * factor

func _canvas_height() -> float:
	return size.y / _drawing_scale().y if size.y > 0.0 else H

func _extra_height() -> float:
	return _canvas_height() - H

func _middle_offset() -> float:
	return _extra_height() * 0.5

func _world_y(y: float) -> float:
	return y * _canvas_height() / H

func _harpoon_position() -> Vector2:
	return Vector2(601, 1114 + _extra_height())

func _set_canvas_transform(offset := Vector2.ZERO) -> void:
	var factor := _drawing_scale()
	draw_set_transform(offset * factor, 0.0, factor)

func _ocean_rect() -> Rect2:
	var factor := maxf(1.0, (_canvas_height() + 128.0) / 1408.0)
	var dimensions := Vector2(792, 1408) * factor
	var progress := clampf(travel / travel_duration, 0.0, 1.0)
	return Rect2(Vector2((W - dimensions.x) * 0.5 + (ship_x - 360.0) * -0.025, -128.0 + progress * 110.0), dimensions)

func _virtual_position(position_in_viewport: Vector2) -> Vector2:
	var local := get_global_transform_with_canvas().affine_inverse() * position_in_viewport
	# This is the responsive layout canvas; world simulation keeps its original
	# 720x1280 coordinates. Dragging is horizontal, so its rule is unchanged.
	return local / _drawing_scale()

func _input(event: InputEvent) -> void:
	if ended or not is_visible_in_tree():
		return
	# Godot may emit a synthetic mouse event alongside each touchscreen event.
	# Ignoring it keeps the second finger from reanchoring the steering finger.
	if (event is InputEventMouseButton or event is InputEventMouseMotion) and event.device == -1:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			if confirm_return:
				confirm_return = false
			elif paused:
				_resume()
			else:
				suspend()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_SPACE:
			_fire()
		return
	if event is InputEventScreenTouch:
		var p := _virtual_position(event.position)
		if event.pressed:
			if _press(p):
				get_viewport().set_input_as_handled()
			elif pointer == -1 and p.y > 150.0:
				pointer = event.index
				pointer_x = p.x
		elif event.index == pointer:
			pointer = -1
	elif event is InputEventScreenDrag and event.index == pointer:
		var p := _virtual_position(event.position)
		_drag_to(p.x)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		var p := _virtual_position(event.position)
		if event.pressed:
			if not _press(p) and p.y > 150.0:
				mouse_drag = true
				pointer_x = p.x
		else:
			mouse_drag = false
	elif event is InputEventMouseMotion and mouse_drag:
		_drag_to(_virtual_position(event.position).x)

func _drag_to(x: float) -> void:
	if not paused and lesson.is_empty() and resume_countdown <= 0.0 and bonus_ride <= 0.0:
		ship_x = clampf(ship_x + x - pointer_x, 90.0, 630.0)
	pointer_x = x

func _press(p: Vector2) -> bool:
	var menu_p := p - Vector2(0, _middle_offset())
	if confirm_return:
		if Rect2(142, 718, 436, 76).has_point(menu_p):
			_finish("early")
		elif Rect2(142, 816, 436, 70).has_point(menu_p):
			confirm_return = false
		return true
	if paused:
		if Rect2(142, 692, 436, 82).has_point(menu_p):
			_resume()
		elif Rect2(142, 794, 436, 70).has_point(menu_p):
			confirm_return = true
			sound_requested.emit("ui")
		return true
	if not lesson.is_empty():
		if Rect2(142, 745, 436, 78).has_point(menu_p):
			lesson = ""
			pointer = -1
			mouse_drag = false
			sound_requested.emit("ui")
		return true
	if Rect2(600, 42, 84, 84).has_point(p):
		suspend()
		sound_requested.emit("ui")
		return true
	if phase == "aim" and p.distance_to(_harpoon_position()) < 81.0:
		_fire()
		return true
	return false

func _resume() -> void:
	paused = false
	confirm_return = false
	resume_countdown = 2.4
	pointer = -1
	mouse_drag = false
	sound_requested.emit("ui")

func _draw() -> void:
	if font == null:
		return
	_update_headlight()
	_set_canvas_transform()
	_draw_ocean()
	if phase == "pursuit":
		_draw_following_strip()
	_draw_attacks()
	for object in objects:
		_draw_object(object)
	if phase in ["aim", "pursuit", "exit"]:
		_draw_creature()
	for shot in shots:
		var sp := Vector2(float(shot.x), _world_y(float(shot.y)))
		draw_line(sp + Vector2(0, 38), sp, CREAM, 6.0, true)
		draw_polyline(PackedVector2Array([sp + Vector2(-10, 12), sp, sp + Vector2(10, 12)]), GOLD, 5.0, true)
	_draw_ship()
	for p in particles:
		var color: Color = p.color
		color.a = clampf(float(p.life) * 2.0, 0.0, 1.0)
		draw_circle(Vector2(float(p.x), _world_y(float(p.y))), 3.0 + float(p.life) * 5.0, color)
	_draw_hud()
	if phase == "aim":
		_draw_harpoon()
	if notice_left > 0.0 and not paused and lesson.is_empty():
		var alpha := minf(1.0, notice_left)
		var notice_y := (1210.0 if phase == "aim" else 1167.0) + _extra_height()
		_panel(Rect2(54, notice_y, 612, 48 if phase == "aim" else 60), Color(0.08, 0.19, 0.23, alpha * 0.92), Color(0.6, 0.85, 0.78, alpha * 0.4), 23)
		_text(notice, Vector2(64, notice_y + (32 if phase == "aim" else 39)), 22, Color(0.95, 0.96, 0.85, alpha), 592, HORIZONTAL_ALIGNMENT_CENTER)
	if paused:
		_draw_pause()
	elif not lesson.is_empty():
		_draw_lesson()
	elif resume_countdown > 0.0:
		draw_rect(Rect2(0, 0, W, _canvas_height()), Color(0.05, 0.12, 0.17, 0.48))
		_set_canvas_transform(Vector2(0, _middle_offset()))
		_circle(Vector2(360, 600), 92.0, CREAM, INK, 5.0)
		_text(str(ceili(resume_countdown)), Vector2(270, 632), 78, INK, 180, HORIZONTAL_ALIGNMENT_CENTER, true)
		_text("Ready when you are", Vector2(100, 757), 28, CREAM, 520, HORIZONTAL_ALIGNMENT_CENTER)
		_text("Touch and hold to prepare your steering", Vector2(55, 800), 22, MINT, 610, HORIZONTAL_ALIGNMENT_CENTER)
		_set_canvas_transform()

func _draw_ocean() -> void:
	if not textures.has("ocean_environment"):
		_draw_ocean_fallback()
		return
	# One overscanned painted plate drifts gradually with the voyage. It never
	# wraps or exposes a seam; separate foreground life supplies faster parallax.
	var ocean_tint := Color.WHITE
	if route == 1:
		ocean_tint = Color(0.91, 1.0, 0.96)
	elif route == 2:
		ocean_tint = Color(0.79, 0.87, 1.0)
	draw_texture_rect(textures.ocean_environment, _ocean_rect(), false, ocean_tint)
	# Subtle painterly beams sit behind every interactive element.
	for i in range(3):
		var x := 90.0 + i * 235.0 + (0.0 if reduced_motion else sin(elapsed * 0.11 + i) * 28.0)
		var points := PackedVector2Array([Vector2(x, -20), Vector2(x + 28, -20), Vector2(x + 175, _world_y(930)), Vector2(x - 90, _world_y(930))])
		draw_polygon(points, PackedColorArray([Color(0.59, 0.83, 0.84, 0.035), Color(0.59, 0.83, 0.84, 0.035), Color(0.59, 0.83, 0.84, 0.0), Color(0.59, 0.83, 0.84, 0.0)]))
	for i in range(24):
		var motion := 0.0 if reduced_motion else elapsed * (10.0 + i % 5)
		var x := fmod(i * 177.7 + 33.0, W)
		var y := fposmod(i * 139.7 - motion, _canvas_height() + 40) - 20
		var radius := 2.0 + (i % 6) * 0.85
		var at := Vector2(x + sin(elapsed * 0.6 + i) * (0 if reduced_motion else 5), y)
		draw_circle(at, radius, Color(0.62, 0.9, 0.91, 0.055))
		draw_arc(at, radius, 0.0, TAU, 16, Color(0.49, 0.87, 0.92, 0.19), 1.1, true)
		draw_arc(at + Vector2(-0.7, -0.7), radius * 0.72, 3.7, 4.8, 6, Color(0.78, 0.98, 1.0, 0.24), 1.0, true)
	if textures.has("kelp"):
		for i in range(5):
			var at := Vector2(43.0 if i % 2 == 0 else 678.0, fposmod(i * (_canvas_height() + 300.0) / 5.0 + sea_scroll * 0.07, _canvas_height() + 300.0) - 130)
			var tilt := 0.0 if reduced_motion else sin(elapsed * 0.9 + i * 2.3) * 0.075
			_draw_rotated_texture(textures.kelp, at, Vector2(92, 174), tilt, Color(0.77, 0.92, 0.86, 0.80))
	# Tiny distant fish have hand-cut silhouettes rather than attention-grabbing
	# outlines. The detailed fauna in the painted plate remains the main read.
	if not reduced_motion:
		for i in range(8):
			var x := fposmod(i * 103.0 + elapsed * (7.0 + i % 3), 1000.0) - 140.0
			var y := _world_y(265.0 + i * 111.0) + sin(elapsed * 0.55 + i) * 8.0
			var at := Vector2(x, y)
			var tail := 6.0 + i % 3
			draw_colored_polygon(PackedVector2Array([at + Vector2(-8, 0), at + Vector2(-13, -tail), at + Vector2(-13, tail)]), Color(0.03, 0.14, 0.23, 0.34))
			draw_colored_polygon(PackedVector2Array([at + Vector2(-8, 0), at + Vector2(0, -4), at + Vector2(9, 0), at + Vector2(0, 4)]), Color(0.03, 0.14, 0.23, 0.34))
	if _current_active() or bonus_ride > 0.0:
		_draw_current_ribbons()
	if phase == "travel" and travel < 6.0:
		var alpha := clampf(6.0 - travel, 0.0, 1.0)
		_text("DIVE 0%d" % (route + 1), Vector2(70, 254), 20, Color(0.93, 0.84, 0.65, alpha), 580, HORIZONTAL_ALIGNMENT_CENTER)
		_text(route_name, Vector2(42, 314), 44, Color(0.02, 0.1, 0.16, alpha * 0.8), 640, HORIZONTAL_ALIGNMENT_CENTER, true)
		_text(route_name, Vector2(40, 310), 44, Color(1, 0.94, 0.8, alpha), 640, HORIZONTAL_ALIGNMENT_CENTER, true)
		_line(Vector2(294, 332), Vector2(426, 332), Color(0.87, 0.71, 0.39, alpha), 2.0)

func _draw_current_ribbons() -> void:
	var direction := _current_direction() if bonus_ride <= 0.0 else 1.0
	for i in range(5):
		var line := PackedVector2Array()
		var base_y := fposmod(i * (_canvas_height() + 170.0) / 5.0 + sea_scroll * 0.25, _canvas_height() + 170.0) - 100
		for j in range(32):
			var x := -60.0 + j * 28.0
			line.append(Vector2(x, base_y + sin(x * 0.005 + i + elapsed * 0.12 * direction) * 84))
		draw_polyline(line, Color(0.22, 0.7, 0.84, 0.08), 22, true)
		draw_polyline(line, Color(0.28, 0.78, 0.88, 0.23), 2, true)
		var drift := fposmod(elapsed * 110.0 * direction + i * 187.0, 720.0)
		var y := base_y + sin(drift * 0.005 + i + elapsed * 0.12 * direction) * 84
		draw_polyline(PackedVector2Array([Vector2(drift - direction * 14, y - 7), Vector2(drift, y), Vector2(drift - direction * 14, y + 7)]), Color(0.50, 0.86, 0.87, 0.42), 2.3, true)

func _draw_rotated_texture(texture: Texture2D, center: Vector2, dimensions: Vector2, angle: float, tint: Color = Color.WHITE) -> void:
	var drawing_scale := _drawing_scale()
	draw_set_transform(center * drawing_scale, angle, drawing_scale)
	draw_texture_rect(texture, Rect2(-dimensions * 0.5, dimensions), false, tint)
	draw_set_transform(Vector2.ZERO, 0.0, drawing_scale)

func _draw_ocean_fallback() -> void:
	var canvas_h := _canvas_height()
	draw_rect(Rect2(0, 0, W, canvas_h), Color("103944") if route < 2 else Color("102c3e"))
	# Broad quiet light shafts, wobbly canyon walls, and sparse pencil-like grain.
	draw_colored_polygon(PackedVector2Array([Vector2(270, 0), Vector2(395, 0), Vector2(620, canvas_h), Vector2(180, canvas_h)]), Color(0.19, 0.48, 0.47, 0.1))
	var left := PackedVector2Array([Vector2(0, 0)])
	var right := PackedVector2Array([Vector2(W, 0)])
	for i in range(ceili(canvas_h / 80.0) + 2):
		var y := i * 80.0
		var wave := sin((y + sea_scroll * 0.25) * 0.009) * 20.0
		left.append(Vector2(48.0 + wave + sin(i * 2.0) * 8.0, y))
		right.append(Vector2(666.0 + wave * 0.85 + cos(i * 1.6) * 9.0, y))
	left.append(Vector2(0, canvas_h))
	right.append(Vector2(W, canvas_h))
	draw_colored_polygon(left, Color("174852"))
	draw_colored_polygon(right, Color("174852"))
	draw_polyline(left, Color("1f5960"), 4.0, true)
	draw_polyline(right, Color("1f5960"), 4.0, true)
	for i in range(36):
		var x := fmod(i * 137.4 + 31.0, 690.0)
		var y := fmod(i * 191.8 + (0.0 if reduced_motion else sea_scroll) * (0.18 + (i % 3) * 0.08), canvas_h + 70.0) - 30.0
		var tint := Color(0.56, 0.79, 0.71, 0.15 + (i % 3) * 0.06)
		draw_arc(Vector2(x, y), 3.0 + i % 5, 0.1, 5.8, 10, tint, 1.5, true)
	for i in range(9):
		var y := fmod(i * 177.0 + sea_scroll * 0.8, canvas_h + 190.0) - 90.0
		_draw_coral(Vector2(24.0 if i % 2 == 0 else 696.0, y), i)
	if _current_active() or bonus_ride > 0.0:
		var direction := _current_direction() if bonus_ride <= 0.0 else 1.0
		for i in range(16):
			var y := fmod(i * 83.0 + sea_scroll * 0.3, canvas_h)
			var x := fmod(i * 127.0 + elapsed * 95.0 * direction + 10000.0, W)
			draw_line(Vector2(x - 44, y), Vector2(x + 44, y), Color(0.5, 0.9, 0.82, 0.17), 3.0, true)
			draw_line(Vector2(x + 44 * direction, y), Vector2(x + 29 * direction, y - 9), Color(0.5, 0.9, 0.82, 0.22), 3.0, true)
	if phase == "travel" and travel < 6.0:
		var alpha := clampf(6.0 - travel, 0.0, 1.0)
		_text("DIVE 0%d" % (route + 1), Vector2(70, 264), 21, Color(0.63, 0.84, 0.74, alpha), 580, HORIZONTAL_ALIGNMENT_CENTER)
		_text(route_name, Vector2(40, 321), 44, Color(1, 0.95, 0.83, alpha), 640, HORIZONTAL_ALIGNMENT_CENTER, true)
		_line(Vector2(274, 343), Vector2(446, 343), Color(0.93, 0.76, 0.35, alpha), 3.0)

func _draw_coral(at: Vector2, index: int) -> void:
	var color := Color("367775") if index % 3 == 0 else Color("285d68")
	for j in range(4):
		var tip := at + Vector2((j - 1.5) * 18.0, -28.0 - sin(j * 2.4 + index) * 23.0)
		draw_line(at + Vector2(0, 25), tip, INK, 12.0, true)
		draw_line(at + Vector2(0, 25), tip, color, 7.0, true)
		draw_circle(tip, 4.0, color)

func _draw_following_strip() -> void:
	var aligned := absf(ship_x - creature_x) <= follow_half_width
	var tint := MINT if aligned else CORAL
	draw_rect(Rect2(creature_x - follow_half_width, 0, follow_half_width * 2.0, _canvas_height()), Color(tint, 0.10))
	for side in [-1, 1]:
		var x: float = creature_x + follow_half_width * side
		for i in range(ceili(_canvas_height() / 93.0) + 1):
			var y := fmod(i * 93.0 + sea_scroll * 0.3, _canvas_height())
			draw_line(Vector2(x, y), Vector2(x, y + 42), Color(tint, 0.35), 3.0, true)
	var cable := PackedVector2Array()
	var start := Vector2(ship_x, _world_y(SHIP_Y) - 78.0)
	var end := Vector2(creature_x, _world_y(382.0) + 45.0)
	for i in range(20):
		var weight := i / 19.0
		var point := start.lerp(end, weight)
		point.x += sin(weight * PI) * (16.0 if aligned else 2.0) + sin(weight * 24.0 + elapsed * 7.0) * minf(grace * 3.0, 6.0)
		cable.append(point)
	draw_polyline(cable, INK, 8.0, true)
	draw_polyline(cable, GOLD if aligned else CORAL, 4.0, true)
	if grace > 1.4:
		for i in range(4):
			var at := start.lerp(end, 0.35 + i * 0.12)
			draw_line(at, at + Vector2((i % 2 * 2 - 1) * 16, -10), CORAL, 2.0, true)

func _draw_attacks() -> void:
	if attack_warning <= 0.0 and attack_active <= 0.0:
		return
	var fill := Color(0.99, 0.69, 0.25, 0.18) if attack_active <= 0.0 else Color(0.95, 0.85, 0.38, 0.66)
	var canvas_h := _canvas_height()
	var rectangle := Rect2(attack_x - attack_width * 0.5, 244, attack_width, canvas_h - 244)
	draw_rect(rectangle, fill)
	draw_line(rectangle.position, Vector2(rectangle.position.x, canvas_h), GOLD, 2.5, true)
	draw_line(Vector2(rectangle.end.x, 244), Vector2(rectangle.end.x, canvas_h), GOLD, 2.5, true)
	for i in range(ceili((canvas_h - 244.0) / 42.0)):
		var y := 250.0 + i * 42.0
		draw_line(Vector2(rectangle.position.x + 3, y + 26), Vector2(rectangle.end.x - 3, y), Color(GOLD, 0.65), 2.0, true)
	_circle(Vector2(attack_x, _world_y(650)), 27.0, GOLD, INK, 3.0)
	_text("!", Vector2(attack_x - 20, _world_y(650) + 12), 35, INK, 40, HORIZONTAL_ALIGNMENT_CENTER, true)
	if attack_active > 0.0:
		var bolt := PackedVector2Array()
		for i in range(ceili((canvas_h - 244.0) / 65.0) + 1):
			bolt.append(Vector2(attack_x + sin(i * 4.3 + elapsed * 35.0) * 20.0, 250 + i * 65))
		draw_polyline(bolt, CREAM, 8.0, true)

func _draw_object(object: Dictionary) -> void:
	var at := Vector2(float(object.x), _world_y(float(object.y)))
	match str(object.kind):
		"salvage":
			at.y += 0.0 if reduced_motion else sin(elapsed * 2.4 + at.x) * 3.0
			for ring in range(4):
				draw_circle(at, 29.0 + ring * 8.0, Color(GOLD, 0.028 - ring * 0.005))
			if textures.has("gear"):
				draw_texture_rect(textures.gear, Rect2(at - Vector2(24, 24), Vector2(48, 48)), false)
			else:
				_circle(at, 16, GOLD, INK, 3)
				_circle(at, 5, INK, INK, 0)
		"rock":
			var radius := float(object.get("radius", 45.0))
			if textures.has("rock"):
				draw_texture_rect(textures.rock, Rect2(at - Vector2(radius, radius) + Vector2(5, 9), Vector2(radius * 2, radius * 2)), false, Color(0.01, 0.06, 0.10, 0.28))
				draw_texture_rect(textures.rock, Rect2(at - Vector2(radius, radius), Vector2(radius * 2, radius * 2)), false)
			else:
				var points := PackedVector2Array()
				for i in range(8):
					var angle := i * TAU / 7.0
					points.append(at + Vector2(cos(angle), sin(angle)) * radius * (0.9 + sin(i * 3) * 0.1))
				draw_colored_polygon(points, Color("597d7d"))
				draw_polyline(points, INK, 4.0, true)
		"boost":
			_circle(at, 36.0, Color("6dcbb2"), INK, 4.0)
			for i in range(2):
				var y := at.y + i * 17.0 - 12.0
				draw_polyline(PackedVector2Array([Vector2(at.x - 13, y + 7), Vector2(at.x, y - 6), Vector2(at.x + 13, y + 7)]), CREAM, 6.0, true)
			_text("BOOST", at + Vector2(-60, 63), 19, MINT, 120, HORIZONTAL_ALIGNMENT_CENTER)
		"portal":
			for ring in range(4):
				draw_circle(at, 50.0 + ring * 14, Color(0.27, 0.77, 0.96, 0.045 - ring * 0.008))
			if textures.has("portal"):
				draw_texture_rect(textures.portal, Rect2(at - Vector2(64, 82), Vector2(128, 164)), false)
			else:
				for i in range(4):
					draw_arc(at, 22 + i * 9, elapsed + i, elapsed + i + 5.0, 32, MINT, 5.0, true)
			_text("BONUS CURRENT", at + Vector2(-102, 94), 18, MINT, 204, HORIZONTAL_ALIGNMENT_CENTER)

func _draw_creature() -> void:
	var restless := phase == "aim" and aim_left < 3.0
	var y := _world_y(382.0) + sin(elapsed * (11.0 if restless else 2.3)) * (4.0 if restless else 9.0)
	if phase == "exit":
		y -= (3.0 - exit_left) * 210.0
	var name := "creature_" + species
	if textures.has(name):
		_draw_rotated_texture(textures[name], Vector2(creature_x, y + 12), Vector2(216, 140), 0.0, Color(0.0, 0.08, 0.12, 0.16))
		_draw_rotated_texture(textures[name], Vector2(creature_x, y), Vector2(210, 136), 0.0 if reduced_motion else sin(elapsed * (8.0 if restless else 2.2)) * 0.035)
	else:
		_circle(Vector2(creature_x, y), 48.0, CORAL, INK, 4.0)
		_circle(Vector2(creature_x + 18, y - 10), 9.0, CREAM, INK, 2.0)
		_circle(Vector2(creature_x + 19, y - 10), 4.0, INK, INK, 0)
	for i in range(3 if not restless else 9):
		var x := creature_x - 87.0 + sin(i * 7.3) * 30
		var by := y - fmod(elapsed * (48.0 if restless else 22.0) + i * 22.0, 95.0)
		draw_arc(Vector2(x, by), 3.0 + i % 3, 0.0, TAU, 12, Color(MINT, 0.45), 2.0, true)

func _draw_ship() -> void:
	var bob := 0.0 if reduced_motion else sin(elapsed * 3.0) * 3.0
	var at := Vector2(ship_x, _world_y(SHIP_Y) + bob)
	for ring in range(5):
		draw_circle(at + Vector2(0, -95), 7.0 + ring * 6.0, Color(1.0, 0.86, 0.45, 0.048 - ring * 0.008))
	for i in range(0 if reduced_motion else 5):
		var y := _world_y(SHIP_Y) + 86.0 + fmod(elapsed * 85 + i * 29.0, 148.0)
		var x := ship_x + sin(i * 2.0 + elapsed * 3) * (7.0 + i * 3)
		draw_arc(Vector2(x, y), 3.0 + i * 1.3, 0, TAU, 12, Color(MINT, 0.25), 2.0, true)
	if boost > 0.0 or bonus_ride > 0.0:
		draw_arc(at, 99.0 + sin(elapsed * 8) * 3, 0, TAU, 48, Color(MINT, 0.6), 5, true)
	var visible_ship := invulnerable <= 0.0 or int(elapsed * 13.0) % 2 == 0
	if visible_ship:
		if textures.has("submarine"):
			var tilt := 0.0 if reduced_motion else sin(elapsed * 1.45) * 0.012
			_draw_rotated_texture(textures.submarine, at + Vector2(5, 12), Vector2(130, 196), tilt, Color(0.0, 0.07, 0.11, 0.20))
			_draw_rotated_texture(textures.submarine, at, Vector2(130, 196), tilt)
		else:
			_panel(Rect2(at - Vector2(42, 73), Vector2(84, 146)), GOLD, INK, 36)
			_circle(at + Vector2(0, -22), 25, Color("8dc9c3"), INK, 5)
			_line(at + Vector2(-48, 39), at + Vector2(48, 39), INK, 13)
		if int(equipment.get("hull", 0)) >= 2:
			_panel(Rect2(at + Vector2(-40, 30), Vector2(80, 16)), Color("ca9b40"), INK, 5)
			if int(equipment.get("hull", 0)) >= 4:
				for side in [-1, 1]:
					_panel(Rect2(at + Vector2(side * 31 - 7, -10), Vector2(14, 55)), Color("bdc9bd"), INK, 5, 2)
		if int(equipment.get("harpoon", 0)) >= 2:
			draw_line(at + Vector2(19, -53), at + Vector2(19, -86), INK, 9, true)
			draw_line(at + Vector2(19, -53), at + Vector2(19, -86), Color("d5ddd2"), 4, true)
			if int(equipment.get("harpoon", 0)) >= 4:
				draw_line(at + Vector2(-19, -53), at + Vector2(-19, -86), INK, 9, true)
				draw_line(at + Vector2(-19, -53), at + Vector2(-19, -86), Color("d5ddd2"), 4, true)
		if int(equipment.get("collector", 0)) >= 2:
			for side in [-1, 1]:
				_circle(at + Vector2(side * 49, 5), 8, MINT, INK, 3)
				if int(equipment.get("collector", 0)) >= 4:
					var angle: float = -PI * 0.5 if side == 1 else PI * 0.5
					draw_arc(at + Vector2(side * 44, 5), 10, angle, angle + PI, 10, GOLD, 3, true)

func _draw_hud() -> void:
	_panel(Rect2(28, 44, 229, 78), CREAM, INK, 20)
	if textures.has("submarine"):
		draw_texture_rect(textures.submarine, Rect2(42, 54, 38, 58), false)
	else:
		_panel(Rect2(49, 58, 28, 48), GOLD, INK, 12)
	_text("HULL", Vector2(93, 73), 16, Color("657771"))
	_panel(Rect2(91, 84, 144, 17), Color("d7d8ba"), INK, 7, 2)
	var hull_color := MINT if hull / max_hull > 0.3 else CORAL
	if hull / max_hull <= 0.3:
		hull_color = hull_color.lightened((sin(ui_clock * 4) + 1.0) * 0.12)
	_panel(Rect2(94, 87, 138 * clampf(hull / max_hull, 0, 1), 11), hull_color, Color.TRANSPARENT, 4, 0)
	_panel(Rect2(313, 44, 178, 78), CREAM, INK, 20)
	if textures.has("gear"):
		draw_texture_rect(textures.gear, Rect2(305, 52, 60, 60), false)
	else:
		_circle(Vector2(340, 84), 18, GOLD, INK, 3)
	_text(str(pickups), Vector2(376, 98), 37, INK, 100, HORIZONTAL_ALIGNMENT_LEFT, true)
	_panel(Rect2(608, 44, 76, 78), CREAM, INK, 20)
	for x in [627, 647]:
		draw_line(Vector2(x, 69), Vector2(x, 100), INK, 7, true)
	if phase in ["aim", "pursuit"]:
		_panel(Rect2(70, 150, 580, 83), CREAM, INK, 22)
		_text(str(CREATURE_NAMES[species]), Vector2(88, 179), 23, INK, 544, HORIZONTAL_ALIGNMENT_CENTER, true)
		_panel(Rect2(93, 195, 534, 15), Color("dcd9bd"), INK, 6, 2)
		_panel(Rect2(96, 198, 528 * resistance / 100.0, 9), CORAL, Color.TRANSPARENT, 4, 0)
	elif phase == "travel":
		var fraction := travel / travel_duration
		for i in range(12):
			var x := 272 + i * 16
			draw_circle(Vector2(x, 155), 3.0, Color(MINT, 0.7 if i / 12.0 < fraction else 0.18))

func _draw_harpoon() -> void:
	var at := _harpoon_position()
	_circle(at + Vector2(0, 6), 76, Color("0a2634"), Color.TRANSPARENT, 0)
	_circle(at, 74, GOLD if shot_cooldown <= 0.0 else Color("708a80"), INK, 5)
	var completion := 1.0 - shot_cooldown / cooldown_duration
	draw_arc(at, 65, -PI / 2, -PI / 2 + maxf(0.01, completion) * TAU, 48, CREAM, 5, true)
	draw_line(at + Vector2(0, 27), at + Vector2(0, -29), INK, 6, true)
	draw_polyline(PackedVector2Array([at + Vector2(-19, -8), at + Vector2(0, -29), at + Vector2(19, -8)]), INK, 6, true)
	draw_line(at + Vector2(-12, 23), at + Vector2(12, 23), INK, 5, true)
	_text("TAP TO FIRE", at + Vector2(-110, -92), 19, CREAM, 220, HORIZONTAL_ALIGNMENT_CENTER)

func _draw_pause() -> void:
	draw_rect(Rect2(0, 0, W, _canvas_height()), Color(0.04, 0.11, 0.15, 0.72))
	_set_canvas_transform(Vector2(0, _middle_offset()))
	if confirm_return:
		_panel(Rect2(91, 383, 538, 542), CREAM, INK, 34)
		_text("Head back?", Vector2(112, 455), 42, INK, 496, HORIZONTAL_ALIGNMENT_CENTER, true)
		_center_lines(["Your %d salvage comes with you." % pickups, "The completion bonus stays behind.", "An unfinished catch earns no recipe."], 520, 27, INK, 43)
		_button(Rect2(142, 718, 436, 76), "Return early", CORAL)
		_button(Rect2(142, 816, 436, 70), "Keep exploring", Color("e3dfc7"))
	else:
		_panel(Rect2(91, 388, 538, 519), CREAM, INK, 34)
		_text("Taking a breather", Vector2(112, 461), 38, INK, 496, HORIZONTAL_ALIGNMENT_CENTER, true)
		_text("PAUSED", Vector2(120, 506), 20, Color("648077"), 480, HORIZONTAL_ALIGNMENT_CENTER)
		_center_lines(["Your dive is safe right here.", "Return early to keep your salvage", "without the completion bonus."], 558, 25, INK, 37)
		_button(Rect2(142, 692, 436, 82), "Resume dive", GOLD)
		_button(Rect2(142, 794, 436, 70), "Return early", Color("e3dfc7"))
	_set_canvas_transform()

func _draw_lesson() -> void:
	draw_rect(Rect2(0, 0, W, _canvas_height()), Color(0.04, 0.11, 0.15, 0.60))
	_set_canvas_transform(Vector2(0, _middle_offset()))
	_panel(Rect2(91, 402, 538, 465), CREAM, INK, 34)
	var title := "A little sea lesson"
	var lines: Array = ["Touch and drag sideways to steer.", "Follow the golden salvage trail.", "Your first dive is a safe practice run."]
	var action := "Let's explore"
	if lesson == "shoot":
		title = "Meet your first catch"
		lines = ["Steer directly beneath the creature.", "Tap the harpoon at the lower right.", "A miss is okay. Line up and try again."]
		action = "Ready to aim"
	elif lesson == "follow":
		title = "Hook, line & dinner"
		lines = ["Stay inside the glowing strip.", "The resistance bar will gently drain.", "Dodge amber warnings as you follow."]
		action = "Let's reel it in"
	_text("FIELD NOTES 0%d" % lesson_step, Vector2(115, 455), 19, Color("648077"), 490, HORIZONTAL_ALIGNMENT_CENTER)
	_text(title, Vector2(108, 518), 35, INK, 504, HORIZONTAL_ALIGNMENT_CENTER, true)
	_center_lines(lines, 584, 24, INK, 45)
	_button(Rect2(142, 745, 436, 78), action, GOLD)
	_set_canvas_transform()

func _panel(rect: Rect2, fill: Color, outline: Color, radius: int, border: int = 3) -> void:
	if rect.size.x <= 0:
		return
	if textures.has("expedition_card") and fill.a > 0.98 and border > 0 and rect.size.y >= 40.0:
		_draw_paper_panel(rect, fill)
		return
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = outline
	style.set_border_width_all(border)
	style.set_corner_radius_all(radius)
	style.anti_aliasing = true
	draw_style_box(style, rect)

func _draw_paper_panel(rect: Rect2, fill: Color) -> void:
	# Nine slices retain the illustrator's irregular ink border and paper grain
	# at phone-sized HUD dimensions and at large pause-card dimensions alike.
	var region := paper_region
	var source_corner := minf(112.0, region.size.y * 0.28)
	var corner := minf(28.0, rect.size.y * 0.30)
	var source_x := [region.position.x, region.position.x + source_corner, region.end.x - source_corner, region.end.x]
	var source_y := [region.position.y, region.position.y + source_corner, region.end.y - source_corner, region.end.y]
	var dest_x := [rect.position.x, rect.position.x + corner, rect.end.x - corner, rect.end.x]
	var dest_y := [rect.position.y, rect.position.y + corner, rect.end.y - corner, rect.end.y]
	var tint := Color(minf(1.0, fill.r / CREAM.r), minf(1.0, fill.g / CREAM.g), minf(1.0, fill.b / CREAM.b), fill.a)
	for y in range(3):
		for x in range(3):
			var source_rect := Rect2(float(source_x[x]), float(source_y[y]), float(source_x[x + 1]) - float(source_x[x]), float(source_y[y + 1]) - float(source_y[y]))
			var dest_rect := Rect2(float(dest_x[x]), float(dest_y[y]), float(dest_x[x + 1]) - float(dest_x[x]), float(dest_y[y + 1]) - float(dest_y[y]))
			draw_texture_rect_region(textures.expedition_card, dest_rect, source_rect, tint)

func _circle(at: Vector2, radius: float, fill: Color, outline: Color, width: float) -> void:
	if textures.has("expedition_card") and radius >= 50.0 and fill.a > 0.98:
		var points := PackedVector2Array()
		var uv := PackedVector2Array()
		var colors := PackedColorArray()
		var tint := Color(minf(1.0, fill.r / CREAM.r), minf(1.0, fill.g / CREAM.g), minf(1.0, fill.b / CREAM.b), fill.a)
		for i in range(64):
			var angle := i * TAU / 64.0
			var direction := Vector2(cos(angle), sin(angle))
			points.append(at + direction * (radius + sin(i * 1.7) * 0.35))
			uv.append(Vector2(887, 445) / Vector2(1774, 887) + direction * Vector2(0.20, 0.15))
			colors.append(tint)
		draw_polygon(points, colors, uv, textures.expedition_card)
	else:
		draw_circle(at, radius, fill)
	if width > 0:
		draw_arc(at, radius, 0, TAU, 48, outline, width, true)

func _line(from: Vector2, to: Vector2, color: Color, width: float) -> void:
	draw_line(from, to, color, width, true)

func _text(value: String, at: Vector2, font_size: int, color: Color = INK, width: float = -1, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, heading: bool = false) -> void:
	draw_string(display_font if heading else font, at, value, align, width, font_size, color)

func _center_lines(lines: Array, y: float, font_size: int, color: Color, line_height: float) -> void:
	for i in range(lines.size()):
		_text(str(lines[i]), Vector2(110, y + i * line_height), font_size, color, 500, HORIZONTAL_ALIGNMENT_CENTER)

func _button(rect: Rect2, label: String, fill: Color) -> void:
	_panel(Rect2(rect.position + Vector2(0, 4), rect.size), INK, INK, 21)
	_panel(rect, fill, INK, 21)
	_text(label, rect.position + Vector2(9, rect.size.y * 0.5 + 10), 29, INK, rect.size.x - 18, HORIZONTAL_ALIGNMENT_CENTER, true)
