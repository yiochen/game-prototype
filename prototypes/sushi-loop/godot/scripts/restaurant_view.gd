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
var art = ArtBook.new()
var state: Dictionary = {}
var portrait := Rect2()
var floor_origin := Vector2.ZERO
var cell := 76.0
var show_gallery := false
var time := 0.0
var sale_pops: Array = []
var reduced_motion := false
var editor_preview: Dictionary = {}
var editor_selection_alpha := 1.0
var font: Font
var heading: Font

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	font = Typography.body()
	heading = Typography.heading()
	art.reload()

func update_layout() -> void:
	var width := minf(size.x, size.y * 9.0 / 16.0)
	portrait = Rect2((size.x - width) * 0.5, 0, width, size.y)
	var floor_data: Dictionary = state.get("floor", {})
	cell = (width - 48.0) / float(floor_data.get("viewport_columns", floor_data.get("columns", 7)))
	var floor_height := float(floor_data.get("rows", 13)) * cell
	floor_origin = Vector2(portrait.position.x + 24.0, maxf(24.0, (size.y - floor_height) * 0.5))
	queue_redraw()

func cell_base(x: float, y: float) -> Vector2:
	var camera: Dictionary = state.get("camera", {"x": 0.0, "y": 0.0})
	return floor_origin + Vector2(x + 0.5 - float(camera.x), y + 0.5 - float(camera.y)) * cell

func sprite(identity: String, base: Vector2, clip := "static", direction := "S", seconds := 0.0, tile_pixels := -1.0, tint := Color.WHITE) -> void:
	var pitch := cell if tile_pixels < 0.0 else tile_pixels
	var data: Dictionary = art.frame_data(identity, clip, direction, seconds)
	if not data.is_empty():
		draw_texture_rect_region(data.texture, art.registered_rect(identity, base, pitch, clip, direction), data.region, tint, false)

func caption(text: String, at: Vector2, pixels: int = 30, color := INK, use_heading := false) -> void:
	draw_string(heading if use_heading else font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, maxi(1, pixels), color)

func _draw() -> void:
	if font == null:
		return
	art.begin_frame()
	draw_rect(Rect2(Vector2.ZERO, size), NIGHT)
	if show_gallery:
		_gallery()
	else:
		_room()
	art.end_frame()

func _room() -> void:
	if state.is_empty():
		return
	draw_rect(portrait, Color("e9cda3"))
	var camera: Dictionary = state.camera
	var rows := int(state.floor.rows)
	var columns := int(state.floor.world_columns)
	# One continuous authored floor extends into the adjoining restaurant. Tile
	# borders are part of the approved native art, not a realistic floor texture.
	for y in range(-6, rows + 6):
		for x in range(columns):
			var base := cell_base(x, y)
			if not portrait.intersects(Rect2(base - Vector2.ONE * cell * 0.5, Vector2.ONE * cell)):
				continue
			var tint := Color.WHITE if x < int(state.floor.columns) else Color("b2aaa0")
			var identity := "floor-blue-wave" if y == 0 or y == rows - 1 else "floor-cream"
			sprite(identity, base, "static", "S", 0.0, -1.0, tint)
	_editor_ground()
	for item in render_plan():
		match item.kind:
			"belt":
				_belt(item.value)
			"dish":
				_dish(item.value)
			"sprite":
				sprite(item.key, item.base, item.get("clip", "static"), item.get("direction", "S"), 0.0 if reduced_motion else float(state.elapsed))
			"chef":
				_chef(item.value)
			"seat":
				_seat_at(item.value, cell_base(float(item.value.x), float(item.value.y)), cell)
			"board":
				_board(item.value)
			"customer":
				_customer(item.value)
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

func _editor_ground() -> void:
	if state.get("mode", "live") != "edit": return
	var identity := str(state.get("editor", {}).get("selected_id", ""))
	for object in state.get("objects", []):
		if str(object.id) != identity: continue
		var rect := Rect2(cell_base(float(object.x), float(object.y)) - Vector2.ONE * cell * 0.5, Vector2.ONE * cell)
		draw_rect(rect, Color(1.0, 0.79, 0.34, 0.30 * editor_selection_alpha))
		draw_rect(rect.grow(-1.5), Color(INK, editor_selection_alpha), false, 4.0, true)
		draw_rect(rect.grow(-3.0), Color(Color("ffcb62"), editor_selection_alpha), false, 2.0, true)

func _editor_ghost() -> void:
	if state.get("mode", "live") != "edit" or editor_preview.is_empty(): return
	var base := cell_base(float(editor_preview.x), float(editor_preview.y))
	var color := Color("66b87a") if editor_preview.get("valid", false) else Color("ce6254")
	var footprint := Rect2(base - Vector2.ONE * cell * 0.5, Vector2.ONE * cell)
	draw_rect(footprint, Color(color, 0.32))
	draw_rect(footprint.grow(-1.5), color, false, 3.0, true)
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
				result.append(_prop(str(object.get("art_id", "plant-angular")), float(object.x), float(object.y), "idle" if object.get("art_id") == "plant-angular" else "static", str(FACING.get(object.get("facing", "south"), "S"))))
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
	# The four-cell entrance retains its authored center and complete width.
	result.append(_prop("entry-finished", float(state.floor.entrance.x), float(state.floor.entrance.y)))
	for x in range(columns):
		result.append(_prop("wall-middle", float(x), -0.5))
	for y in range(1, rows - 1):
		result.append(_prop("wall-middle", -0.5, float(y), "static", "E"))
	result.append(_prop("plant-angular", 0.0, 0.0, "idle"))
	result.append(_prop("barrel-wood", 0.0, float(rows) - 1.0))
	result.append(_prop("plant-angular", float(columns) - 1.0, float(rows) - 1.0, "idle"))
	for x in range(1, columns, 5):
		result.append(_prop("lantern-gold", float(x), 0.0, "idle"))
		result.append(_prop("crate-wood", float(x), float(rows) - 1.0))
	# Adjoining space stays visibly present but unavailable in the starter. These
	# are complete approved garbage assemblies, not repeated decoration patches.
	for pile in [["garbage-sofa", 9.5, 5.5], ["garbage-shelving", 13.5, 8.5], ["garbage-car", 18.0, 5.5]]:
		result.append(_prop(str(pile[0]), float(pile[1]), float(pile[2]), "idle"))
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
	if chef.get("held_dish") != null and not clip.begins_with("load") and chef.get("active", true):
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
	var fallback := "eat" if phase == "eating" else "seated-wait" if phase == "waiting" else "walk"
	var clip := str(customer.get("visual_phase", fallback))
	if customer.get("restless", false) and phase == "waiting" and clip in ["seated-wait", "seated-wait-empty", "restless"]:
		return "restless"
	if clip == "seated-wait":
		return "seated-wait-empty"
	if clip == "eat" and customer.get("meal_dish") is Dictionary and customer.meal_dish.get("recipe_id") == "salmon_nigiri":
		return "eat-salmon"
	return clip

func customer_feedback(customer: Dictionary) -> Dictionary:
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
	for index in range(5):
		result.append(base.duplicate(true))
	result[1].merge({"preference_phase": "active", "preferred_recipe_id": "cucumber_maki", "preference_phase_elapsed": 2.0 + fmod(time, 6.0), "preference_progress": 0.75 - fmod(time, 6.0) / 8.0}, true)
	result[2].merge({"phase": "eating", "visual_phase": "eat", "meal_dish": {"recipe_id": "salmon_nigiri"}, "preference_phase": "satisfied", "happy_elapsed": fmod(time, 2.2), "happy_duration": 2.2}, true)
	result[3].merge({"preference_phase": "expired", "preference_phase_elapsed": fmod(time, 3.0)}, true)
	result[4].merge({"preference_phase": "expired", "preference_phase_elapsed": 5.0, "restless": true}, true)
	return result

func _gallery() -> void:
	var unit := portrait.size.x / 720.0
	var left := portrait.position.x + 36.0 * unit
	caption("Shared components", Vector2(left, 58 * unit), int(40 * unit), PAPER, true)
	caption("Customer visits · preferences and reactions", Vector2(left, 101 * unit), int(22 * unit), Color("a9d6d0"))
	var panel := Rect2(left, 240 * unit, portrait.size.x - 72 * unit, minf(940 * unit, portrait.size.y - 475 * unit))
	draw_style_box(_paper_style(), panel)
	var row_unit := panel.size.y / 940.0
	var pitch := minf(112 * unit, 106 * row_unit)
	caption("One guest, five moments", panel.position + Vector2(24 * unit, 30 * row_unit), int(27 * unit), INK, true)
	var guests := gallery_customers()
	var labels := ["Waiting", "Preference", "Happy", "Expired", "Restless", "Inactive"]
	for index in range(6):
		var column := index % 3
		var row := 0 if index < 3 else 1
		var base := panel.position + Vector2((112 + column * 212) * unit, (300 + row * 325) * row_unit)
		if index < 5:
			_gallery_tile(base, pitch)
			_seat_at({"facing": "south", "active": true}, base, pitch)
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
		caption(labels[index], panel.position + Vector2((57 + column * 212) * unit, (380 + row * 325) * row_unit), int(25 * unit))
	caption("Connected service", panel.position + Vector2(24 * unit, 740 * row_unit), int(27 * unit), INK, true)
	var start := panel.position + Vector2(108 * unit, 860 * row_unit)
	for index in range(4):
		var base := start + Vector2(float(index) * pitch, 0)
		_gallery_tile(base, pitch)
		var identity: String = ["belt-start-e", "belt-straight-e", "belt-straight-e", "belt-end-e"][index]
		sprite(identity, base, "running", "S", 0.0 if reduced_motion else time, pitch)
	for index in range(2):
		var progress := fmod((0.0 if reduced_motion else time * 0.7) + float(index) * 1.5, 3.0)
		var at: Vector2 = start + Vector2(progress * pitch, 0) + art.socket("belt-straight-e", "deck") * pitch / art.cell_size
		sprite("dish-salmon" if index == 0 else "dish-cucumber", at, "static", "S", 0.0, pitch)

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
