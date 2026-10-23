extends Control
## Shared scene/gallery renderer for the approved Faceted #33 asset library.
## Ground cells are square; every full sprite uses its authored 128px root/pitch.

const ArtBook = preload("res://scripts/art_book.gd")
const Typography = preload("res://scripts/typography.gd")
const INK := Color("253b3b")
const NIGHT := Color("103d4b")
const PAPER := Color("ffefcf")
const DIRECTIONS := {"north": Vector2.UP, "south": Vector2.DOWN, "east": Vector2.RIGHT, "west": Vector2.LEFT}
const BELT_FACING := {"east": "S", "north": "E", "west": "N", "south": "W"}
const FACING := {"north": "N", "east": "E", "south": "S", "west": "W"}
const CUSTOMERS := ["customer-rosa", "customer-ellis", "customer-samir", "customer-june"]
const BUBBLE_ATTACHMENT := Vector2(0, -172) # Fixed C125 head clearance, logical pixels.
const INACTIVE_TINT := Color(0.56, 0.62, 0.65, 0.82)
const DISHES := {"salmon_nigiri": "dish-salmon", "cucumber_maki": "dish-cucumber", "eel_nigiri": "dish-eel"}
var native_composition_enabled := true
var _native_world_clone := false
# Native pixels per source Control pixel, for fixed editor-marker sizes.
var _native_screen_pixel_scale := 1.0
var _native_world_layer: Node
var _native_world_controller: Node
var art = ArtBook.new()
var state: Dictionary = {}
var portrait := Rect2()
var floor_origin := Vector2.ZERO
var safe_top := 0.0
var sky_height := 0.0
var sky_texture: Texture2D
var cell := 76.0
var show_gallery := false
var time := 0.0
var sale_pops: Array = []
var reduced_motion := false
var editor_preview: Dictionary = {}
var editor_selection_alpha := 1.0
var font: Font
var heading: Font
var _hit_records: Array[Dictionary] = []
var _hit_signature: Array = []
var _capture_hits := false
var _record_only := false
var _current_owner := ""

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	font = Typography.body()
	heading = Typography.heading()
	sky_texture = load("res://assets/ui/night-sky.png")
	if not _native_world_clone:
		art.reload()
	if native_composition_enabled:
		var helper_path: String = get_script().resource_path.get_base_dir().path_join("native_world_layer.gd")
		_native_world_layer = load(helper_path).new()
		add_child(_native_world_layer)
		_native_world_layer.initialize(self)

func _process(_delta: float) -> void:
	if native_composition_enabled and _native_world_layer != null:
		_native_world_layer.sync()

func update_layout() -> void:
	var width := minf(size.x, size.y * 9.0 / 16.0)
	portrait = Rect2((size.x - width) * 0.5, 0, width, size.y)
	var floor_data: Dictionary = state.get("floor", {})
	cell = width / float(floor_data.get("viewport_columns", floor_data.get("columns", 7)))
	# Full-width scenery begins below a quiet, fixed camera-clearance strip.
	var unit := width / 720.0
	sky_height = 0.0 if show_gallery else maxf(80.0 * unit, safe_top + 12.0 * unit)
	floor_origin = portrait.position + Vector2(0, sky_height)
	queue_redraw()

func hud_area() -> Rect2:
	return Rect2(portrait.position + Vector2(0, sky_height), portrait.size - Vector2(0, sky_height))

func _sky() -> void:
	if sky_height <= 0.0 or sky_texture == null: return
	var target := Rect2(portrait.position, Vector2(portrait.size.x, sky_height))
	# Crop the opaque generated sky uniformly; never flatten its stars/facets.
	var dimensions := sky_texture.get_size()
	var scale_value := maxf(target.size.x / dimensions.x, target.size.y / dimensions.y)
	var source_size := target.size / scale_value
	draw_texture_rect_region(sky_texture, target, Rect2((dimensions - source_size) * 0.5, source_size))

func cell_base(x: float, y: float) -> Vector2:
	var camera: Dictionary = state.get("camera", {"x": 0.0, "y": 0.0})
	return floor_origin + Vector2(x + 0.5 - float(camera.x), y + 0.5 - float(camera.y)) * cell

func sprite(identity: String, base: Vector2, clip := "static", direction := "S", seconds := 0.0, tile_pixels := -1.0, tint := Color.WHITE) -> void:
	var pitch := cell if tile_pixels < 0.0 else tile_pixels
	var data: Dictionary = art.frame_data(identity, clip, direction, seconds)
	if not data.is_empty():
		var destination: Rect2 = art.registered_rect(identity, base, pitch, clip, direction)
		if _capture_hits:
			_hit_records.append({"owner_id": _current_owner, "art_id": identity, "clip": clip, "direction": direction, "frame": data.frame, "frames": data.frames, "texture": data.texture, "source_path": data.source_path, "region": data.region, "rect": destination, "tint": tint})
		if not _record_only:
			var draw_texture: Texture2D = data.texture
			if _native_world_clone:
				draw_texture = _native_world_controller.native_sprite_texture(identity, draw_texture)
			draw_texture_rect_region(draw_texture, destination, data.region, tint, false)

func caption(text: String, at: Vector2, pixels: int = 30, color := INK, use_heading := false) -> void:
	draw_string(heading if use_heading else font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, maxi(1, pixels), color)

func _draw() -> void:
	if font == null:
		return
	if native_composition_enabled and not show_gallery and _native_world_layer != null:
		# Visuals use the identical world pass in the native viewport. Picking
		# remains the original pass at actual screen-space roots and rectangles.
		draw_rect(Rect2(Vector2.ZERO, size), NIGHT)
		_hit_records.clear()
		_hit_signature.clear()
		_record_only = true
		_render_room_items()
		_record_only = false
		return
	if _native_world_clone:
		_native_world_controller.begin_native_frame()
	art.begin_frame()
	_hit_records.clear()
	_hit_signature.clear()
	draw_rect(Rect2(Vector2.ZERO, size), NIGHT)
	if show_gallery:
		_gallery()
	else:
		_room()
		_sky()
	art.end_frame()
	if _native_world_clone:
		_native_world_controller.end_native_frame()

func _room() -> void:
	if state.is_empty():
		return
	draw_rect(portrait, Color("e9cda3"))
	var camera: Dictionary = state.camera
	var rows := int(state.floor.rows)
	var columns := int(state.floor.world_columns)
	# One continuous authored floor extends into the adjoining restaurant. Tile
	# borders are part of the approved native art, not a realistic floor texture.
	for y in range(int(state.floor.get("backdrop_rows", 3)), rows + 6):
		for x in range(columns):
			var base := cell_base(x, y)
			if not portrait.intersects(Rect2(base - Vector2.ONE * cell * 0.5, Vector2.ONE * cell)):
				continue
			var tint := Color.WHITE if x < int(state.floor.columns) else Color("b2aaa0")
			var identity := "floor-blue-wave" if y == rows - 1 else "floor-cream"
			sprite(identity, base, "static", "S", 0.0, -1.0, tint)
	for piece in backdrop_plan():
		sprite(piece.key, piece.base)
	_editor_ground()
	_render_room_items()
	_editor_ghost()
	# Thought/reaction art is a final feedback layer, following the same saved
	# visual offset as its customer while remaining readable above furniture.
	for customer in state.get("customers", []):
		_feedback_at(customer, cell_base(float(customer.x), float(customer.y)), cell)
	for pop in sale_pops:
		var age := time - float(pop.time)
		if age >= 0.0 and age < 0.9:
			# Native pop frames already rise above this registered customer root.
			# Keep its authored scale/motion and the existing quiet alpha fade.
			sprite("coin-pop", cell_base(float(pop.x), float(pop.y)), "pop", "S", 0.0 if reduced_motion else age, -1.0, Color(1, 1, 1, 1.0 - age / 0.9))

func _render_room_items() -> void:
	# Rendering and picking share this exact pass, including sprite frame,
	# attachment geometry and painter order. Other decorative/editor layers
	# never enter its ownership records.
	_hit_records.clear()
	_capture_hits = true
	for item in render_plan():
		_current_owner = str(item.get("owner_id", ""))
		if item.kind in ["belt", "dish", "chef", "seat", "board"]:
			_current_owner = str(item.value.get("id", ""))
		match item.kind:
			"belt": _belt(item.value)
			"dish": _dish(item.value)
			"sprite": sprite(item.key, item.base, item.get("clip", "static"), item.get("direction", "S"), 0.0 if reduced_motion else float(state.elapsed))
			"chef": _chef(item.value)
			"seat": _seat_at(item.value, cell_base(float(item.value.x), float(item.value.y)), cell)
			"board": _board(item.value)
			"customer": _customer(item.value)
	_capture_hits = false
	_current_owner = ""
	_hit_signature = _geometry_signature()

func _geometry_signature() -> Array:
	return [state.hash(), portrait, floor_origin, cell, size, reduced_motion, show_gallery, time, art.revision]

func _ensure_sprite_hits() -> void:
	if _hit_signature == _geometry_signature(): return
	if show_gallery or state.is_empty():
		_hit_records.clear()
		_hit_signature = _geometry_signature()
		return
	# Headless tests do not receive CanvasItem._draw. Input can also arrive
	# after camera/layout/state changed but before the next rendered frame.
	# Resolve the same item pass without invoking any drawing primitives.
	_record_only = true
	_render_room_items()
	_record_only = false

func sprite_hits() -> Array[Dictionary]:
	_ensure_sprite_hits()
	return _hit_records.duplicate(true)

func object_at(point: Vector2) -> Dictionary:
	if show_gallery or not hud_area().has_point(point) or not Rect2(Vector2.ZERO, size).has_point(point): return {}
	_ensure_sprite_hits()
	for index in range(_hit_records.size() - 1, -1, -1):
		var item: Dictionary = _hit_records[index]
		var bounds: Rect2 = item.rect
		if not bounds.has_area() or not bounds.has_point(point) or float(item.tint.a) <= ArtBook.PICK_ALPHA: continue
		var uv := (point - bounds.position) / bounds.size
		var source: Rect2 = item.region
		if not art.frame_has_ink(item, source.position + uv * source.size): continue
		# An opaque guest or fixed room prop blocks furniture behind it. Only
		# sprites explicitly registered to an owned object can select that object.
		var identity := str(item.owner_id)
		if identity.is_empty(): return {}
		for object in state.get("objects", []):
			if str(object.get("id", "")) == identity: return object
		return {}
	return {}

func _editor_ground() -> void:
	if state.get("mode", "live") != "edit": return
	var identity := str(state.get("editor", {}).get("selected_id", ""))
	for object in state.get("objects", []):
		if str(object.id) != identity: continue
		var rect := Rect2(cell_base(float(object.x), float(object.y)) - Vector2.ONE * cell * 0.5, Vector2.ONE * cell)
		draw_rect(rect, Color(Color("bfd4af"), 0.48 * editor_selection_alpha))
		# The approved B marker keeps the tile readable under the object: pale
		# sage fill and four navy brackets, with open edges between the corners.
		var inset := rect.grow(-2.0 * _native_screen_pixel_scale)
		var arm := cell * 0.20
		var thickness := maxf(2.0 * _native_screen_pixel_scale, cell * 0.04)
		for corner in [Vector2.ZERO, Vector2.RIGHT, Vector2.ONE, Vector2.DOWN]:
			var point: Vector2 = inset.position + inset.size * corner
			var across := Vector2(-1.0 if corner.x > 0.0 else 1.0, 0.0) * arm
			var down := Vector2(0.0, -1.0 if corner.y > 0.0 else 1.0) * arm
			draw_polyline(PackedVector2Array([point + across, point, point + down]), Color(Color("233d58"), editor_selection_alpha), thickness, true)

func _editor_ghost() -> void:
	if state.get("mode", "live") != "edit" or editor_preview.is_empty(): return
	var base := cell_base(float(editor_preview.x), float(editor_preview.y))
	var color := Color("66b87a") if editor_preview.get("valid", false) else Color("ce6254")
	var footprint := Rect2(base - Vector2.ONE * cell * 0.5, Vector2.ONE * cell)
	draw_rect(footprint, Color(color, 0.32))
	draw_rect(footprint.grow(-1.5 * _native_screen_pixel_scale), color, false, 3.0 * _native_screen_pixel_scale, true)
	var object: Dictionary = editor_preview.get("source", {})
	var identity := str(object.get("art_id", ""))
	var clip := "static"
	if object.get("kind") == "chef": clip = "idle"
	elif object.get("kind") == "belt":
		identity = "belt-straight-e"
		clip = "running"
	elif object.get("kind") == "seat": identity = "stool-wood"
	elif identity == "plant-angular": clip = "idle"
	if not identity.is_empty(): sprite(identity, base, clip, belt_direction(object) if object.get("kind") == "belt" else str(FACING.get(object.get("facing", "south"), "S")), 0.0, -1.0, Color(1, 1, 1, 0.65))

func render_plan() -> Array:
	# Sort by ground depth, never by image height. All connected deck modules
	# at the same depth precede every plate, preventing neighboring rail overlap.
	var result := _decor_plan()
	for object in state.get("objects", []):
		match object.kind:
			"belt":
				result.append({"kind": "belt", "value": object, "depth": float(object.y), "priority": 1})
				if object.get("dish") != null:
					result.append({"kind": "dish", "value": object, "depth": float(object.y), "priority": 3})
			"seat":
				result.append({"kind": "seat", "value": object, "depth": float(object.y), "priority": 0})
			"decor":
				var prop := _prop(str(object.get("art_id", "plant-angular")), float(object.x), float(object.y), "idle" if object.get("art_id") == "plant-angular" else "static", str(FACING.get(object.get("facing", "south"), "S")))
				prop["owner_id"] = str(object.get("id", ""))
				result.append(prop)
			"chef":
				result.append({"kind": "chef", "value": object, "depth": float(object.y), "priority": 2})
				result.append({"kind": "board", "value": object, "depth": float(object.y) + 0.4, "priority": 4})
	for customer in state.get("customers", []):
		result.append({"kind": "customer", "value": customer, "depth": float(customer.y) + float(customer.get("render_offset_y", 0)), "priority": 2})
	result.sort_custom(func(a: Dictionary, b: Dictionary):
		if not is_equal_approx(float(a.depth), float(b.depth)):
			return float(a.depth) < float(b.depth)
		return int(a.get("priority", 0)) < int(b.get("priority", 0)))
	return result

func _prop(key: String, x: float, y: float, clip := "static", direction := "S") -> Dictionary:
	return {"kind": "sprite", "key": key, "base": cell_base(x, y), "clip": clip, "direction": direction, "depth": y, "priority": 0}

func _decor_plan() -> Array:
	if state.is_empty():
		return []
	var rows := int(state.floor.rows)
	var columns := int(state.floor.world_columns)
	var result: Array = []
	for y in range(3, rows - 1):
		result.append(_prop("wall-middle", -0.5, float(y), "static", "E"))
	result.append(_prop("barrel-wood", 0.0, float(rows) - 1.0))
	result.append(_prop("plant-angular", float(columns) - 1.0, float(rows) - 1.0, "idle"))
	for x in range(1, columns, 5):
		result.append(_prop("crate-wood", float(x), float(rows) - 1.0))
	# Adjoining space stays visibly present but unavailable in the starter. These
	# are complete approved garbage assemblies, not repeated decoration patches.
	for pile in [["garbage-sofa", 9.5, 5.5], ["garbage-shelving", 13.5, 8.5], ["garbage-car", 18.0, 5.5]]:
		result.append(_prop(str(pile[0]), float(pile[1]), float(pile[2]), "idle"))
	return result

func backdrop_plan() -> Array:
	# Backdrop coordinates are projected tile edges, independent of the guest's
	# arrival cell. The registered baseline is exactly the bottom of row three.
	var result: Array = []
	if state.is_empty(): return result
	var x := 0
	while x < int(state.floor.world_columns):
		var gate := x == 3
		var width := 4 if gate else 1
		result.append({"key": "backdrop-entrance" if gate else "backdrop-wall", "x": x, "width": width, "base": cell_base(float(x) + float(width) / 2.0 - 0.5, 2.5)})
		x += width
	return result

func _has_belt(at: Vector2) -> bool:
	for object in state.get("objects", []):
		if object.kind == "belt" and Vector2(float(object.x), float(object.y)).is_equal_approx(at):
			return true
	return false

func belt_clip(belt: Dictionary) -> String:
	var direction: Vector2 = DIRECTIONS.get(str(belt.facing), Vector2.RIGHT)
	var at := Vector2(float(belt.x), float(belt.y))
	if not _has_belt(at - direction):
		return "belt-start-e"
	if not _has_belt(at + direction):
		return "belt-end-e"
	return "belt-straight-e"

func belt_direction(belt: Dictionary) -> String:
	return str(BELT_FACING.get(str(belt.get("facing", "east")), "S"))

func _belt(belt: Dictionary) -> void:
	sprite(belt_clip(belt), cell_base(float(belt.x), float(belt.y)), "running", belt_direction(belt), 0.0 if reduced_motion else float(state.elapsed))

func dish_base(belt: Dictionary) -> Vector2:
	var direction: Vector2 = DIRECTIONS.get(str(belt.facing), Vector2.ZERO)
	var ahead := Vector2.ZERO
	for other in state.objects:
		if other.kind == "belt" and float(other.x) == float(belt.x) + direction.x and float(other.y) == float(belt.y) + direction.y:
			ahead = direction * cell * float(belt.travel_progress)
			break
	return cell_base(float(belt.x), float(belt.y)) + ahead + art.socket(belt_clip(belt), "deck", belt_direction(belt)) * cell / art.cell_size

func _dish(belt: Dictionary) -> void:
	sprite(str(DISHES.get(str(belt.dish.recipe_id), "dish-salmon")), dish_base(belt))

func activity_tint(object: Dictionary) -> Color:
	return Color.WHITE if object.get("active", true) else INACTIVE_TINT

func chef_clip(chef: Dictionary) -> String:
	if not chef.get("active", true):
		return "idle"
	var clip := str(chef.get("visual_phase", "hold" if chef.get("held_dish") != null else "work"))
	if chef.get("art_id", "chef-lena") == "chef-omar" and chef.get("recipe_id") == "cucumber_maki" and clip in ["hold", "load"]:
		return clip + "-cucumber"
	return clip

func _chef(chef: Dictionary) -> void:
	_chef_at(chef, cell_base(float(chef.x), float(chef.y)), cell)

func _chef_at(chef: Dictionary, base: Vector2, pitch: float) -> void:
	var clip := chef_clip(chef)
	var seconds := 0.0 if reduced_motion else float(chef.get("visual_elapsed", state.get("elapsed", time)))
	sprite(str(chef.get("art_id", "chef-lena")), base, clip, str(FACING.get(chef.get("facing", "south"), "S")), seconds, pitch, activity_tint(chef))
	if not _record_only and chef.get("held_dish") != null and not clip.begins_with("load") and chef.get("active", true):
		var center := base - Vector2(pitch * 0.42, pitch * 1.25)
		draw_circle(center, pitch * 0.10, PAPER)
		draw_arc(center, pitch * 0.10, 0, TAU, 24, INK, 1.4, true)
		draw_line(center, center - Vector2(0, pitch * 0.05), INK, 1.4, true)

func _seat_at(seat: Dictionary, base: Vector2, pitch: float) -> void:
	sprite("stool-wood", base, "static", str(FACING.get(seat.get("facing", "south"), "S")), 0.0, pitch, activity_tint(seat))

func _board(chef: Dictionary) -> void:
	_board_at(chef, cell_base(float(chef.x), float(chef.y)), cell)

func _board_at(chef: Dictionary, base: Vector2, pitch: float) -> void:
	# Front placement and blank face are modeled in the source. This fixture
	# stays in the chef's cell and always faces the player.
	var tint := activity_tint(chef)
	sprite("chef-blackboard", base, "idle", "S", 0.0, pitch, tint)
	var face: Vector2 = base + art.socket("chef-blackboard", "display_face") * pitch / art.cell_size
	sprite(str(DISHES.get(str(chef.get("recipe_id", "salmon_nigiri")), "dish-salmon")), face, "static", "S", 0.0, pitch * 0.28, tint)

func _customer(customer: Dictionary) -> void:
	_customer_at(customer, cell_base(float(customer.x), float(customer.y)), cell)

func customer_pose_offset(customer: Dictionary, pitch: float) -> Vector2:
	var result := Vector2(float(customer.get("render_offset_x", 0)), float(customer.get("render_offset_y", 0))) * pitch
	var happy := float(customer.get("happy_elapsed", 100.0))
	if not reduced_motion and customer.get("preference_phase") == "satisfied" and happy >= 0.0 and happy < 0.55:
		result.y -= sin(PI * happy / 0.55) * pitch * 0.14
	return result

func _customer_at(customer: Dictionary, base: Vector2, pitch: float) -> void:
	var identity: String = CUSTOMERS[posmod(int(customer.get("appearance", 0)), CUSTOMERS.size())]
	var direction := str(FACING.get(str(customer.get("facing", "south")), "S"))
	var seconds := 0.0 if reduced_motion else float(customer.get("visual_elapsed", state.get("elapsed", time)))
	# Sit/stand actions retain their native wood-stool support calibration.
	# Passing and brief happiness move only the visual instance, never its cell.
	sprite(identity, base + customer_pose_offset(customer, pitch), customer_clip(customer), direction, seconds, pitch)

func customer_clip(customer: Dictionary) -> String:
	var phase := str(customer.get("phase", "waiting"))
	var fallback := "stand" if phase == "entrance_wait" else "eat" if phase == "eating" else "seated-wait" if phase == "waiting" else "walk"
	var clip := str(customer.get("visual_phase", fallback))
	if customer.get("restless", false) and phase == "waiting" and clip in ["seated-wait", "seated-wait-empty", "restless"]:
		return "restless"
	if clip == "seated-wait":
		return "seated-wait-empty"
	if clip == "eat" and customer.get("meal_dish") is Dictionary and customer.meal_dish.get("recipe_id") == "salmon_nigiri":
		return "eat-salmon"
	return clip

func customer_feedback(customer: Dictionary) -> Dictionary:
	if customer.get("phase") == "entrance_wait":
		if reduced_motion: return {"object": "bubble-puzzled", "clip": "idle", "seconds": 0.0, "timer": -1.0}
		var waited := maxf(0.0, float(customer.get("entrance_wait_elapsed", 0.0)))
		var duration := maxf(1.0, float(customer.get("entrance_wait_total", 4.0)))
		var fading := waited >= duration - 1.0
		return {"object": "bubble-puzzled", "clip": "fade" if fading else "appear" if waited < 1.0 else "idle", "seconds": waited - (duration - 1.0) if fading else waited if waited < 1.0 else waited - 1.0, "timer": -1.0}
	if customer.get("navigation_mode") == "wander" and customer.get("phase") in ["walking", "leaving"]:
		if reduced_motion: return {"object": "bubble-panic", "clip": "idle", "seconds": 0.0, "timer": -1.0}
		var scared := maxf(0.0, float(customer.get("wander_elapsed", 0.0)))
		return {"object": "bubble-panic", "clip": "appear" if scared < 1.0 else "idle", "seconds": scared if scared < 1.0 else scared - 1.0, "timer": -1.0}
	var phase := str(customer.get("preference_phase", "pending"))
	var prefix := "cucumber-" if customer.get("preferred_recipe_id") == "cucumber_maki" else ""
	var age := maxf(0.0, float(customer.get("preference_phase_elapsed", float(customer.get("preference_total", 0)) - float(customer.get("preference_remaining", 0)))))
	if phase == "active":
		return {"object": "bubble-preference", "clip": prefix + ("appear" if age < 1.0 else "idle"), "seconds": age if age < 1.0 else age - 1.0, "timer": clampf(float(customer.get("preference_progress", 1)), 0, 1)}
	if phase == "expired" and age < 1.0:
		return {"object": "bubble-preference", "clip": prefix + "fade", "seconds": age, "timer": -1.0}
	if phase == "satisfied":
		var happy := maxf(0.0, float(customer.get("happy_elapsed", 0)))
		var duration := float(customer.get("happy_duration", 2.2))
		if happy >= duration:
			return {}
		var clip := "happy-smile-transition" if happy < 1.0 else "happy-smile-fade" if happy >= duration - 1.0 else "happy-smile-idle"
		return {"object": "bubble-happy", "clip": clip, "seconds": happy if happy < 1.0 else happy - (duration - 1.0) if clip == "happy-smile-fade" else happy - 1.0, "timer": -1.0}
	return {}

func _feedback_at(customer: Dictionary, base: Vector2, pitch: float) -> void:
	var feedback := customer_feedback(customer)
	if feedback.is_empty():
		return
	var bubble_base: Vector2 = base + customer_pose_offset(customer, pitch) + BUBBLE_ATTACHMENT * pitch / art.cell_size
	sprite(feedback.object, bubble_base, feedback.clip, "S", 0.0 if reduced_motion else float(feedback.seconds), pitch)
	if float(feedback.timer) >= 0.0:
		var center: Vector2 = bubble_base + Vector2(37, -84) * pitch / art.cell_size
		var radius := pitch * 0.115
		var stroke := maxf(1.4, pitch * 0.032)
		draw_circle(center, radius + stroke, Color("fff5dc"))
		draw_arc(center, radius, 0, TAU, 36, Color("c5ccbc"), stroke, true)
		var progress := float(feedback.timer)
		if progress > 0.001:
			draw_arc(center, radius, -PI * 0.5, -PI * 0.5 + TAU * progress, 36, Color("3c8d7b") if progress > 0.25 else Color("bf8147"), stroke, true)

func gallery_customers() -> Array:
	var base := {"id": "review-guest", "appearance": 0, "phase": "waiting", "visual_phase": "seated-wait", "visual_elapsed": time, "facing": "south", "meal_dish": null, "preference_phase": "pending", "preferred_recipe_id": "salmon_nigiri", "preference_total": 8.0, "preference_remaining": 8.0, "preference_progress": 1.0, "preference_phase_elapsed": 0.0, "restless": false}
	var result: Array = []
	for index in range(7):
		result.append(base.duplicate(true))
	result[1].merge({"preference_phase": "active", "preferred_recipe_id": "cucumber_maki", "preference_phase_elapsed": 2.0 + fmod(time, 6.0), "preference_progress": 0.75 - fmod(time, 6.0) / 8.0}, true)
	result[2].merge({"phase": "eating", "visual_phase": "eat", "meal_dish": {"recipe_id": "salmon_nigiri"}, "preference_phase": "satisfied", "happy_elapsed": fmod(time, 2.2), "happy_duration": 2.2}, true)
	result[3].merge({"preference_phase": "expired", "preference_phase_elapsed": fmod(time, 3.0)}, true)
	result[4].merge({"preference_phase": "expired", "preference_phase_elapsed": 5.0, "restless": true}, true)
	result[5].merge({"phase": "entrance_wait", "visual_phase": "stand", "seat_id": "", "entrance_wait_elapsed": fmod(time, 4.0), "entrance_wait_total": 4.0}, true)
	result[6].merge({"phase": "walking", "visual_phase": "walk", "navigation_mode": "wander", "wander_elapsed": time}, true)
	return result

func _gallery() -> void:
	var unit := portrait.size.x / 720.0
	var left := portrait.position.x + 36.0 * unit
	caption("Shared components", Vector2(left, 58 * unit), int(40 * unit), PAPER, true)
	caption("Customer visits · preferences and reactions", Vector2(left, 101 * unit), int(22 * unit), Color("a9d6d0"))
	var panel := Rect2(left, 240 * unit, portrait.size.x - 72 * unit, minf(940 * unit, portrait.size.y - 475 * unit))
	draw_style_box(_paper_style(), panel)
	var row_unit := panel.size.y / 940.0
	var pitch := minf(92 * unit, 92 * row_unit)
	caption("One guest, seven moments", panel.position + Vector2(24 * unit, 30 * row_unit), int(27 * unit), INK, true)
	var guests := gallery_customers()
	var labels := ["Waiting", "Preference", "Happy", "Expired", "Restless", "Entrance wait", "Trapped", "Inactive"]
	for index in range(8):
		var column := index % 3
		var row := index / 3
		var base := panel.position + Vector2((112 + column * 212) * unit, (260 + row * 280) * row_unit)
		if index < 7:
			_gallery_tile(base, pitch)
			if index < 5: _seat_at({"facing": "south", "active": true}, base, pitch)
			_customer_at(guests[index], base, pitch)
			_feedback_at(guests[index], base, pitch)
		else:
			var chef_base := base - Vector2(pitch * 0.5, 0)
			var seat_base := base + Vector2(pitch * 0.5, 0)
			_gallery_tile(chef_base, pitch)
			_gallery_tile(seat_base, pitch)
			var chef := {"art_id": "chef-lena", "recipe_id": "salmon_nigiri", "facing": "south", "active": false, "visual_phase": "idle", "visual_elapsed": time}
			_chef_at(chef, chef_base, pitch)
			_board_at(chef, chef_base, pitch)
			_seat_at({"facing": "south", "active": false}, seat_base, pitch)
		caption(labels[index], panel.position + Vector2((57 + column * 212) * unit, (330 + row * 280) * row_unit), int(25 * unit))
	var service_pitch := pitch * 0.4
	var start := panel.position + Vector2(468 * unit, 820 * row_unit)
	for index in range(4):
		var base := start + Vector2(float(index) * service_pitch, 0)
		_gallery_tile(base, service_pitch)
		var identity: String = ["belt-start-e", "belt-straight-e", "belt-straight-e", "belt-end-e"][index]
		sprite(identity, base, "running", "S", 0.0 if reduced_motion else time, service_pitch)
	for index in range(2):
		var progress := fmod((0.0 if reduced_motion else time * 0.7) + float(index) * 1.5, 3.0)
		var at: Vector2 = start + Vector2(progress * service_pitch, 0) + art.socket("belt-straight-e", "deck") * service_pitch / art.cell_size
		sprite("dish-salmon" if index == 0 else "dish-cucumber", at, "static", "S", 0.0, service_pitch)
	caption("Service", panel.position + Vector2(481 * unit, 890 * row_unit), int(25 * unit))

func _gallery_tile(base: Vector2, pitch: float) -> void:
	sprite("floor-cream", base, "static", "S", 0.0, pitch)

func _paper_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = PAPER
	style.border_color = Color("513d32")
	style.set_border_width_all(4)
	style.set_corner_radius_all(18)
	style.shadow_color = Color(0, 0, 0, 0.2)
	style.shadow_size = 10
	return style
