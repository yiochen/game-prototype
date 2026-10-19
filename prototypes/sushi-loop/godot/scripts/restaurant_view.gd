extends Control
## Shared scene/gallery renderer for the approved Faceted #33 asset library.
## Ground cells are square; every full sprite uses its authored 128px root/pitch.

const ArtBook = preload("res://scripts/art_book.gd")
const Typography = preload("res://scripts/typography.gd")
const INK := Color("253b3b")
const NIGHT := Color("103d4b")
const PAPER := Color("ffefcf")
const DIRECTIONS := {"north": Vector2.UP, "south": Vector2.DOWN, "east": Vector2.RIGHT, "west": Vector2.LEFT}
const FACING := {"north": "N", "east": "E", "south": "S", "west": "W"}
const CUSTOMERS := ["customer-rosa", "customer-ellis", "customer-samir", "customer-june"]
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
			"board":
				_board(item.value)
			"customer":
				_customer(item.value)
	for pop in sale_pops:
		var age := time - float(pop.time)
		if age >= 0.0 and age < 0.9:
			# Native pop frames already rise above this registered customer root.
			# Keep its authored scale/motion and the existing quiet alpha fade.
			sprite("coin-pop", cell_base(float(pop.x), float(pop.y)), "pop", "S", 0.0 if reduced_motion else age, -1.0, Color(1, 1, 1, 1.0 - age / 0.9))

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
				result.append(_prop("stool-wood", float(object.x), float(object.y), "static", str(FACING.get(object.facing, "S"))))
			"chef":
				result.append({"kind": "chef", "value": object, "depth": float(object.y), "priority": 2})
				result.append({"kind": "board", "value": object, "depth": float(object.y) + 0.4, "priority": 4})
	for customer in state.get("customers", []):
		result.append({"kind": "customer", "value": customer, "depth": float(customer.y), "priority": 2})
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
	for y in [4, 7, rows - 2]:
		result.append(_prop("barrel-wood" if y == 7 else "plant-angular", 0, float(y), "static" if y == 7 else "idle"))
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

func _belt(belt: Dictionary) -> void:
	sprite(belt_clip(belt), cell_base(float(belt.x), float(belt.y)), "running", "S", 0.0 if reduced_motion else float(state.elapsed))

func dish_base(belt: Dictionary) -> Vector2:
	var direction: Vector2 = DIRECTIONS.get(str(belt.facing), Vector2.ZERO)
	var ahead := Vector2.ZERO
	for other in state.objects:
		if other.kind == "belt" and float(other.x) == float(belt.x) + direction.x and float(other.y) == float(belt.y) + direction.y and other.get("dish") == null:
			ahead = direction * cell * float(belt.travel_progress)
			break
	return cell_base(float(belt.x), float(belt.y)) + ahead + art.socket(belt_clip(belt), "deck") * cell / art.cell_size

func _dish(belt: Dictionary) -> void:
	sprite(str(DISHES.get(str(belt.dish.recipe_id), "dish-salmon")), dish_base(belt))

func _chef(chef: Dictionary) -> void:
	var held := chef.get("held_dish") != null
	var clip := str(chef.get("visual_phase", "hold" if held else "work"))
	var seconds := 0.0 if reduced_motion else float(chef.get("visual_elapsed", state.elapsed))
	sprite("chef-lena", cell_base(float(chef.x), float(chef.y)), clip, str(FACING.get(chef.facing, "N")), seconds)
	if held and clip != "load":
		var center := cell_base(float(chef.x), float(chef.y)) - Vector2(cell * 0.42, cell * 1.25)
		draw_circle(center, cell * 0.10, PAPER)
		draw_arc(center, cell * 0.10, 0, TAU, 24, INK, 1.4, true)
		draw_line(center, center - Vector2(0, cell * 0.05), INK, 1.4, true)

func _board(chef: Dictionary) -> void:
	var base := cell_base(float(chef.x), float(chef.y))
	# Front placement and blank face are modeled in the source. Do not translate
	# this fixture to a second ground cell or rotate it away from the player.
	sprite("chef-blackboard", base, "idle", "S")
	var face: Vector2 = base + art.socket("chef-blackboard", "display_face") * cell / art.cell_size
	# Dynamic recipe content is UI on the board, independent of native artwork.
	# A uniform quarter-size copy of the food sprite is centered on its plate root.
	var food := str(DISHES.get(str(chef.recipe_id), "dish-salmon"))
	sprite(food, face, "static", "S", 0.0, cell * 0.28)

func _customer(customer: Dictionary) -> void:
	var identity: String = CUSTOMERS[posmod(int(customer.get("appearance", 0)), CUSTOMERS.size())]
	var direction := str(FACING.get(str(customer.get("facing", "south")), "S"))
	var phase := str(customer.phase)
	var fallback := "eat" if phase == "eating" else "seated-wait" if phase == "waiting" else "walk"
	var clip := str(customer.get("visual_phase", fallback))
	var seconds := 0.0 if reduced_motion else float(customer.get("visual_elapsed", state.elapsed))
	# Native sit/stand actions were calibrated to the wood stool's support plane.
	# Their ground root stays centered while hips and legs move inside the frame.
	sprite(identity, cell_base(float(customer.x), float(customer.y)), clip, direction, seconds)

func _gallery() -> void:
	var unit := portrait.size.x / 720.0
	var left := portrait.position.x + 36.0 * unit
	caption("Shared components", Vector2(left, 58 * unit), int(40 * unit), PAPER, true)
	caption("Approved Faceted art · same scene renderer", Vector2(left, 101 * unit), int(22 * unit), Color("a9d6d0"))
	var panel := Rect2(left, 240 * unit, portrait.size.x - 72 * unit, minf(940 * unit, portrait.size.y - 475 * unit))
	draw_style_box(_paper_style(), panel)
	var row_unit := panel.size.y / 940.0
	var pitch := minf(116 * unit, 144 * row_unit)
	caption("Four facings · C125 chef", panel.position + Vector2(24 * unit, 42 * row_unit), int(27 * unit), INK, true)
	for index in range(4):
		var base := panel.position + Vector2((94 + index * 150) * unit, 260 * row_unit)
		_gallery_tile(base, pitch)
		sprite("chef-lena", base, "work", ["N", "E", "S", "W"][index], 0.0 if reduced_motion else time, pitch)
	caption("Guests · walk, sit, wait, eat", panel.position + Vector2(24 * unit, 370 * row_unit), int(27 * unit), INK, true)
	for index in range(4):
		var base := panel.position + Vector2((94 + index * 150) * unit, 570 * row_unit)
		_gallery_tile(base, pitch)
		var clip: String = ["walk", "sit-down", "seated-wait", "eat"][index]
		if index > 0:
			sprite("stool-wood", base, "static", "S", 0.0, pitch)
		sprite(CUSTOMERS[index], base, clip, "S", 0.0 if reduced_motion else fmod(time, 1.8), pitch)
	caption("24-frame connected conveyor", panel.position + Vector2(24 * unit, 675 * row_unit), int(27 * unit), INK, true)
	var start := panel.position + Vector2(106 * unit, 825 * row_unit)
	for index in range(4):
		var base := start + Vector2(float(index) * pitch, 0)
		_gallery_tile(base, pitch)
		var identity: String = ["belt-start-e", "belt-straight-e", "belt-straight-e", "belt-end-e"][index]
		sprite(identity, base, "running", "S", 0.0 if reduced_motion else time, pitch)
	var dish_at: Vector2 = start + Vector2(fmod(0.0 if reduced_motion else time * 0.7, 3.0) * pitch, 0) + art.socket("belt-straight-e", "deck") * pitch / art.cell_size
	sprite("dish-salmon", dish_at, "static", "S", 0.0, pitch)
	caption("Whole frames · registered tile roots", panel.position + Vector2(24 * unit, 924 * row_unit), int(23 * unit))

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
