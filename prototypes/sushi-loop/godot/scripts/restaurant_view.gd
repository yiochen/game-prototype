extends Control
## Shared production renderer: true square ground cells, registered 3/4 art.

const ArtBook = preload("res://scripts/art_book.gd")
const Typography = preload("res://scripts/typography.gd")
const INK := Color("253b3b")
const NIGHT := Color("103d4b")
const PAPER := Color("ffefcf")
const DIRECTIONS := {"north": Vector2.UP, "south": Vector2.DOWN, "east": Vector2.RIGHT, "west": Vector2.LEFT}
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
var coin_icon: Texture2D
var actor_positions: Dictionary = {}
var actor_facings: Dictionary = {}

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	font = Typography.body()
	heading = Typography.heading()
	coin_icon = load("res://assets/ui/coin.svg")
	art.reload()

func update_layout() -> void:
	var width := minf(size.x, size.y * 9.0 / 16.0)
	portrait = Rect2((size.x - width) * 0.5, 0, width, size.y)
	var floor_data: Dictionary = state.get("floor", {})
	cell = (width - 48.0) / float(floor_data.get("viewport_columns", floor_data.get("columns", 9)))
	var floor_height := float(floor_data.get("rows", 16)) * cell
	floor_origin = Vector2(portrait.position.x + 24.0, maxf(24.0, (size.y - floor_height) * 0.5))
	queue_redraw()

func cell_base(x: float, y: float) -> Vector2:
	var camera: Dictionary = state.get("camera", {"x": 0.0, "y": 0.0})
	return floor_origin + Vector2(x + 0.5 - float(camera.x), y + 0.5 - float(camera.y)) * cell

func sprite(key: String, base: Vector2, dimensions: Vector2, tint := Color.WHITE) -> void:
	var texture: Texture2D = art.get_texture(key)
	if texture != null:
		draw_texture_rect(texture, art.fit(key, base, dimensions), false, tint)

func caption(text: String, at: Vector2, pixels: int = 30, color := INK, use_heading := false) -> void:
	draw_string(heading if use_heading else font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, color)

func _draw() -> void:
	if font == null:
		return
	draw_rect(Rect2(Vector2.ZERO, size), NIGHT)
	if show_gallery:
		_gallery()
	else:
		_room()

func _room() -> void:
	if state.is_empty():
		return
	var camera: Dictionary = state.camera
	var rows := int(state.floor.rows)
	var columns := int(state.floor.world_columns)
	var floor_texture: Texture2D = art.get_texture("floor_wood")
	var world_rect := Rect2(floor_origin - Vector2(float(camera.x), float(camera.y)) * cell, Vector2(columns, rows) * cell)
	draw_rect(portrait, Color("efd7a7"))
	# One quiet painted material spans four cells, continuing behind the HUD
	# through tall-phone margins. Ground geometry never takes sprite perspective.
	for y in range(-6, rows + 6):
		for x in range(columns):
			var origin := floor_origin + Vector2(float(x) - float(camera.x), float(y) - float(camera.y)) * cell
			var rect := Rect2(origin, Vector2.ONE * cell)
			if portrait.intersects(rect) and floor_texture != null:
				var tint := Color.WHITE if x < int(state.floor.columns) else Color("afa18a")
				_floor_tile(floor_texture, rect, x, y, tint)
	var grid_ink := Color(0.38, 0.27, 0.17, 0.22)
	for x in range(columns + 1):
		var at := world_rect.position + Vector2(float(x) * cell, 0)
		draw_line(at, at + Vector2(0, world_rect.size.y), grid_ink, 1.8, true)
	for y in range(rows + 1):
		var at := world_rect.position + Vector2(0, float(y) * cell)
		draw_line(at, at + Vector2(world_rect.size.x, 0), grid_ink, 1.8, true)
	for item in render_plan():
		match item.kind:
			"belt":
				_belt(item.value)
			"dish":
				_dish(item.value)
			"sprite":
				sprite(item.key, item.base, item.dimensions)
			"chef":
				_chef(item.value)
			"customer":
				_customer(item.value)
	_clean_actor_history()
	for pop in sale_pops:
		var age := time - float(pop.time)
		if age >= 0 and age < 0.9:
			var center := cell_base(float(pop.x), float(pop.y)) - Vector2(0, cell * (1.1 + (0.0 if reduced_motion else age * 0.75)))
			draw_texture_rect(coin_icon, Rect2(center - Vector2.ONE * cell * 0.2, Vector2.ONE * cell * 0.4), false, Color(1, 1, 1, 1.0 - age / 0.9))

func render_plan() -> Array:
	# Structural conveyor modules are a complete pass before any carried dish.
	# World objects then sort by their ground anchor, not by atlas/bounding height.
	var decks: Array = []
	var foreground: Array = _decor_plan()
	for object in state.get("objects", []):
		if object.kind == "belt":
			decks.append({"kind": "belt", "value": object})
			if object.get("dish") != null:
				foreground.append({"kind": "dish", "value": object, "depth": float(object.y), "priority": 1})
		elif object.kind == "seat":
			foreground.append(_prop("stool", float(object.x), float(object.y), Vector2(0.84, 0.78)))
		elif object.kind == "chef":
			foreground.append({"kind": "chef", "value": object, "depth": float(object.y), "priority": 2})
	for customer in state.get("customers", []):
		foreground.append({"kind": "customer", "value": customer, "depth": float(customer.y), "priority": 2})
	foreground.sort_custom(func(a: Dictionary, b: Dictionary):
		if not is_equal_approx(float(a.depth), float(b.depth)):
			return float(a.depth) < float(b.depth)
		return int(a.get("priority", 0)) < int(b.get("priority", 0)))
	return decks + foreground

func _prop(key: String, x: float, y: float, dimensions: Vector2) -> Dictionary:
	return {"kind": "sprite", "key": key, "base": cell_base(x, y), "dimensions": dimensions * cell, "depth": y, "priority": 0}

func _decor_plan() -> Array:
	if state.is_empty():
		return []
	var result: Array = [_prop("entrance", float(state.floor.entrance.x), float(state.floor.entrance.y), Vector2(1.6, 2.0))]
	for y in [2.0, 6.0, 12.0, 15.0]:
		result.append(_prop("plant" if int(y) % 2 == 0 else "barrel", -0.43, y, Vector2(0.8, 1.2)))
	for x in [1.2, 7.0, 10.8, 17.0, 20.5, 25.4]:
		result.append(_prop("lantern", x, 0.6, Vector2(0.65, 1.0)))
		result.append(_prop("crate" if int(x) % 2 == 0 else "plant", x, 15.7, Vector2(0.9, 1.0)))
	for pile in [["pile_sofa", 11.0, 4.0], ["pile_shelf", 15.0, 9.0], ["pile_cart", 23.0, 5.0], ["covered_dock", 13.0, 14.0], ["pile_sofa", 23.0, 12.0]]:
		result.append(_prop(str(pile[0]), float(pile[1]), float(pile[2]), Vector2(3.1, 3.2)))
	return result

func _has_belt(at: Vector2) -> bool:
	for object in state.objects:
		if object.kind == "belt" and Vector2(float(object.x), float(object.y)).is_equal_approx(at):
			return true
	return false

func belt_clip(belt: Dictionary) -> String:
	var direction: Vector2 = DIRECTIONS.get(str(belt.facing), Vector2.RIGHT)
	var at := Vector2(float(belt.x), float(belt.y))
	var ordinal := 0
	var previous := at - direction
	while _has_belt(previous):
		ordinal += 1
		previous -= direction
	var key := "belt_horizontal" if ordinal % 2 == 1 else "belt_horizontal_b"
	if not _has_belt(at - direction):
		key = "belt_end_" + {"east": "left", "west": "right", "north": "down", "south": "up"}.get(str(belt.facing), "left")
	elif not _has_belt(at + direction):
		key = "belt_end_" + {"east": "right", "west": "left", "north": "up", "south": "down"}.get(str(belt.facing), "right")
	return key

func _belt(belt: Dictionary) -> void:
	var key: String = art.animation_frame(belt_clip(belt), 0.0 if reduced_motion else float(state.elapsed))
	var center := cell_base(float(belt.x), float(belt.y))
	# All modules are equal native-width quarter cuts of the SAME whole strip.
	# Width sets their scale; independent height fitting would open rail gaps.
	sprite(key, center, Vector2(cell, cell * 2.0))

func _dish(belt: Dictionary) -> void:
	var direction: Vector2 = DIRECTIONS.get(str(belt.facing), Vector2.ZERO)
	var ahead := Vector2.ZERO
	for other in state.objects:
		if other.kind == "belt" and float(other.x) == float(belt.x) + direction.x and float(other.y) == float(belt.y) + direction.y and other.get("dish") == null:
			ahead = direction * cell * float(belt.travel_progress)
			break
	var center := cell_base(float(belt.x), float(belt.y)) + ahead - Vector2(0, cell * 0.12)
	sprite(str(belt.dish.recipe_id), center, Vector2(cell * 0.53, cell * 0.43))

func _floor_tile(texture: Texture2D, destination: Rect2, x: int, y: int, tint: Color) -> void:
	var quarter := texture.get_size() / 4.0
	var source := Rect2(Vector2(posmod(x, 4), posmod(y, 4)) * quarter, quarter)
	draw_texture_rect_region(texture, destination, source, tint)

func _chef(chef: Dictionary) -> void:
	var base := cell_base(float(chef.x), float(chef.y))
	var facing: String = {"north": "up", "south": "down", "west": "left", "east": "right"}.get(str(chef.facing), "up")
	var held := chef.get("held_dish") != null
	var clip := ("chef_hold_" if held else "chef_work_") + facing
	var key: String = art.animation_frame(clip, 0.0 if reduced_motion else float(state.elapsed))
	sprite(key, base, Vector2(cell * 0.85, cell * 1.28))
	# The board and recipe remain wholly inside the chef's ground footprint.
	var board_base := base + Vector2(cell * 0.28, cell * 0.29)
	sprite("blackboard", board_base, Vector2(cell * 0.32, cell * 0.43))
	sprite(str(chef.recipe_id), board_base - Vector2(0, cell * 0.26), Vector2(cell * 0.23, cell * 0.19))
	if held:
		var center := base - Vector2(cell * 0.4, cell * 1.15)
		draw_circle(center, cell * 0.12, PAPER)
		draw_arc(center, cell * 0.12, 0, TAU, 28, INK, 2.2, true)
		draw_line(center, center - Vector2(0, cell * 0.065), INK, 2.0, true)
		draw_line(center, center + Vector2(cell * 0.04, cell * 0.03), INK, 2.0, true)

func _customer(customer: Dictionary) -> void:
	var identity := "guest_a" if int(customer.get("appearance", 0)) % 2 == 0 else "guest_b"
	var position := Vector2(float(customer.x), float(customer.y))
	var previous: Vector2 = actor_positions.get(customer.id, position)
	var movement := position - previous
	if movement.length_squared() > 0.00001:
		actor_facings[customer.id] = ("right" if movement.x > 0 else "left") if absf(movement.x) > absf(movement.y) else ("down" if movement.y > 0 else "up")
	actor_positions[customer.id] = position
	var clip: String = identity + "_walk_" + str(actor_facings.get(customer.id, "down"))
	if customer.phase in ["waiting", "eating"]:
		clip = identity + ("_eating_down" if customer.phase == "eating" else "_waiting_down")
	var phase := float(posmod(str(customer.id).hash(), 6))
	var key: String = art.animation_frame(clip, 0.0 if reduced_motion else float(state.elapsed), 0.0 if reduced_motion else phase)
	sprite(key, cell_base(float(customer.x), float(customer.y)), Vector2(cell * 0.85, cell * 1.26))

func _clean_actor_history() -> void:
	var active_ids := {}
	for customer in state.customers:
		active_ids[customer.id] = true
	for identity in actor_positions.keys():
		if not active_ids.has(identity):
			actor_positions.erase(identity)
			actor_facings.erase(identity)

func _gallery() -> void:
	var unit := portrait.size.x / 720.0
	var left := portrait.position.x + 44 * unit
	caption("Shared components", Vector2(left, 58 * unit), int(42 * unit), PAPER, true)
	caption("Restaurant service", Vector2(left, 100 * unit), int(27 * unit), Color("a9d6d0"))
	var panel_height := minf(940 * unit, portrait.size.y - 475 * unit)
	var panel := Rect2(left, 240 * unit, portrait.size.x - 88 * unit, panel_height)
	var row_unit := panel_height / 940.0
	var picture_scale := minf(unit, row_unit)
	draw_style_box(_paper_style(), panel)
	caption("Chefs & guests · 6-frame loops", panel.position + Vector2(30 * unit, 46 * row_unit), int(30 * unit), INK, true)
	var clips := ["chef_work_down", "chef_hold_up", "guest_a_waiting_down", "guest_b_eating_down"]
	for i in range(clips.size()):
		var key: String = art.animation_frame(clips[i], 0.0 if reduced_motion else time)
		sprite(key, panel.position + Vector2((86 + i * 152) * unit, 246 * row_unit), Vector2(112, 177) * picture_scale)
	caption("Tile centers · 3/4 front + top", panel.position + Vector2(30 * unit, 304 * row_unit), int(31 * unit))
	for i in range(4):
		var clip: String = ["stool", "salmon_nigiri", "belt_horizontal", "belt_endpoint"][i]
		var key: String = art.animation_frame(clip, 0.0 if reduced_motion else time)
		var base := panel.position + Vector2((82 + i * 148) * unit, (548 if i == 0 else 495) * row_unit)
		sprite(key, base, Vector2(126, 145) * picture_scale)
	caption("Food, seats & conveyor", panel.position + Vector2(30 * unit, 598 * row_unit), int(34 * unit))
	for i in range(5):
		sprite(["plant", "lantern", "barrel", "entrance", "crate"][i], panel.position + Vector2((72 + i * 118) * unit, 834 * row_unit), Vector2(96, 132) * picture_scale)
	caption("Room edge dressing", panel.position + Vector2(30 * unit, 890 * row_unit), int(34 * unit))

func _paper_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = PAPER
	style.border_color = Color("513d32")
	style.set_border_width_all(4)
	style.set_corner_radius_all(18)
	style.shadow_color = Color(0, 0, 0, 0.2)
	style.shadow_size = 10
	return style
