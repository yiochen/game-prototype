extends Control
## The same production renderer is used in gameplay and the native gallery.

const ArtBook = preload("res://scripts/art_book.gd")
const Typography = preload("res://scripts/typography.gd")
const INK := Color("253b3b")
const NIGHT := Color("103d4b")
const PAPER := Color("ffefcf")
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
	font = Typography.body()
	heading = Typography.heading()
	coin_icon = load("res://assets/ui/coin.svg")
	art.reload()

func update_layout() -> void:
	var width := minf(size.x, size.y * 9.0 / 16.0)
	portrait = Rect2((size.x - width) * 0.5, 0, width, size.y)
	var floor_data: Dictionary = state.get("floor", {})
	cell = (width - 48.0) / float(floor_data.get("viewport_columns", floor_data.get("columns", 9)))
	var floor_height := float(state.get("floor", {}).get("rows", 16)) * cell
	floor_origin = Vector2(portrait.position.x + 24.0, maxf(24.0, (size.y - floor_height) * 0.5))
	queue_redraw()

func cell_base(x: float, y: float) -> Vector2:
	var camera: Dictionary = state.get("camera", {"x": 0.0, "y": 0.0})
	return floor_origin + Vector2((x + 0.5 - float(camera.x)) * cell, (y + 0.92 - float(camera.y)) * cell)

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
	var rows: int = int(state.floor.rows)
	var columns: int = int(state.floor.world_columns)
	var floor_texture: Texture2D = art.get_texture("floor_wood")
	var world_rect := Rect2(floor_origin - Vector2(float(camera.x), float(camera.y)) * cell, Vector2(columns, rows) * cell)
	# One material spans four cells. The floor extends behind the transparent
	# controls, including tall-phone margins; cell pitch stays square.
	if floor_texture != null:
		for y in range(-6, rows + 6):
			for x in range(columns):
				var origin := floor_origin + Vector2(float(x) - float(camera.x), float(y) - float(camera.y)) * cell
				var rect := Rect2(origin, Vector2.ONE * cell)
				if portrait.intersects(rect):
					_floor_tile(floor_texture, rect, x, y, Color.WHITE)
	else:
		draw_rect(portrait, Color("9a7657"))
	for y in range(rows):
		for x in range(columns):
			var origin := floor_origin + Vector2(float(x) - float(camera.x), float(y) - float(camera.y)) * cell
			var rect := Rect2(origin, Vector2.ONE * cell)
			if not portrait.intersects(rect):
				continue
			var color := Color.WHITE if x < int(state.floor.columns) else Color("82735e")
			if floor_texture != null:
				_floor_tile(floor_texture, rect, x, y, color)
			else:
				draw_rect(rect, Color("bb966a"))
	# Grid marks are independent of the material's plank grain and aligned to
	# actual simulation cells, so empty aisles remain understandable on phones.
	var grid_ink := Color(0.32, 0.23, 0.17, 0.27)
	for x in range(columns + 1):
		var at := world_rect.position + Vector2(float(x) * cell, 0)
		draw_line(at, at + Vector2(0, world_rect.size.y), grid_ink, 2.0, true)
	for y in range(rows + 1):
		var at := world_rect.position + Vector2(0, float(y) * cell)
		draw_line(at, at + Vector2(world_rect.size.x, 0), grid_ink, 2.0, true)
	# Outer room edges are continuous; panel boundaries never become walls.
	_boundary(world_rect)
	for object in state.objects:
		if object.kind == "belt":
			var key := "belt_endpoint" if object.get("endpoint", false) or int(object.x) == 6 else "belt_horizontal"
			if int(object.x) == 3:
				key = "belt_end_left"
			var base := cell_base(float(object.x), float(object.y))
			sprite(key, base, Vector2(cell * 1.01, cell * 0.85))
			if object.get("dish") != null:
				var dish: Dictionary = object.dish
				var ahead := Vector2.ZERO
				var direction: Vector2 = {"north": Vector2.UP, "south": Vector2.DOWN, "east": Vector2.RIGHT, "west": Vector2.LEFT}.get(str(object.facing), Vector2.ZERO)
				for other in state.objects:
					if other.kind == "belt" and float(other.x) == float(object.x) + direction.x and float(other.y) == float(object.y) + direction.y and other.get("dish") == null:
						ahead = direction * cell * float(object.travel_progress)
						break
				sprite(str(dish.recipe_id), base + ahead - Vector2(0, cell * 0.21), Vector2(cell * 0.52, cell * 0.45))
		elif object.kind == "seat":
			sprite("stool", cell_base(float(object.x), float(object.y)), Vector2(cell * 0.65, cell * 0.68))
	var actors: Array = []
	for object in state.objects:
		if object.kind == "chef":
			actors.append({"kind": "chef", "value": object, "y": float(object.y)})
	for customer in state.customers:
		actors.append({"kind": "customer", "value": customer, "y": float(customer.y)})
	actors.sort_custom(func(a: Dictionary, b: Dictionary): return float(a.y) < float(b.y))
	for actor in actors:
		if actor.kind == "chef":
			_chef(actor.value)
		else:
			_customer(actor.value)
	var active_ids := {}
	for customer in state.customers:
		active_ids[customer.id] = true
	for identity in actor_positions.keys():
		if not active_ids.has(identity):
			actor_positions.erase(identity)
			actor_facings.erase(identity)
	for pop in sale_pops:
		var age := time - float(pop.time)
		if age >= 0 and age < 0.9:
			var center := cell_base(float(pop.x), float(pop.y)) - Vector2(0, cell * (1.1 + (0.0 if reduced_motion else age * 0.75)))
			draw_texture_rect(coin_icon, Rect2(center - Vector2.ONE * cell * 0.2, Vector2.ONE * cell * 0.4), false, Color(1, 1, 1, 1.0 - age / 0.9))

func _floor_tile(texture: Texture2D, destination: Rect2, x: int, y: int, tint: Color) -> void:
	var quarter := texture.get_size() / 4.0
	var source := Rect2(Vector2(posmod(x, 4), posmod(y, 4)) * quarter, quarter)
	draw_texture_rect_region(texture, destination, source, tint)

func _boundary(world_rect: Rect2) -> void:
	var entrance_x := cell_base(float(state.floor.entrance.x), 0).x
	var top := world_rect.position.y
	sprite("entrance", Vector2(entrance_x, top + cell * 0.9), Vector2(cell * 0.98, cell * 1.36))
	for y in [2.0, 6.0, 12.0, 15.0]:
		var base := cell_base(-0.43, y)
		sprite("plant" if int(y) % 2 == 0 else "barrel", base, Vector2(cell * 0.7, cell * 1.2))
	for x in [1.2, 7.0, 10.8, 17.0, 20.5, 25.4]:
		sprite("lantern", cell_base(x, 0.6), Vector2(cell * 0.65, cell * 1.2))
		sprite("crate" if int(x) % 2 == 0 else "plant", cell_base(x, 15.7), Vector2(cell * 0.8, cell * 1.0))
	# Whole environmental objects preview the still locked adjoining floor.
	for pile in [["pile_sofa", 11.0, 4.0], ["pile_shelf", 15.0, 9.0], ["pile_cart", 23.0, 5.0], ["covered_dock", 13.0, 14.0], ["pile_sofa", 23.0, 12.0]]:
		sprite(str(pile[0]), cell_base(float(pile[1]), float(pile[2])), Vector2(cell * 3.1, cell * 3.2))

func _chef(chef: Dictionary) -> void:
	var base := cell_base(float(chef.x), float(chef.y))
	var facing: String = {"north": "up", "south": "down", "west": "left", "east": "right"}.get(str(chef.facing), "up")
	var key: String = "chef_" + facing
	if chef.get("held_dish") != null and art.get_texture("chef_hold_" + facing) != null:
		key = "chef_hold_" + facing
	var working := chef.get("held_dish") == null
	var bob := 0.0 if reduced_motion or not working else sin(time * 4.0) * cell * 0.015
	sprite(key, base + Vector2(0, bob), Vector2(cell * 0.78, cell * 1.46))
	var board_base := base + Vector2(cell * 0.23, -cell * 0.02)
	sprite("blackboard", board_base, Vector2(cell * 0.43, cell * 0.60))
	sprite(str(chef.recipe_id), board_base - Vector2(0, cell * 0.13), Vector2(cell * 0.31, cell * 0.25))
	if not working:
		var center := base - Vector2(cell * 0.36, cell * 1.2)
		draw_circle(center, cell * 0.12, PAPER)
		draw_arc(center, cell * 0.12, 0, TAU, 28, INK, 2.2, true)
		draw_line(center, center - Vector2(0, cell * 0.065), INK, 2.0, true)
		draw_line(center, center + Vector2(cell * 0.04, cell * 0.03), INK, 2.0, true)

func _customer(customer: Dictionary) -> void:
	var index := int(customer.get("appearance", 0))
	var identity := "guest_a" if index % 2 == 0 else "guest_b"
	var seated: bool = customer.phase in ["waiting", "eating"]
	var position := Vector2(float(customer.x), float(customer.y))
	var previous: Vector2 = actor_positions.get(customer.id, position)
	var movement := position - previous
	if movement.length_squared() > 0.00001:
		actor_facings[customer.id] = ("right" if movement.x > 0 else "left") if absf(movement.x) > absf(movement.y) else ("down" if movement.y > 0 else "up")
	actor_positions[customer.id] = position
	var facing: String = actor_facings.get(customer.id, "down")
	var key: String = identity + "_" + facing
	if seated:
		key = identity + ("_seated_down" if customer.phase == "eating" else "_waiting_down")
		if art.get_texture(key) == null:
			key = identity + "_down"
	var base := cell_base(float(customer.x), float(customer.y))
	var stride := 0.0 if reduced_motion or seated else sin(time * 9.0 + index) * cell * 0.025
	if customer.phase == "eating" and not reduced_motion:
		stride = sin(time * 4.0 + index) * cell * 0.008
	sprite(key, base + Vector2(0, stride), Vector2(cell * 0.76, cell * 1.3))

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
	caption("Chefs & guests", panel.position + Vector2(30 * unit, 46 * row_unit), int(32 * unit), INK, true)
	for i in range(4):
		var keys := ["chef_down", "chef_hold_up", "guest_a_waiting_down", "guest_b_seated_down"]
		sprite(keys[i], panel.position + Vector2((86 + i * 152) * unit, 246 * row_unit), Vector2(112, 177) * picture_scale)
	caption("Square cells · anchored bases", panel.position + Vector2(30 * unit, 304 * row_unit), int(34 * unit))
	for i in range(4):
		var base := panel.position + Vector2((82 + i * 148) * unit, 548 * row_unit)
		sprite(["stool", "salmon_nigiri", "belt_horizontal", "belt_endpoint"][i], base, Vector2(126, 145) * picture_scale)
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
