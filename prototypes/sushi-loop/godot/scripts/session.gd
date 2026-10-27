class_name GameSession
extends RefCounted
## The restaurant's public command / elapsed-time / save boundary.
## Construction loads tuneable content; rules have no wall clock or persistence.
## A caller decides when time passes and where snapshots are stored.

const SAVE_VERSION := 1
const Doorway = preload("res://scripts/doorway.gd")
const RecipeBook = preload("res://scripts/recipe_book.gd")
const RECIPE_BOOK_VERSION := 1
const StaffBook = preload("res://scripts/staff_book.gd")
const STAFF_VERSION := 1
const BELT_MOTION_VERSION := 1
const BELT_ROUTE_VERSION := 1
const BeltRoutes = preload("res://scripts/belt_routes.gd")
const CUSTOMER_VISIT_VERSION := 1
const CUSTOMER_NAVIGATION_VERSION := 1
const CUSTOMER_ADMISSION_VERSION := 1
const CUSTOMER_LAYOUT_VERSION := 2
const EDITOR_VERSION := 3
const EDITOR_PATH := "res://content/editor.json"
const EDITOR_LAYERS := ["people", "layout", "floor"]
const DECOR_ART_IDS := ["plant-angular", "crate-wood", "barrel-wood"]
const CHEF_ART_IDS := ["chef-lena", "chef-omar", "chef-ama", "chef-mateo", "chef-noor", "chef-dalia", "chef-ellis", "chef-rowan"]
const MAX_EXACT_INTEGER := 9007199254740991
const CONTENT_PATH := "res://content/starter.json"
const DIRECTIONS := {
	"north": Vector2i(0, -1), "east": Vector2i(1, 0),
	"south": Vector2i(0, 1), "west": Vector2i(-1, 0),
}

var _configuration: Dictionary = {}
var _state: Dictionary = {}
var _random := RandomNumberGenerator.new()
var _remainder := 0.0
var _staff_seed := 1
var _access_paths: Dictionary = {}
var _editor_content: Dictionary = {}

static func new_session(seed_value: int = 1, configuration: Dictionary = {}) -> GameSession:
	var session := GameSession.new()
	var defaults: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONTENT_PATH))
	if not defaults is Dictionary:
		push_error("The restaurant starter content could not be read.")
		return null
	session._configuration = session._merge_configuration(defaults, configuration)
	# Custom simulation fixtures can define their own small floor. A backdrop
	# is reserved only when that floor explicitly opts into the room contract.
	if configuration.has("floor") and not configuration.floor.has("backdrop_rows"):
		session._configuration.floor.backdrop_rows = 0
	if not session._valid_configuration(session._configuration):
		push_error("The restaurant starter configuration is invalid.")
		return null
	session._random.seed = seed_value
	session._staff_seed = seed_value
	session._start()
	return session

func command(request: Dictionary) -> Dictionary:
	if request.get("type") in ["hire_applicant", "refresh_applicants", "staff_seen"]:
		return StaffBook.command(_configuration, _state, request)
	if request.get("type") == "staff_place":
		var stock:=_inventory_item(str(request.get("inventory_id","")))
		if stock.get("kind")!="chef" or stock.get("assigned",false):return {"ok":false,"reason":"invalid_staff"}
		var old_mode: String = _state.mode
		var old_editor: Dictionary = _state.editor.duplicate(true)
		_state.mode = "edit"
		var placement: Dictionary = request.duplicate(true)
		placement.type = "editor_place"
		var result := _editor_change(placement)
		_state.mode = old_mode
		_state.editor = old_editor
		return result
	if request.get("type") in ["inspect_recipe", "prepare_recipe", "discover_recipe"]:
		return RecipeBook.command(_configuration, _state, request)
	if str(request.get("type", "")).begins_with("editor_"):
		return _editor_command(request)
	match request.get("type", ""):
		"set_mode":
			if not request.get("mode") in ["live", "edit"]:
				return {"ok": false, "reason": "invalid_mode"}
			_state.mode = request.mode
			if request.mode == "live":
				_state.editor.belt_path = []
				if not _customer_by_id(_state.editor.selected_id).is_empty(): _state.editor.selected_id = ""
			return {"ok": true}
		"set_camera":
			if not _finite_number(request.get("x")) or not _finite_number(request.get("y")):
				return {"ok": false, "reason": "invalid_camera"}
			_state.camera = {"x": float(request.x), "y": float(request.y)}
			return {"ok": true}
		"set_entrance_open":
			# An environmental control useful to exhibition hosts and deterministic
			# service scenarios. It never removes visitors already in the restaurant.
			if not request.get("open") is bool:
				return {"ok": false, "reason": "invalid_entrance"}
			_state.entrance_open = request.open
			return {"ok": true}
	return {"ok": false, "reason": "unknown_command"}

func advance(elapsed: float) -> Array:
	var events: Array = []
	if not is_finite(elapsed) or elapsed <= 0.0 or _state.is_empty() or _state.get("mode", "live") == "edit":
		return events
	var step := float(_configuration.service.step_seconds)
	var accumulated := _remainder + elapsed
	var step_count: float = floor((accumulated + 0.000000001) / step)
	if not is_finite(step_count) or step_count > MAX_EXACT_INTEGER - int(_state.step_index):
		return events
	_remainder = accumulated
	# Fixed simulation steps make caller frame rate irrelevant, including across
	# a save made between steps. The fractional remainder is part of the save.
	var count := int(floor((_remainder + 0.000000001) / step))
	_remainder = maxf(0.0, _remainder - count * step)
	for index in range(count):
		_state.step_index += 1
		_state.elapsed = int(_state.step_index) * step
		_step_customers(step, events)
		_step_belts(step, events)
		_step_chefs(step, events)
		_step_arrivals(step, events)
	return events

func snapshot() -> Dictionary:
	if _state.is_empty():
		return {}
	var result := {
		"version": SAVE_VERSION,
		"elapsed": _state.elapsed,
		"coins": _state.coins,
		"camera": _state.camera.duplicate(true),
		"entrance_open": _state.entrance_open,
		"mode": _state.mode,
		"editor": _state.editor.duplicate(true),
		"inventory": _inventory_snapshot(),
		"floor": _configuration.floor.duplicate(true),
		"recipes": _configuration.recipes.duplicate(true),
		"loading_seconds": float(_configuration.service.get("loading_seconds", 0.0)),
		"recipe_book": _state.recipe_book.duplicate(true),
		"staff": StaffBook.snapshot(_state),
		"objects": [],
		"customers": [],
		"stats": _state.stats.duplicate(true),
	}
	for original in _state.objects:
		var object: Dictionary = original.duplicate(true)
		if object.kind in ["chef", "seat"]:
			var service := _chef_service(original) if object.kind == "chef" else _seat_service(original)
			object.active = service.active
			object.inactive_reason = service.reason
		if object.kind == "chef":
			object.preparation_seconds = RecipeBook.seconds(_configuration.recipes.get(object.recipe_id, {}), object)
			object.preparation = clampf(float(object.preparation_elapsed) / float(object.preparation_seconds), 0.0, 1.0) if float(object.preparation_seconds) > 0.0 else 0.0
			object.erase("preparation_elapsed")
		elif object.kind == "belt":
			object.travel_progress = clampf(float(object.travel_elapsed) / float(_configuration.service.belt_seconds_per_cell), 0.0, 1.0)
			object.incoming_id = str(BeltRoutes.incoming(_state.objects, object.id).get("id", ""))
			object.erase("travel_elapsed")
		result.objects.append(object)
	result.editor.belt_targets = _belt_targets()
	for customer in _state.customers:
		var visible := {
			"id": customer.id, "x": customer.x, "y": customer.y,
			"seat_id": customer.seat_id, "phase": customer.phase,
			"meal_progress": clampf(float(customer.meal_elapsed) / float(customer.meal_duration), 0.0, 1.0),
			"meal_dish": customer.meal_dish.duplicate(true) if customer.meal_dish is Dictionary else null,
			"appearance": customer.appearance,
			"facing": customer.facing,
			"visual_phase": customer.visual_phase,
			"visual_elapsed": customer.visual_elapsed,
			"preferred_recipe_id": customer.preferred_recipe_id,
			"preference_phase": customer.preference_phase,
			"preference_phase_elapsed": customer.preference_phase_elapsed,
			"preference_total": _customer_number("preference_seconds"),
			"preference_remaining": maxf(0.0, _customer_number("preference_seconds") - float(customer.preference_elapsed)) if customer.preference_phase in ["pending", "active"] else 0.0,
			"preference_progress": clampf(1.0 - float(customer.preference_elapsed) / maxf(0.000000001, _customer_number("preference_seconds")), 0.0, 1.0) if customer.preference_phase in ["pending", "active"] else 0.0,
			"happy_elapsed": customer.happy_elapsed,
			"happy_duration": _customer_number("happy_seconds"),
			"restless": customer.restless, "waiting_elapsed": customer.waiting_elapsed,
			"yielding": customer.yielding,
			"navigation_mode": customer.navigation_mode,
			"entrance_wait_elapsed": customer.entrance_wait_elapsed,
			"entrance_wait_total": _customer_number("entrance_wait_seconds"),
			"wander_elapsed": customer.wander_elapsed,
			"layout_pending": customer.layout_pending, "standing_elapsed": customer.standing_elapsed,
			"render_offset_x": customer.render_offset_x, "render_offset_y": customer.render_offset_y,
		}
		Doorway.present(visible, customer, float(_configuration.service.walking_cells_per_second))
		result.customers.append(visible)
	return result

func save_data() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"belt_motion_version": BELT_MOTION_VERSION,
		"belt_route_version": BELT_ROUTE_VERSION,
		"customer_visit_version": CUSTOMER_VISIT_VERSION,
		"customer_navigation_version": CUSTOMER_NAVIGATION_VERSION,
		"customer_admission_version": CUSTOMER_ADMISSION_VERSION,
		"customer_layout_version": CUSTOMER_LAYOUT_VERSION,
		"editor_version": EDITOR_VERSION,
		"recipe_book_version": RECIPE_BOOK_VERSION,
		"staff_version": STAFF_VERSION,
		"configuration": _configuration.duplicate(true),
		"state": _state.duplicate(true),
		"remainder": _remainder,
		# JSON numbers cannot exactly hold a 64-bit generator state.
		"random_state": str(_random.state),
	}

func restore(data: Dictionary) -> bool:
	# Validate before changing anything. Restoring is a state replacement, never
	# elapsed-time simulation or event playback, even when called repeatedly.
	if not _nonnegative_integer(data.get("recipe_book_version", 0)) or int(data.get("recipe_book_version", 0)) > RECIPE_BOOK_VERSION:
		return false
	if not _nonnegative_integer(data.get("staff_version",0)) or int(data.get("staff_version",0))>STAFF_VERSION: return false
	if data.get("version") != SAVE_VERSION or not data.get("configuration") is Dictionary:
		return false
	if not _valid_configuration(data.configuration) or not data.get("state") is Dictionary:
		return false
	if not _finite_number(data.get("remainder")) or float(data.remainder) < 0.0:
		return false
	if float(data.remainder) >= float(data.configuration.service.step_seconds):
		return false
	if not data.get("random_state") is String or not data.random_state.is_valid_int():
		return false
	if data.random_state != str(int(data.random_state)):
		return false
	if not _nonnegative_integer(data.get("belt_motion_version", 0)) or int(data.get("belt_motion_version", 0)) > BELT_MOTION_VERSION:
		return false
	if not _nonnegative_integer(data.get("belt_route_version", 0)) or int(data.get("belt_route_version", 0)) > BELT_ROUTE_VERSION:
		return false
	if not _nonnegative_integer(data.get("customer_visit_version", 0)) or int(data.get("customer_visit_version", 0)) > CUSTOMER_VISIT_VERSION:
		return false
	if not _nonnegative_integer(data.get("customer_navigation_version", 0)) or int(data.get("customer_navigation_version", 0)) > CUSTOMER_NAVIGATION_VERSION:
		return false
	if not _nonnegative_integer(data.get("customer_admission_version", 0)) or int(data.get("customer_admission_version", 0)) > CUSTOMER_ADMISSION_VERSION:
		return false
	if not _nonnegative_integer(data.get("editor_version", 0)) or int(data.get("editor_version", 0)) > EDITOR_VERSION:
		return false
	if not _nonnegative_integer(data.get("customer_layout_version", 0)) or int(data.get("customer_layout_version", 0)) > CUSTOMER_LAYOUT_VERSION:
		return false
	var current_content: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONTENT_PATH))
	if not current_content is Dictionary or not current_content.get("floor") is Dictionary:
		return false
	var viewport_columns: Variant = current_content.floor.get("viewport_columns", current_content.floor.get("columns"))
	if not _nonnegative_integer(viewport_columns) or int(viewport_columns) < 1:
		return false
	var restored_configuration: Dictionary = data.configuration.duplicate(true)
	# Cell scale is presentation, independent of the saved restaurant footprint.
	# Older 9-column saves keep every cell and economic rule at the new scale.
	restored_configuration.floor.viewport_columns = int(viewport_columns)
	if not restored_configuration.has("customers"):
		restored_configuration.customers = current_content.get("customers", {}).duplicate(true)
	if restored_configuration.get("customers") is Dictionary:
		for key in ["wander_retry_seconds", "wander_speed_multiplier", "entrance_wait_seconds"]:
			if not restored_configuration.customers.has(key):
				restored_configuration.customers[key] = current_content.customers[key]
	if not _valid_configuration(restored_configuration):
		return false
	var restored_state: Dictionary = data.state.duplicate(true)
	if not restored_state.get("objects") is Array or not _valid_objects(restored_state.objects, restored_configuration): return false
	_migrate_visual_state(restored_state)
	if int(data.get("customer_visit_version", 0)) == 0:
		_migrate_visit_state(restored_state, restored_configuration)
	if int(data.get("editor_version", 0)) == 0:
		_initialize_editor_state(restored_state)
	elif int(data.get("editor_version", 0)) < EDITOR_VERSION:
		if not _migrate_editor_paging(restored_state, int(data.editor_version)): return false
	if int(data.get("belt_route_version", 0)) == 0:
		BeltRoutes.initialize(restored_state.objects)
		if not restored_state.get("editor") is Dictionary: return false
		restored_state.editor.belt_path = []
	var navigation_version := int(data.get("customer_navigation_version", 0))
	var admission_version := int(data.get("customer_admission_version", 0))
	if int(data.get("customer_layout_version", 0)) == 0:
		for customer in restored_state.get("customers", []):
			if not customer is Dictionary: return false
			_initialize_customer_layout(customer)
	if int(data.get("recipe_book_version", 0)) == 0:
		if not RecipeBook.initialize(restored_configuration, restored_state): return false
	if int(data.get("staff_version",0))==0: StaffBook.initialize(restored_configuration,restored_state)
	if not StaffBook.valid(restored_configuration,restored_state): return false
	if not RecipeBook.valid(restored_configuration, restored_state): return false
	if not _valid_saved_state(restored_state, restored_configuration, navigation_version, admission_version):
		return false
	if navigation_version == 0:
		_migrate_navigation(restored_state, restored_configuration)
	if admission_version == 0:
		for customer in restored_state.customers:
			# Existing visits keep every action, route and random sample. Admission
			# only adds neutral feedback clocks; old guests are never readmitted.
			customer.entrance_wait_elapsed = 0.0
			customer.wander_elapsed = 0.0
	if int(data.get("belt_motion_version", 0)) == 0:
		_migrate_belt_motion(restored_state)
	_configuration = restored_configuration
	_state = restored_state
	_normalize_restored_numbers()
	_remainder = float(data.remainder)
	_random.state = int(data.random_state)
	_rebuild_access()
	_upgrade_restaurant_backdrop()
	return true

func _upgrade_restaurant_backdrop() -> void:
	# Older shipped saves retain their economy, visits and edited furniture.
	# Custom simulation layouts are not restaurant-content migrations.
	var floor_data: Dictionary = _configuration.floor
	if floor_data.has("backdrop_rows") or int(_configuration.get("content_version", 0)) > 2 or int(floor_data.columns) < 7 or int(floor_data.rows) < 13 or int(floor_data.world_columns) < 21:
		return
	var entrance := Vector2i(4, 3)
	var offset := 0
	for objects in [_configuration.objects, _state.objects]:
		for object in objects:
			if int(object.y) < 3 or _point(object) == entrance: offset = 3
	# A layout using the old top rows moves as a whole, preserving every belt
	# connection and occupied seat. Add rows rather than discarding any cells.
	if offset > 0:
		floor_data.rows = int(floor_data.rows) + offset
		for objects in [_configuration.objects, _state.objects]:
			for object in objects: object.y = int(object.y) + offset
	for stock in _state.inventory:
		if stock.get("stored_object") is Dictionary:
			stock.stored_object.y = maxi(3, int(stock.stored_object.y) + offset)
	floor_data.backdrop_rows = 3
	floor_data.entrance = {"x": entrance.x, "y": entrance.y}
	_configuration.content_version = 3
	for customer in _state.customers:
		customer.y = float(customer.y) + offset
		if customer.phase == "entrance_wait":
			customer.x = float(entrance.x)
			customer.y = float(entrance.y)
	# Rebuild routes during migration without turning a blocked visit into a
	# departure before the first Live step (the released 0.4.8 contract).
	var saved_mode: String = _state.mode
	_state.mode = "edit"
	for customer in _state.customers:
		var waiting_overlap: bool = customer.phase != "entrance_wait" and _state.customers.any(func(other): return other.phase == "entrance_wait" and Vector2(float(customer.x),float(customer.y)).distance_to(Vector2(float(other.x),float(other.y))) < _customer_number("personal_space"))
		if customer.phase != "entrance_wait" and (float(customer.y) < 3.0 or waiting_overlap):
			# A visitor already crossing the retired doorway starts at the nearest
			# free floor cell. No arrival, meal, payment or visit clock is replayed.
			var nearest := Vector2(entrance)
			var distance := INF
			for y in range(3, int(floor_data.rows)):
				for x in range(int(floor_data.columns)):
					var point := Vector2(x, y)
					if not _object_at(Vector2i(point)).is_empty(): continue
					if _state.customers.any(func(other): return other.id != customer.id and point.distance_to(Vector2(float(other.x), float(other.y))) < 0.75): continue
					var candidate := point.distance_squared_to(Vector2(float(customer.x), float(customer.y)))
					if candidate < distance:
						distance = candidate
						nearest = point
			customer.x = nearest.x
			customer.y = nearest.y
		customer.render_offset_x = 0.0
		customer.render_offset_y = 0.0
		if customer.phase in ["walking", "leaving"]:
			var wander_elapsed: float = customer.wander_elapsed
			_replan_navigation(customer)
			if customer.navigation_mode == "wander": customer.wander_elapsed = wander_elapsed
		else:
			_clear_seated_route(customer)
	_state.mode = saved_mode
	_rebuild_access()

func _normalize_restored_numbers() -> void:
	# JSON represents integers and floats with the same number type. Normalize
	# counters before future ID creation, and cell coordinates before rendering.
	_configuration.starting_coins = int(_configuration.starting_coins)
	for field in ["columns", "rows", "world_columns", "viewport_columns"]:
		if _configuration.floor.has(field):
			_configuration.floor[field] = int(_configuration.floor[field])
	for field in ["x", "y"]:
		_configuration.floor.entrance[field] = int(_configuration.floor.entrance[field])
	for recipe in _configuration.recipes.values():
		recipe.price = int(recipe.price)
	for field in ["coins", "step_index", "next_customer_id", "next_dish_id", "next_object_id", "discarded_dishes"]:
		_state[field] = int(_state[field])
	_state.editor.page = int(_state.editor.page)
	for layer in EDITOR_LAYERS:
		_state.editor.pages[layer] = int(_state.editor.pages[layer])
	for entry in _state.inventory:
		entry.count = int(entry.count)
		if entry.kind == "chef" and not entry.assigned:
			entry.stored_object.x = int(entry.stored_object.x)
			entry.stored_object.y = int(entry.stored_object.y)
	for field in _state.stats:
		_state.stats[field] = int(_state.stats[field])
	for objects in [_configuration.objects, _state.objects]:
		for object in objects:
			object.x = int(object.x)
			object.y = int(object.y)
	for customer in _state.customers:
		customer.path_index = int(customer.path_index)
		customer.appearance = int(customer.appearance)
		customer.wander_cursor = int(customer.wander_cursor)
		for point in customer.path:
			point.x = int(point.x)
			point.y = int(point.y)

func _start() -> void:
	_state = {
		"coins": int(_configuration.starting_coins),
		"elapsed": 0.0, "step_index": 0,
		"camera": {"x": 0.0, "y": 0.0}, "entrance_open": true,
		"objects": _configuration.objects.duplicate(true), "customers": [],
		"stats": {"sales": 0, "served": 0, "arrivals": 0},
		"arrival_remaining": float(_configuration.service.first_arrival_seconds),
		"next_customer_id": 1, "next_dish_id": 1,
	}
	for object in _state.objects:
		match object.kind:
			"chef":
				object.preparation_elapsed = 0.0
				object.held_dish = null
				object.loading_elapsed = 0.0
				object.visual_phase = "work"
				object.visual_elapsed = 0.0
			"belt":
				object.travel_elapsed = 0.0
				object.dish = null
	_initialize_editor_state(_state)
	RecipeBook.initialize(_configuration, _state)
	StaffBook.initialize(_configuration,_state,_staff_seed)
	BeltRoutes.initialize(_state.objects)
	_remainder = 0.0
	_rebuild_access()

func _transition_seconds(key: String) -> float:
	# Missing durations identify legacy v1 configurations, whose instant
	# transitions keep their original timing when reopened.
	return float(_configuration.service.get(key, 0.0))

func _clock_advance(value: float, delta: float) -> float:
	# Canonical nanosecond precision removes float-addition residue before JSON
	# persistence, so a reopened action clock selects the same animation frame.
	return roundf((value + delta) * 1000000000.0) / 1000000000.0

func _set_visual(actor: Dictionary, phase: String) -> void:
	if actor.get("visual_phase") != phase:
		actor.visual_phase = phase
		actor.visual_elapsed = 0.0

func _step_chefs(delta: float, events: Array) -> void:
	for chef in _state.objects:
		if chef.kind != "chef":
			continue
		chef.visual_elapsed = _clock_advance(float(chef.visual_elapsed), delta)
		if not _chef_service(chef).active:
			chef.loading_elapsed = 0.0
			_set_visual(chef, "idle")
			continue
		if chef.held_dish == null:
			_set_visual(chef, "work")
			var duration := RecipeBook.seconds(_configuration.recipes[chef.recipe_id], chef)
			chef.preparation_elapsed = minf(duration, _clock_advance(float(chef.preparation_elapsed), delta))
			if float(chef.preparation_elapsed) + 0.000000001 >= duration:
				chef.preparation_elapsed = duration
				chef.held_dish = {"id": "dish-%s" % _state.next_dish_id, "recipe_id": chef.recipe_id}
				_state.next_dish_id += 1
				events.append({"type": "prepared", "chef_id": chef.id, "dish_id": chef.held_dish.id})
		if chef.held_dish == null:
			continue
		var loading := _facing_object(chef)
		var approaching := BeltRoutes.incoming(_state.objects, str(loading.get("id", "")))
		if loading.get("kind") != "belt" or loading.dish != null or (not approaching.is_empty() and approaching.dish != null and float(approaching.travel_elapsed) > 0.0):
			chef.loading_elapsed = 0.0
			_set_visual(chef, "hold")
			continue
		var loading_duration := _transition_seconds("loading_seconds")
		if loading_duration > 0.0:
			if chef.visual_phase != "load":
				chef.loading_elapsed = 0.0
				_set_visual(chef, "load")
				continue
			chef.loading_elapsed = minf(loading_duration, _clock_advance(float(chef.loading_elapsed), delta))
			chef.visual_elapsed = chef.loading_elapsed
			if float(chef.loading_elapsed) + 0.000000001 < loading_duration:
				continue
		# One ownership transfer after the visible loading motion. The plate is
		# never simultaneously present in the chef's hands and on the belt.
		loading.dish = chef.held_dish
		loading.travel_elapsed = 0.0
		chef.held_dish = null
		chef.preparation_elapsed = 0.0
		chef.loading_elapsed = 0.0
		_set_visual(chef, "work")
		events.append({"type": "loaded", "chef_id": chef.id, "belt_id": loading.id, "dish_id": loading.dish.id})

func _step_belts(delta: float, events: Array) -> void:
	var duration := float(_configuration.service.belt_seconds_per_cell)
	var transfers: Array = []
	var moving := {}
	for tile in _state.objects:
		if tile.kind == "belt" and tile.dish != null and not tile.next_id.is_empty(): moving[tile.id] = true
	moving = BeltRoutes.vacating_tiles(_state.objects, moving)
	var ready := {}
	# A free endpoint releases its upstream train; a closed occupied cycle can
	# advance as one train. A blocked endpoint freezes its complete queue.
	for tile in _state.objects:
		if tile.kind != "belt" or tile.dish == null:
			continue
		if tile.next_id.is_empty():
			continue
		if not moving.get(tile.id, false): continue
		tile.travel_elapsed = minf(duration, _clock_advance(float(tile.travel_elapsed), delta))
		if float(tile.travel_elapsed) + 0.000000001 >= duration: ready[tile.id] = true
	ready = BeltRoutes.vacating_tiles(_state.objects, ready)
	for tile in _state.objects:
		if tile.kind == "belt" and ready.get(tile.id, false):
			transfers.append({"from": tile, "to": BeltRoutes.by_id(_state.objects, tile.next_id), "dish": tile.dish})
	# Clear every source before assigning any destination, including cycles.
	for transfer in transfers:
		var source: Dictionary = transfer.from
		source.dish = null
		source.travel_elapsed = 0.0
	for transfer in transfers:
		var destination: Dictionary = transfer.to
		destination.dish = transfer.dish
		destination.travel_elapsed = 0.0
		events.append({"type": "belt_moved", "dish_id": destination.dish.id, "from_id": transfer.from.id, "to_id": destination.id})

func _customer_number(key: String) -> float:
	return float(_configuration.get("customers", {}).get(key, 0.0))

func _entrance_lanes() -> Array[Vector2i]:
	var entrance := _point(_configuration.floor.entrance)
	if not Doorway.enabled(_configuration.floor): return [entrance]
	var result: Array[Vector2i] = []
	for x in [4, 5]:
		var cell := Vector2i(x, entrance.y)
		if _object_at(cell).is_empty(): result.append(cell)
	return result

func _entrance_path(entrance: Vector2i, seat: Dictionary) -> Array:
	# Prefer walking straight off this side of the threshold before turning
	# toward the seat. Furniture may require a valid sideways alternative.
	if Doorway.enabled(_configuration.floor):
		var apron := entrance + Vector2i.DOWN
		if _object_at(apron).is_empty():
			var onward := _walk_path(apron, _point(seat), seat.id)
			if not onward.is_empty():
				onward.push_front({"x": apron.x, "y": apron.y})
				return onward
	return _walk_path(entrance, _point(seat), seat.id)

func _rebuild_access() -> void:
	_access_paths.clear()
	for object in _state.objects:
		if object.kind != "seat": continue
		_access_paths[object.id] = []
		for entrance in _entrance_lanes():
			var route := _entrance_path(entrance, object)
			if not route.is_empty():
				_access_paths[object.id] = route
				break

func _chef_service(chef: Dictionary) -> Dictionary:
	if str(chef.get("recipe_id", "")).is_empty(): return {"active":false, "reason":"no_recipe"}
	if _facing_object(chef).get("kind") != "belt":
		return {"active": false, "reason": "no_belt"}
	return {"active": true, "reason": ""}

func _belt_reaches(source: Dictionary, target_id: String) -> bool:
	var seen := {}
	var tile := source
	while tile.get("kind") == "belt" and not seen.has(tile.id):
		if tile.id == target_id:
			return true
		seen[tile.id] = true
		tile = BeltRoutes.by_id(_state.objects, tile.next_id)
	return false

func _seat_service(seat: Dictionary) -> Dictionary:
	var result := {"active": false, "reason": "no_belt", "ready": [], "menu": [], "front": ""}
	var front := _facing_object(seat)
	if front.get("kind") != "belt":
		return result
	result.front = front.dish.recipe_id if front.dish != null else ""
	if _access_paths.get(seat.id, []).is_empty():
		result.reason = "no_access"
		return result
	for object in _state.objects:
		if object.kind == "belt" and object.dish != null and _belt_reaches(object, front.id):
			if not result.ready.has(object.dish.recipe_id):
				result.ready.append(object.dish.recipe_id)
		elif object.kind == "chef" and _chef_service(object).active and _belt_reaches(_facing_object(object), front.id):
			if not result.menu.has(object.recipe_id):
				result.menu.append(object.recipe_id)
	result.active = not result.ready.is_empty() or not result.menu.is_empty()
	result.reason = "" if result.active else "no_supply"
	return result

func _preference_for(choices: Array) -> String:
	var recipes: Array = []
	for choice in choices:
		for recipe in choice.service.ready + choice.service.menu:
			if not recipes.has(recipe):
				recipes.append(recipe)
	recipes.sort()
	return str(recipes[_random.randi_range(0, recipes.size() - 1)])

func _choose_useful_seat(choices: Array, preferred: String) -> Dictionary:
	# Prefer an immediate match, then matching food en route, then its connected
	# chef's board. Distance breaks service-quality ties; RNG breaks equal ties.
	var best: Array = []
	var rank := 99
	var length := 2147483647
	for choice in choices:
		var service: Dictionary = choice.service
		var candidate_rank := 0 if service.front == preferred else 1 if service.ready.has(preferred) else 2 if service.menu.has(preferred) else 3 if not service.ready.is_empty() else 4
		var candidate_length: int = choice.path.size()
		if candidate_rank < rank or (candidate_rank == rank and candidate_length < length):
			best.clear()
			rank = candidate_rank
			length = candidate_length
		if candidate_rank == rank and candidate_length == length:
			best.append(choice)
	return best[_random.randi_range(0, best.size() - 1)]

func _new_visit_fields(customer: Dictionary) -> void:
	_initialize_customer_layout(customer)
	customer.visit_legacy = false
	customer.first_dish_received = false
	customer.preferred_recipe_id = ""
	customer.preference_phase = "pending"
	customer.preference_elapsed = 0.0
	customer.preference_phase_elapsed = 0.0
	customer.happy_elapsed = 0.0
	customer.waiting_elapsed = 0.0
	customer.restless = false
	customer.yielding = false
	customer.render_offset_x = 0.0
	customer.render_offset_y = 0.0
	customer.fullness = 0.0
	customer.appetite_target = _random.randf_range(_customer_number("fullness_min"), _customer_number("fullness_max"))
	customer.meal_fullness = 0.0
	customer.meal_duration = float(_configuration.service.eating_seconds)
	customer.departure_reason = ""
	customer.entrance_wait_elapsed = 0.0

func _arrival_seat_choices(customer: Dictionary = {}) -> Array:
	var choices: Array = []
	for seat in _state.objects:
		if seat.kind != "seat" or _seat_reserved(seat.id):
			continue
		var path: Array = _entrance_path(Doorway.anchor(customer, _configuration.floor), seat) if customer.has("door_lane") else _access_paths.get(seat.id, [])
		var service := _seat_service(seat)
		if not path.is_empty() and service.active:
			choices.append({"seat": seat, "path": path, "service": service})
	return choices

func _assign_arrival_seat(customer: Dictionary, choice: Dictionary, preferred: String) -> void:
	customer.seat_id = choice.seat.id
	customer.phase = "walking"
	customer.path = choice.path.duplicate(true)
	customer.path_index = 0
	customer.preferred_recipe_id = preferred
	customer.entrance_wait_elapsed = 0.0
	customer.facing = _direction_toward(Vector2(float(customer.x), float(customer.y)), Vector2(float(choice.path[0].x), float(choice.path[0].y)))
	_set_visual(customer, "walk")

func _step_arrivals(delta: float, events: Array) -> void:
	if not _state.entrance_open:
		return
	_state.arrival_remaining = maxf(0.0, float(_state.arrival_remaining) - delta)
	if float(_state.arrival_remaining) > 0.000000001:
		return
	var entrance := _point(_configuration.floor.entrance)
	var door_motion := {}
	var entrance_guest := {}
	if Doorway.enabled(_configuration.floor):
		var lanes := _entrance_lanes()
		# A blocked doorway is outside admission: do not spawn in furniture.
		if lanes.is_empty(): return
		door_motion = Doorway.motion("enter", "customer-%s" % _state.next_customer_id, _random.state)
		var preferred_lane := Vector2i(4 + roundi(float(door_motion.offset_x)), entrance.y)
		entrance = preferred_lane if lanes.has(preferred_lane) else lanes[0]
		entrance_guest.door_lane = entrance.x
		if lanes.size() == 1: door_motion.offset_x = _offset_for_lane(float(door_motion.offset_x), entrance.x)
	# A new arrival never materializes inside an existing visitor at the door.
	for customer in _state.customers:
		if customer.has("door_motion") or customer.phase == "entrance_wait" or _render_position(customer).distance_to(Vector2(entrance)) < _customer_number("personal_space"):
			return
	var choices := _arrival_seat_choices(entrance_guest)
	var preferred := ""
	var choice: Dictionary = {}
	if not choices.is_empty():
		# Keep the established random draw order for immediate admissions.
		preferred = _preference_for(choices)
		choice = _choose_useful_seat(choices, preferred)
	var customer := {
		"id": "customer-%s" % _state.next_customer_id,
		"x": float(entrance.x), "y": float(entrance.y),
		"seat_id": "", "phase": "entrance_wait",
		"path": [], "path_index": 0,
		"meal_dish": null, "meal_elapsed": 0.0,
		"appearance": _random.randi_range(0, 3),
		"facing": "south", "visual_phase": "stand", "visual_elapsed": 0.0,
	}
	_new_visit_fields(customer)
	if entrance_guest.has("door_lane"): customer.door_lane = entrance.x
	_initialize_navigation(customer, Vector2(entrance))
	if not choice.is_empty():
		_assign_arrival_seat(customer, choice, preferred)
	if Doorway.enabled(_configuration.floor):
		customer.door_motion = door_motion
	_state.next_customer_id += 1
	_state.customers.append(customer)
	_state.stats.arrivals += 1
	events.append({"type": "arrived", "customer_id": customer.id, "seat_id": customer.seat_id, "preferred_recipe_id": preferred})
	var jitter := float(_configuration.service.arrival_jitter_seconds)
	_state.arrival_remaining = float(_configuration.service.arrival_seconds) + _random.randf_range(-jitter, jitter)

func _set_preference(customer: Dictionary, phase: String) -> void:
	if customer.preference_phase != phase:
		customer.preference_phase = phase
		customer.preference_phase_elapsed = 0.0

func _customer_event(kind: String, customer: Dictionary) -> Dictionary:
	return {"type": kind, "customer_id": customer.id, "seat_id": customer.seat_id, "recipe_id": customer.preferred_recipe_id, "x": customer.x, "y": customer.y}

func _offset_for_lane(sample: float, lane: int) -> float:
	if 4 + roundi(sample) == lane: return sample
	return sample * 0.5 if lane == 4 else 0.5 + sample * 0.5

func _exit_route(customer: Dictionary) -> Dictionary:
	if not Doorway.enabled(_configuration.floor):
		return _route_from_position(customer, _point(_configuration.floor.entrance))
	var sample := float(customer.get("door_exit_offset", Doorway.motion("exit", str(customer.id), _random.state).offset_x))
	var preferred := int(customer.get("door_lane", 4 + roundi(sample))) if customer.has("door_exit_offset") else 4 + roundi(sample)
	var lanes := _entrance_lanes()
	var position := Vector2(float(customer.x), float(customer.y))
	# Try the selected side's front approach before falling back to a sideways
	# route around furniture. Neither side is permanently reserved by the door.
	for direct in [false, true]:
		for lane in [preferred, 9 - preferred]:
			var goal := Vector2i(lane, int(_configuration.floor.entrance.y))
			if not lanes.has(goal): continue
			var apron := goal + Vector2i.DOWN
			var route := {}
			if direct or position.y <= float(goal.y) + 0.000001 or (position.y < float(apron.y) and roundi(position.x) == lane):
				route = _route_from_position(customer, goal)
			elif _object_at(apron).is_empty():
				route = _route_from_position(customer, apron)
				if not route.is_empty(): route.path.append({"x": goal.x, "y": goal.y})
			if route.is_empty(): continue
			route.door_lane = lane
			route.door_exit_offset = _offset_for_lane(sample, lane) if lanes.size() == 1 else sample
			return route
	return {}

func _begin_door_exit(customer: Dictionary) -> void:
	customer.door_motion = Doorway.motion("exit", str(customer.id), _random.state)
	if customer.has("door_exit_offset"): customer.door_motion.offset_x = customer.door_exit_offset
	customer.render_offset_x = 0.0
	customer.render_offset_y = 0.0
	customer.yielding = false
	_clear_seated_route(customer)
	_set_visual(customer, "walk")

func _step_door_motion(customer: Dictionary, delta: float) -> bool:
	var motion: Dictionary = customer.door_motion
	motion.distance = minf(Doorway.TRAVEL, float(motion.distance) + delta * float(_configuration.service.walking_cells_per_second))
	if float(motion.distance) + 0.000000001 < Doorway.TRAVEL: return false
	if motion.direction == "exit": return true
	customer.erase("door_motion")
	return false

func _step_customers(delta: float, events: Array) -> void:
	var departed: Array = []
	for customer in _state.customers:
		customer.layout_pending = false
		if customer.has("door_motion"):
			if _step_door_motion(customer, delta):
				departed.append(customer)
				events.append({"type": "departed", "customer_id": customer.id, "reason": customer.departure_reason})
			continue
		if customer.phase == "standing":
			customer.standing_elapsed = _clock_advance(float(customer.standing_elapsed), delta)
			if not _try_reseat(customer):
				_step_standing(customer, delta)
				continue
		if customer.phase == "entrance_wait":
			# An unadmitted visitor has not started a meal preference or a route.
			# They stay at the door rather than borrowing trapped-guest wandering.
			var choices := _arrival_seat_choices(customer)
			if not choices.is_empty():
				var preferred := _preference_for(choices)
				_assign_arrival_seat(customer, _choose_useful_seat(choices, preferred), preferred)
				events.append(_customer_event("seat_assigned", customer))
			else:
				customer.entrance_wait_elapsed = _clock_advance(float(customer.entrance_wait_elapsed), delta)
				if float(customer.entrance_wait_elapsed) + 0.000000001 >= _customer_number("entrance_wait_seconds"):
					if Doorway.enabled(_configuration.floor):
						customer.phase = "leaving"
						customer.departure_reason = "no_seat"
						customer.entrance_wait_elapsed = 0.0
						_set_visual(customer, "walk")
						_apply_navigation_route(customer, _exit_route(customer))
					else:
						departed.append(customer)
						events.append({"type": "departed", "customer_id": customer.id, "reason": "no_seat"})
			continue
		customer.visual_elapsed = _clock_advance(float(customer.visual_elapsed), delta)
		if customer.navigation_mode == "wander":
			customer.wander_elapsed = _clock_advance(float(customer.wander_elapsed), delta)
		customer.preference_phase_elapsed = _clock_advance(float(customer.preference_phase_elapsed), delta)
		if customer.preference_phase == "satisfied":
			customer.happy_elapsed = customer.preference_phase_elapsed
			if float(customer.happy_elapsed) + 0.000000001 >= _customer_number("happy_seconds"):
				_set_preference(customer, "complete")
		elif customer.preference_phase == "expired" and customer.first_dish_received and float(customer.preference_phase_elapsed) + 0.000000001 >= _customer_number("happy_seconds"):
			_set_preference(customer, "complete")
		match customer.phase:
			"walking", "leaving":
				if customer.visual_phase == "stand-up":
					if float(customer.visual_elapsed) + 0.000000001 >= _transition_seconds("standing_seconds"):
						_set_visual(customer, "walk")
					continue
				if _step_navigation(customer, delta):
					if customer.phase == "leaving":
						if Doorway.enabled(_configuration.floor):
							_begin_door_exit(customer)
						else:
							departed.append(customer)
							events.append({"type": "departed", "customer_id": customer.id, "reason": customer.departure_reason})
					else:
						customer.phase = "eating" if customer.meal_dish != null else "waiting"
						_clear_seated_route(customer)
						customer.facing = _object_by_id(customer.seat_id).facing
						customer.render_offset_x = 0.0
						customer.render_offset_y = 0.0
						_set_visual(customer, "eat" if customer.meal_dish != null else "sit-down" if _transition_seconds("sitting_seconds") > 0.0 else "seated-wait")
			"waiting":
				if customer.visual_phase == "sit-down":
					if float(customer.visual_elapsed) + 0.000000001 < _transition_seconds("sitting_seconds"):
						continue
					_set_visual(customer, "seated-wait")
				if customer.preference_phase == "pending":
					# A manually admitted door guest chooses their preference only in Live.
					if not customer.visit_legacy and customer.preferred_recipe_id.is_empty():
						var service := _seat_service(_object_by_id(customer.seat_id))
						var recipes: Array = service.ready + service.menu
						if recipes.is_empty(): recipes = _state.recipe_book.discovered.duplicate()
						if recipes.is_empty(): continue
						recipes.sort()
						customer.preferred_recipe_id = str(recipes[_random.randi_range(0, recipes.size() - 1)])
					_set_preference(customer, "active")
				if customer.preference_phase == "active":
					customer.preference_elapsed = minf(_customer_number("preference_seconds"), _clock_advance(float(customer.preference_elapsed), delta))
					if float(customer.preference_elapsed) + 0.000000001 >= _customer_number("preference_seconds"):
						_set_preference(customer, "expired")
						events.append(_customer_event("preference_expired", customer))
				var seat := _object_by_id(customer.seat_id)
				var tile := _facing_object(seat)
				if tile.get("kind") == "belt" and tile.dish != null and (customer.preference_phase != "active" or tile.dish.recipe_id == customer.preferred_recipe_id):
					_take_dish(customer, seat, tile, events)
					continue
				customer.waiting_elapsed = _clock_advance(float(customer.waiting_elapsed), delta)
				if not customer.restless and float(customer.waiting_elapsed) + 0.000000001 >= _customer_number("restless_seconds"):
					customer.restless = true
					events.append(_customer_event("customer_restless", customer))
				if float(customer.waiting_elapsed) + 0.000000001 >= _customer_number("leave_seconds"):
					_begin_leaving(customer, "unfed")
					events.append(_customer_event("visit_abandoned", customer))
			"eating":
				customer.meal_elapsed = _clock_advance(float(customer.meal_elapsed), delta)
				if float(customer.meal_elapsed) + 0.000000001 >= float(customer.meal_duration):
					_finish_meal(customer, events)
	for customer in departed:
		_state.customers.erase(customer)

func _take_dish(customer: Dictionary, seat: Dictionary, tile: Dictionary, events: Array) -> void:
	var matched: bool = not customer.first_dish_received and customer.preference_phase == "active" and tile.dish.recipe_id == customer.preferred_recipe_id
	customer.meal_dish = tile.dish
	customer.meal_elapsed = 0.0
	customer.meal_duration = float(_configuration.service.eating_seconds)
	customer.meal_fullness = 1.0
	if not customer.visit_legacy:
		var jitter := _customer_number("eating_jitter_seconds")
		customer.meal_duration += _random.randf_range(-jitter, jitter)
		customer.meal_fullness = _random.randf_range(_customer_number("dish_fullness_min"), _customer_number("dish_fullness_max"))
	customer.first_dish_received = true
	customer.waiting_elapsed = 0.0
	customer.restless = false
	customer.phase = "eating"
	_set_visual(customer, "eat")
	if matched:
		_set_preference(customer, "satisfied")
		customer.happy_elapsed = 0.0
		events.append(_customer_event("preference_matched", customer))
	elif not customer.preference_phase in ["satisfied", "expired"]:
		_set_preference(customer, "complete")
	var source_belt := tile.duplicate(true)
	source_belt.travel_progress = clampf(float(tile.travel_elapsed)/float(_configuration.service.belt_seconds_per_cell),0,1)
	tile.dish = null
	tile.travel_elapsed = 0.0
	events.append({"type": "eating_started", "customer_id": customer.id, "dish_id": customer.meal_dish.id, "recipe_id": customer.meal_dish.recipe_id, "seat_id": seat.id, "source_belt":source_belt, "taken_at":float(_state.elapsed)})

func _begin_leaving(customer: Dictionary, reason: String) -> void:
	customer.phase = "leaving"
	customer.departure_reason = reason
	customer.yielding = false
	_set_visual(customer, "stand-up" if _transition_seconds("standing_seconds") > 0.0 else "walk")
	_replan_navigation(customer)

func _finish_meal(customer: Dictionary, events: Array) -> void:
	var dish: Dictionary = customer.meal_dish
	var price := int(_configuration.recipes[dish.recipe_id].price)
	_state.coins += price
	_state.stats.sales += 1
	_state.stats.served += 1
	customer.fullness += customer.meal_fullness
	# Consume and credit together: no reward is left pending in a save.
	customer.meal_dish = null
	customer.meal_elapsed = 0.0
	customer.meal_fullness = 0.0
	if customer.visit_legacy or float(customer.fullness) + 0.000000001 >= float(customer.appetite_target):
		_begin_leaving(customer, "satisfied")
	else:
		customer.phase = "waiting"
		customer.waiting_elapsed = 0.0
		customer.restless = false
		_set_visual(customer, "seated-wait")
	events.append({
		"type": "sale", "customer_id": customer.id, "seat_id": customer.seat_id,
		"dish_id": dish.id, "recipe_id": dish.recipe_id, "price": price,
		"x": customer.x, "y": customer.y,
	})

func _render_position(customer: Dictionary) -> Vector2:
	return Vector2(float(customer.x) + float(customer.render_offset_x), float(customer.y) + float(customer.render_offset_y))

func _foot_on_floor(position: Vector2, seat_id: String, objects: Array, floor_data: Dictionary) -> bool:
	var cell := Vector2i(floori(position.x + 0.5), floori(position.y + 0.5))
	if not _inside(cell, floor_data):
		return false
	for object in objects:
		if _point(object) == cell:
			return object.kind == "seat" and object.id == seat_id
	return true

func _walking_position_clear(position: Vector2, customer: Dictionary) -> bool:
	# Guests can pass through each other. Only furniture and floor boundaries
	# constrain walking, so another visitor can never deadlock a valid route.
	return _foot_on_floor(position, customer.seat_id, _state.objects, _configuration.floor)

func _initialize_navigation(customer: Dictionary, origin: Vector2) -> void:
	customer.navigation_mode = "goal"
	customer.wander_elapsed = 0.0
	customer.path_origin = {"x": origin.x, "y": origin.y}
	customer.navigation_retry_elapsed = 0.0
	customer.wander_cursor = 0

func _migrate_navigation(state: Dictionary, config: Dictionary) -> void:
	for customer in state.customers:
		var origin := _point(config.floor.entrance)
		if customer.phase == "leaving":
			for object in state.objects:
				if object.id == customer.seat_id:
					origin = _point(object)
					break
		_initialize_navigation(customer, Vector2(origin))
		if customer.phase in ["waiting", "eating"]:
			_clear_seated_route(customer)

func _clear_seated_route(customer: Dictionary) -> void:
	customer.navigation_mode = "goal"
	customer.wander_elapsed = 0.0
	customer.path_origin = {"x": customer.x, "y": customer.y}
	customer.path = []
	customer.path_index = 0
	customer.navigation_retry_elapsed = 0.0

func _navigation_speed(customer: Dictionary) -> float:
	var speed := float(_configuration.service.walking_cells_per_second)
	return speed * _customer_number("wander_speed_multiplier") if customer.navigation_mode == "wander" else speed

func _navigation_goal(customer: Dictionary) -> Vector2i:
	if customer.phase == "standing": return Vector2i(roundi(customer.x), roundi(customer.y))
	return Doorway.anchor(customer, _configuration.floor) if customer.phase == "leaving" else _point(_object_by_id(customer.seat_id))

func _navigation_anchors(customer: Dictionary) -> Array[Vector2i]:
	# The centerline lies on a cardinal segment. Replanning may reverse to its
	# previous cell, but must never round/teleport a fractional foot position.
	var position := Vector2(float(customer.x), float(customer.y))
	var candidates: Array[Vector2i] = []
	for x in [floori(position.x), ceili(position.x)]:
		for y in [floori(position.y), ceili(position.y)]:
			var cell := Vector2i(x, y)
			if candidates.has(cell) or not _inside(cell, _configuration.floor):
				continue
			if absf(position.x - x) > 0.000001 and absf(position.y - y) > 0.000001:
				continue
			var occupant := _object_at(cell)
			if not occupant.is_empty() and not (occupant.kind == "seat" and occupant.id == customer.seat_id and Vector2(cell).distance_to(position) < 0.5):
				continue
			var clear := true
			for fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
				if not _foot_on_floor(position.lerp(Vector2(cell), fraction), customer.seat_id, _state.objects, _configuration.floor):
					clear = false
					break
			if clear:
				candidates.append(cell)
	return candidates

func _route_from_position(customer: Dictionary, goal: Vector2i, goal_id: String = "") -> Dictionary:
	var position := Vector2(float(customer.x), float(customer.y))
	var best := {}
	var best_length := INF
	for anchor in _navigation_anchors(customer):
		var route := _walk_path(anchor, goal, goal_id)
		if route.is_empty() and anchor != goal:
			continue
		var length := position.distance_to(Vector2(anchor)) + route.size()
		if length + 0.000001 >= best_length:
			continue
		if position.distance_to(Vector2(anchor)) > 0.000001:
			route.push_front({"x": anchor.x, "y": anchor.y})
		best = {"path": route, "origin": {"x": position.x, "y": position.y}}
		best_length = length
	return best

func _apply_navigation_route(customer: Dictionary, route: Dictionary) -> void:
	if route.has("door_lane"):
		customer.door_lane = route.door_lane
		customer.door_exit_offset = route.door_exit_offset
	customer.path = route.path
	customer.path_origin = route.origin
	customer.path_index = 0

func _try_goal_route(customer: Dictionary) -> bool:
	var goal_id := "" if customer.phase == "leaving" else str(customer.seat_id)
	var route := _exit_route(customer) if customer.phase == "leaving" else _route_from_position(customer, _navigation_goal(customer), goal_id)
	if route.is_empty():
		return false
	_apply_navigation_route(customer, route)
	customer.navigation_mode = "goal"
	customer.wander_elapsed = 0.0
	customer.navigation_retry_elapsed = 0.0
	return true

func _try_reachable_exit(customer: Dictionary) -> bool:
	# A blocked seat does not trap a visitor who can still reach the door.
	# Decide only in Live: furniture edits may change routes while every visit
	# phase, animation and clock remains frozen for the player's review.
	if customer.phase != "walking" or _state.mode != "live":
		return false
	if customer.meal_dish != null: return false
	var route := _exit_route(customer)
	if route.is_empty():
		return false
	# A newly reopened seat still takes priority over abandoning the visit.
	if _try_goal_route(customer):
		return true
	customer.phase = "leaving"
	customer.departure_reason = "seat_unreachable"
	customer.yielding = false
	# The visitor is already on their feet, possibly between tile centers.
	# Playing stand-up here would invent a seated pose and invalidate the save.
	_apply_navigation_route(customer, route)
	customer.navigation_mode = "goal"
	customer.wander_elapsed = 0.0
	customer.navigation_retry_elapsed = 0.0
	return true

func _choose_wander_route(customer: Dictionary) -> void:
	var position := Vector2(float(customer.x), float(customer.y))
	var reachable := {}
	var blocked := {}
	for object in _state.objects:
		blocked[_point(object)] = true
	# Each of the at most two adjacent anchors needs one flood fill. Keep the
	# predecessor maps, then reconstruct only the selected target's route.
	for anchor in _navigation_anchors(customer):
		var frontier: Array[Vector2i] = [anchor]
		var previous := {anchor: anchor}
		var lengths := {anchor: position.distance_to(Vector2(anchor))}
		var cursor := 0
		while cursor < frontier.size():
			var cell := frontier[cursor]
			cursor += 1
			var length := float(lengths[cell])
			if not reachable.has(cell) or length + 0.000001 < float(reachable[cell].length):
				reachable[cell] = {"length": length, "anchor": anchor, "previous": previous}
			for offset in DIRECTIONS.values():
				var neighbor: Vector2i = cell + offset
				if previous.has(neighbor) or not _inside(neighbor, _configuration.floor) or blocked.has(neighbor):
					continue
				previous[neighbor] = cell
				lengths[neighbor] = length + 1.0
				frontier.append(neighbor)
	var choices: Array[Vector2i] = []
	# Preserve stable row order independently of flood-fill and Dictionary order.
	for y in range(int(_configuration.floor.rows)):
		for x in range(int(_configuration.floor.columns)):
			var target := Vector2i(x, y)
			if reachable.has(target) and not blocked.has(target) and position.distance_to(Vector2(target)) >= 0.75:
				choices.append(target)
	customer.wander_cursor += 1
	if choices.is_empty():
		# One reachable tile is a legitimate trap. Stay on it and retry forever;
		# an empty wander route never counts as reaching the seat or entrance.
		_apply_navigation_route(customer, {"path": [], "origin": {"x": customer.x, "y": customer.y}})
		return
	var index := posmod((int(customer.wander_cursor) - 1) * 17 + _id_index(customer.id, "customer-") * 11, choices.size())
	var target := choices[index]
	var record: Dictionary = reachable[target]
	var route: Array = []
	var cell := target
	while cell != record.anchor:
		route.push_front({"x": cell.x, "y": cell.y})
		cell = record.previous[cell]
	if position.distance_to(Vector2(record.anchor)) > 0.000001:
		route.push_front({"x": record.anchor.x, "y": record.anchor.y})
	_apply_navigation_route(customer, {"path": route, "origin": {"x": position.x, "y": position.y}})

func _replan_navigation(customer: Dictionary) -> void:
	if customer.get("door_motion", {}).get("direction") == "exit": return
	if customer.phase == "standing":
		_clear_seated_route(customer)
		return
	var was_wandering: bool = customer.navigation_mode == "wander"
	if _try_goal_route(customer):
		return
	if _try_reachable_exit(customer):
		return
	customer.navigation_mode = "wander"
	if not was_wandering:
		customer.wander_elapsed = 0.0
	customer.navigation_retry_elapsed = 0.0
	_choose_wander_route(customer)

func _step_navigation(customer: Dictionary, delta: float) -> bool:
	# Check an escape before taking even one more wandering step. This also
	# repairs a saved older visit on its first Live step without mutating it
	# during restore or waiting for the normal seat-retry interval.
	if customer.navigation_mode == "wander":
		_try_reachable_exit(customer)
	if customer.navigation_mode == "wander":
		customer.navigation_retry_elapsed = _clock_advance(float(customer.navigation_retry_elapsed), delta)
		if float(customer.navigation_retry_elapsed) + 0.000000001 >= _customer_number("wander_retry_seconds"):
			customer.navigation_retry_elapsed = 0.0
			_try_goal_route(customer)
		if customer.navigation_mode == "wander" and int(customer.path_index) >= customer.path.size():
			_choose_wander_route(customer)
	var finished := _walk_with_traffic(customer, delta)
	return finished and customer.navigation_mode == "goal"

func _walk_with_traffic(customer: Dictionary, delta: float) -> bool:
	var candidate: Dictionary = customer.duplicate(true)
	var finished := _walk_customer(candidate, delta)
	var direction: Vector2i = DIRECTIONS[candidate.facing]
	var right := Vector2(-direction.y, direction.x)
	var desired := right * _customer_number("passing_offset")
	var goal := _navigation_goal(customer)
	# Small simulation fixtures retain their cell-edge departure boundary.
	# The restaurant reaches its selected doorway lane before walking outside.
	if not Doorway.enabled(_configuration.floor) and customer.phase == "leaving" and customer.navigation_mode == "goal" and Vector2(float(candidate.x), float(candidate.y)).distance_to(Vector2(goal)) <= 0.5:
		return true
	# Return to the anchor when arriving at a seat or exiting through the door.
	desired *= minf(1.0, Vector2(float(candidate.x), float(candidate.y)).distance_to(Vector2(goal)))
	var offset := Vector2(float(customer.render_offset_x), float(customer.render_offset_y)).move_toward(desired, delta * _navigation_speed(customer))
	candidate.render_offset_x = offset.x
	candidate.render_offset_y = offset.y
	if _walking_position_clear(_render_position(candidate), customer):
		for field in ["x", "y", "path_index", "facing", "render_offset_x", "render_offset_y"]:
			customer[field] = candidate[field]
		customer.yielding = false
		return finished
	# Keep a passing offset off furniture when turning around a corner.
	# Centerline path progress is retained, so a save can resume either state.
	customer.yielding = true
	for sign_value in [1.0, -1.0]:
		var side: Vector2 = right * _customer_number("passing_offset") * 2.0 * sign_value
		var retreat := Vector2(float(customer.render_offset_x), float(customer.render_offset_y)).move_toward(side, delta * _navigation_speed(customer))
		var position := Vector2(float(customer.x), float(customer.y)) + retreat
		if _walking_position_clear(position, customer):
			customer.render_offset_x = retreat.x
			customer.render_offset_y = retreat.y
			break
	return false

func _direction_toward(position: Vector2, target: Vector2) -> String:
	var movement := target - position
	if absf(movement.x) > absf(movement.y):
		return "east" if movement.x > 0.0 else "west"
	return "south" if movement.y > 0.0 else "north"

func _walk_customer(customer: Dictionary, delta: float) -> bool:
	var distance := delta * _navigation_speed(customer)
	while distance > 0.0 and int(customer.path_index) < customer.path.size():
		var point: Dictionary = customer.path[int(customer.path_index)]
		var target := Vector2(float(point.x), float(point.y))
		var position := Vector2(float(customer.x), float(customer.y))
		var remaining := position.distance_to(target)
		if remaining > 0.000000001:
			customer.facing = _direction_toward(position, target)
		if remaining <= distance + 0.000000001:
			customer.x = target.x
			customer.y = target.y
			customer.path_index += 1
			distance = maxf(0.0, distance - remaining)
		else:
			position = position.move_toward(target, distance)
			customer.x = position.x
			customer.y = position.y
			distance = 0.0
	return int(customer.path_index) >= customer.path.size()

func _walk_path(start: Vector2i, goal: Vector2i, goal_object_id: String = "") -> Array:
	var frontier: Array[Vector2i] = [start]
	var previous: Dictionary = {start: start}
	var cursor := 0
	while cursor < frontier.size():
		var position := frontier[cursor]
		cursor += 1
		if position == goal:
			var result: Array = []
			var cell := goal
			while cell != start:
				result.push_front({"x": cell.x, "y": cell.y})
				cell = previous[cell]
			return result
		for offset in DIRECTIONS.values():
			var neighbor: Vector2i = position + offset
			if not _inside(neighbor, _configuration.floor) or previous.has(neighbor):
				continue
			var occupant := _object_at(neighbor)
			if not occupant.is_empty() and not (neighbor == goal and occupant.id == goal_object_id):
				continue
			previous[neighbor] = position
			frontier.append(neighbor)
	return []

func _seat_reserved(seat_id: String, excluding_customer: String = "") -> bool:
	if seat_id.is_empty():
		return false
	for customer in _state.customers:
		if customer.id == excluding_customer: continue
		if customer.seat_id == seat_id and (customer.phase != "leaving" or customer.visual_phase == "stand-up"):
			return true
	return false

func _object_by_id(object_id: String) -> Dictionary:
	for object in _state.objects:
		if object.id == object_id:
			return object
	return {}

func _object_at(cell: Vector2i) -> Dictionary:
	for object in _state.objects:
		if int(object.x) == cell.x and int(object.y) == cell.y:
			return object
	return {}

func _facing_object(object: Dictionary) -> Dictionary:
	if object.is_empty():
		return {}
	return _object_at(Vector2i(int(object.x), int(object.y)) + DIRECTIONS[object.facing])

func _point(value: Dictionary) -> Vector2i:
	return Vector2i(int(value.x), int(value.y))

func _inside(cell: Vector2i, floor_data: Dictionary) -> bool:
	return cell.x >= 0 and cell.y >= int(floor_data.get("backdrop_rows", 0)) and cell.x < int(floor_data.columns) and cell.y < int(floor_data.rows)

func _merge_configuration(base: Dictionary, override_values: Dictionary) -> Dictionary:
	var result := base.duplicate(true)
	for key in override_values:
		if override_values[key] is Dictionary and result.get(key) is Dictionary:
			result[key] = _merge_configuration(result[key], override_values[key])
		else:
			result[key] = override_values[key].duplicate(true) if override_values[key] is Array or override_values[key] is Dictionary else override_values[key]
	return result

func _finite_number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value))

func _nonnegative_integer(value: Variant) -> bool:
	return _finite_number(value) and float(value) >= 0.0 and float(value) <= MAX_EXACT_INTEGER and float(value) == floor(float(value))

func _valid_configuration(config: Dictionary) -> bool:
	for field in ["floor", "recipes", "service"]:
		if not config.get(field) is Dictionary:
			return false
	if config.floor.has("viewport_columns") and (not _nonnegative_integer(config.floor.viewport_columns) or float(config.floor.viewport_columns) < 1.0):
		return false
	if not config.get("objects") is Array or not _nonnegative_integer(config.get("starting_coins")):
		return false
	for field in ["columns", "rows", "world_columns"]:
		if not _nonnegative_integer(config.floor.get(field)) or float(config.floor[field]) < 1.0:
			return false
	if config.floor.has("backdrop_rows") and (not _nonnegative_integer(config.floor.backdrop_rows) or int(config.floor.backdrop_rows) >= int(config.floor.rows)):
		return false
	if not _valid_point(config.floor.get("entrance"), config.floor):
		return false
	for field in ["step_seconds", "belt_seconds_per_cell", "arrival_seconds", "walking_cells_per_second", "eating_seconds"]:
		if not _finite_number(config.service.get(field)) or float(config.service[field]) <= 0.0:
			return false
	for field in ["first_arrival_seconds", "arrival_jitter_seconds"]:
		if not _finite_number(config.service.get(field)) or float(config.service[field]) < 0.0:
			return false
	for field in ["loading_seconds", "sitting_seconds", "standing_seconds"]:
		if config.service.has(field) and (not _finite_number(config.service[field]) or float(config.service[field]) < 0.0):
			return false
	if float(config.service.arrival_jitter_seconds) >= float(config.service.arrival_seconds):
		return false
	if config.recipes.is_empty():
		return false
	for recipe in config.recipes.values():
		if not recipe is Dictionary or not recipe.get("name") is String:
			return false
		if not _nonnegative_integer(recipe.get("price")) or not _finite_number(recipe.get("preparation_seconds")):
			return false
		if float(recipe.preparation_seconds) <= 0.0:
			return false
	if config.has("customers") and not _valid_customer_rules(config.customers, config.service):
		return false
	return _valid_objects(config.objects, config)

func _valid_objects(objects: Array, config: Dictionary) -> bool:
	var ids: Dictionary = {}
	var cells: Dictionary = {}
	for object in objects:
		if not object is Dictionary or not object.get("id") is String or object.id.is_empty() or ids.has(object.id):
			return false
		if not object.get("kind") in ["chef", "belt", "seat", "decor"] or not DIRECTIONS.has(object.get("facing")):
			return false
		if not _valid_point(object, config.floor):
			return false
		var cell := _point(object)
		if cells.has(cell) or (not Doorway.enabled(config.floor) and cell == _point(config.floor.entrance)):
			return false
		if object.kind == "chef" and (not object.get("recipe_id") is String or (object.recipe_id != "" and not config.recipes.has(object.recipe_id))):
			return false
		if object.kind == "decor" and not object.get("art_id") in DECOR_ART_IDS:
			return false
		if object.kind == "chef" and object.has("art_id") and not object.art_id in CHEF_ART_IDS:
			return false
		ids[object.id] = true
		cells[cell] = true
	return true

func _valid_point(value: Variant, floor_data: Dictionary) -> bool:
	if not value is Dictionary or not _nonnegative_integer(value.get("x")) or not _nonnegative_integer(value.get("y")):
		return false
	return _inside(_point(value), floor_data)

func _migrate_visual_state(state: Dictionary) -> void:
	# Version 1 saves predate explicit animation clocks. Their gameplay state
	# stays authoritative; do not replay sitting, loading or completed sales.
	var objects: Variant = state.get("objects")
	var customers: Variant = state.get("customers")
	if not objects is Array or not customers is Array:
		return
	var seats := {}
	for object in objects:
		if not object is Dictionary:
			continue
		if object.get("kind") == "seat":
			seats[object.get("id", "")] = object
		if object.get("kind") != "chef":
			continue
		if not object.has("loading_elapsed"):
			object.loading_elapsed = 0.0
		if not object.has("visual_phase"):
			object.visual_phase = "hold" if object.get("held_dish") != null else "work"
		if not object.has("visual_elapsed"):
			object.visual_elapsed = object.get("preparation_elapsed", 0.0) if object.visual_phase == "work" else 0.0
	for customer in customers:
		if not customer is Dictionary:
			continue
		var phase: Variant = customer.get("phase")
		if not customer.has("visual_phase"):
			customer.visual_phase = "eat" if phase == "eating" else "seated-wait" if phase == "waiting" else "walk"
		if not customer.has("visual_elapsed"):
			customer.visual_elapsed = customer.get("meal_elapsed", 0.0) if phase == "eating" else 0.0
		if not customer.has("facing"):
			var seat: Dictionary = seats.get(customer.get("seat_id", ""), {})
			customer.facing = seat.get("facing", "south")
			if customer.visual_phase == "walk" and _finite_number(customer.get("x")) and _finite_number(customer.get("y")) and customer.get("path") is Array and _nonnegative_integer(customer.get("path_index")):
				var index := int(customer.path_index)
				if index < customer.path.size():
					var target: Variant = customer.path[index]
					if target is Dictionary and _finite_number(target.get("x")) and _finite_number(target.get("y")):
						customer.facing = _direction_toward(Vector2(float(customer.x), float(customer.y)), Vector2(float(target.x), float(target.y)))

func _migrate_belt_motion(state: Dictionary) -> void:
	# Earlier saves charged blocked clocks while drawing those dishes at their
	# source centers. Keep that visible position, but retain any real crossing
	# toward an empty belt. The motion marker prevents repeating this migration.
	var belts := {}
	for object in state.objects:
		if object.kind == "belt":
			belts[_point(object)] = object
	for tile in belts.values():
		var destination: Dictionary = belts.get(_point(tile) + DIRECTIONS[tile.facing], {})
		if destination.is_empty() or destination.dish != null:
			tile.travel_elapsed = 0.0

func _id_index(value: Variant, prefix: String) -> int:
	if not value is String or not value.begins_with(prefix):
		return 0
	var suffix: String = value.trim_prefix(prefix)
	if not suffix.is_valid_int():
		return 0
	var index := int(suffix)
	return index if index > 0 and index <= MAX_EXACT_INTEGER and str(index) == suffix else 0

func _valid_dish(value: Variant, recipes: Dictionary, dish_ids: Dictionary) -> bool:
	if value == null:
		return true
	if not value is Dictionary or _id_index(value.get("id"), "dish-") == 0 or not recipes.has(value.get("recipe_id")):
		return false
	if dish_ids.has(value.id):
		return false
	dish_ids[value.id] = true
	return true

func _valid_saved_state(state: Dictionary, config: Dictionary, navigation_version: int = CUSTOMER_NAVIGATION_VERSION, admission_version: int = CUSTOMER_ADMISSION_VERSION) -> bool:
	if not _valid_editor_state(state, config):
		return false
	for field in ["coins", "step_index", "next_customer_id", "next_dish_id"]:
		if not _nonnegative_integer(state.get(field)):
			return false
	if not _finite_number(state.get("elapsed")) or not _finite_number(state.get("arrival_remaining")):
		return false
	if float(state.elapsed) < 0.0 or float(state.arrival_remaining) < 0.0:
		return false
	if absf(float(state.elapsed) - int(state.step_index) * float(config.service.step_seconds)) > 0.000001:
		return false
	if not state.get("camera") is Dictionary or not state.get("stats") is Dictionary or not state.get("entrance_open") is bool:
		return false
	if not _finite_number(state.camera.get("x")) or not _finite_number(state.camera.get("y")):
		return false
	for field in ["sales", "served", "arrivals"]:
		if not _nonnegative_integer(state.stats.get(field)):
			return false
	if int(state.stats.sales) != int(state.stats.served) or int(state.next_customer_id) != int(state.stats.arrivals) + 1:
		return false
	if not state.get("objects") is Array or not state.get("customers") is Array or not _valid_objects(state.objects, config):
		return false
	if int(state.stats.arrivals) < state.customers.size():
		return false
	var dish_ids: Dictionary = {}
	var seats: Dictionary = {}
	var occupants: Dictionary = {}
	var owned_objects: Array = state.objects.duplicate()
	for entry in state.inventory:
		if entry.kind == "chef" and not entry.assigned:
			owned_objects.append(entry.stored_object)
	for object in owned_objects:
		if state.objects.has(object):
			occupants[_point(object)] = object
		if object.kind == "chef":
			if not object.has("held_dish") or not _valid_dish(object.held_dish, config.recipes, dish_ids):
				return false
			var duration := RecipeBook.seconds(config.recipes.get(object.recipe_id, {}), object)
			if not _finite_number(object.get("preparation_elapsed")) or float(object.preparation_elapsed) < 0.0 or float(object.preparation_elapsed) > duration:
				return false
			if not object.get("visual_phase") in ["work", "hold", "load", "idle"] or not _finite_number(object.get("visual_elapsed")) or float(object.visual_elapsed) < 0.0:
				return false
			if not _finite_number(object.get("loading_elapsed")) or float(object.loading_elapsed) < 0.0:
				return false
			if object.held_dish != null:
				if object.held_dish.recipe_id != object.recipe_id or absf(float(object.preparation_elapsed) - duration) > 0.000001 or object.visual_phase == "work":
					return false
			elif not object.visual_phase in ["work", "idle"]:
				return false
			if object.visual_phase == "load":
				var load_seconds := float(config.service.get("loading_seconds", 0.0))
				if load_seconds <= 0.0 or float(object.loading_elapsed) >= load_seconds or absf(float(object.visual_elapsed) - float(object.loading_elapsed)) > 0.000001:
					return false
			elif float(object.loading_elapsed) != 0.0:
				return false
		elif object.kind == "belt":
			if not object.has("dish") or not _valid_dish(object.dish, config.recipes, dish_ids):
				return false
			if not _finite_number(object.get("travel_elapsed")) or float(object.travel_elapsed) < 0.0 or float(object.travel_elapsed) > float(config.service.belt_seconds_per_cell):
				return false
			if object.dish == null and float(object.travel_elapsed) != 0.0:
				return false
		elif object.kind == "seat":
			seats[object.id] = object
	var customer_ids: Dictionary = {}
	var reservations: Dictionary = {}
	var entrance_wait_reserved := false
	for customer in state.customers:
		if not customer is Dictionary or not Doorway.valid(customer, config.floor) or _id_index(customer.get("id"), "customer-") == 0 or customer_ids.has(customer.id):
			return false
		if _id_index(customer.id, "customer-") >= int(state.next_customer_id):
			return false
		customer_ids[customer.id] = true
		var entrance_wait: bool = admission_version > 0 and customer.get("phase") == "entrance_wait"
		if entrance_wait:
			if entrance_wait_reserved or not _valid_entrance_wait(customer, config):
				return false
			entrance_wait_reserved = true
		elif customer.get("phase") == "standing":
			if customer.get("seat_id") != "": return false
		elif customer.get("phase") == "leaving" and customer.get("seat_id") == "":
			if customer.get("visual_phase") != "walk": return false
		elif not seats.has(customer.get("seat_id")) or not customer.get("phase") in ["walking", "waiting", "eating", "leaving"]:
			return false
		if not customer.get("layout_pending") is bool or not _finite_number(customer.get("standing_elapsed")) or float(customer.standing_elapsed) < 0.0: return false
		if admission_version > 0 and (not _finite_number(customer.get("entrance_wait_elapsed")) or (not entrance_wait and float(customer.entrance_wait_elapsed) != 0.0)):
			return false
		if admission_version > 0 and (not _finite_number(customer.get("wander_elapsed")) or float(customer.wander_elapsed) < 0.0 or (customer.get("navigation_mode") != "wander" and float(customer.wander_elapsed) != 0.0)):
			return false
		if not _valid_visit(customer, config):
			return false
		if not DIRECTIONS.has(customer.get("facing")) or not _finite_number(customer.get("visual_elapsed")) or float(customer.visual_elapsed) < 0.0:
			return false
		var allowed_visuals: Array = {"standing": ["stand", "walk"], "entrance_wait": ["stand"], "walking": ["walk"], "waiting": ["sit-down", "seated-wait"], "eating": ["eat"], "leaving": ["stand-up", "walk"]}[customer.phase]
		if not customer.get("visual_phase") in allowed_visuals:
			return false
		if customer.visual_phase in ["sit-down", "stand-up"]:
			var seconds := float(config.service.get("sitting_seconds" if customer.visual_phase == "sit-down" else "standing_seconds", 0.0))
			if seconds <= 0.0 or float(customer.visual_elapsed) >= seconds:
				return false
		if not entrance_wait and not customer.seat_id.is_empty() and (customer.phase != "leaving" or customer.visual_phase == "stand-up"):
			if reservations.has(customer.seat_id):
				return false
			reservations[customer.seat_id] = true
		if not _finite_number(customer.get("x")) or not _finite_number(customer.get("y")):
			return false
		if not _inside(Vector2i(floori(customer.x), floori(customer.y)), config.floor):
			return false
		if not _nonnegative_integer(customer.get("appearance")) or int(customer.appearance) > 3 or not _nonnegative_integer(customer.get("path_index")):
			return false
		if not customer.get("path") is Array or int(customer.path_index) > customer.path.size():
			return false
		for point in customer.path:
			if not _valid_point(point, config.floor):
				return false
		if entrance_wait:
			if navigation_version == 0 or not _valid_customer_navigation(customer, {}, occupants, config):
				return false
		elif navigation_version == 0:
			if not _valid_legacy_customer_path(customer, seats[customer.seat_id], occupants, config.floor):
				return false
		elif not _valid_customer_navigation(customer, seats.get(customer.seat_id, {}), occupants, config):
			return false
		if not _foot_on_floor(Vector2(float(customer.x), float(customer.y)), customer.seat_id, state.objects, config.floor) or not _foot_on_floor(_render_position(customer), customer.seat_id, state.objects, config.floor):
			return false
		if not _finite_number(customer.get("meal_elapsed")) or float(customer.meal_elapsed) < 0.0:
			return false
		if not customer.has("meal_dish") or not _valid_dish(customer.meal_dish, config.recipes, dish_ids):
			return false
		if customer.phase == "eating" and customer.meal_dish == null: return false
		if customer.meal_dish != null:
			if not customer.phase in ["eating", "standing", "walking"]: return false
			if float(customer.meal_elapsed) >= float(customer.meal_duration):
				return false
		elif float(customer.meal_elapsed) != 0.0:
			return false
	# Every produced plate is either still owned by one actor/tile or was sold.
	# Counters must advance past all surviving IDs before new food/visitors spawn.
	if int(state.next_dish_id) != int(state.stats.sales) + int(state.discarded_dishes) + dish_ids.size() + 1:
		return false
	for dish_id in dish_ids:
		if _id_index(dish_id, "dish-") >= int(state.next_dish_id):
			return false
	return true

func _valid_customer_rules(value: Variant, service: Dictionary) -> bool:
	if not value is Dictionary:
		return false
	for key in ["preference_seconds", "happy_seconds", "restless_seconds", "eating_jitter_seconds"]:
		if not _finite_number(value.get(key)) or float(value[key]) < 0.0:
			return false
	if value.has("wander_retry_seconds") and (not _finite_number(value.wander_retry_seconds) or float(value.wander_retry_seconds) <= 0.0):
		return false
	if value.has("wander_speed_multiplier") and (not _finite_number(value.wander_speed_multiplier) or float(value.wander_speed_multiplier) <= 0.0 or float(value.wander_speed_multiplier) > 1.0):
		return false
	if value.has("entrance_wait_seconds") and (not _finite_number(value.entrance_wait_seconds) or float(value.entrance_wait_seconds) <= 0.0):
		return false
	for key in ["leave_seconds", "fullness_min", "fullness_max", "dish_fullness_min", "dish_fullness_max", "passing_offset", "personal_space"]:
		if not _finite_number(value.get(key)) or float(value[key]) <= 0.0:
			return false
	return float(value.restless_seconds) < float(value.leave_seconds) and float(value.fullness_min) <= float(value.fullness_max) and float(value.dish_fullness_min) <= float(value.dish_fullness_max) and float(value.eating_jitter_seconds) < float(service.eating_seconds) and float(value.passing_offset) < 0.5 and float(value.personal_space) <= 2.0 * float(value.passing_offset)

func _migrate_visit_state(state: Dictionary, config: Dictionary) -> void:
	if not state.get("customers") is Array:
		return
	for customer in state.customers:
		if not customer is Dictionary:
			continue
		# Existing visitors finish their original one-plate visit. No new random
		# draws, preference replay, appetite reroll or sale occurs on migration.
		customer.visit_legacy = true
		customer.first_dish_received = customer.get("phase") in ["eating", "leaving"]
		customer.preferred_recipe_id = ""
		customer.preference_phase = "complete"
		customer.preference_elapsed = 0.0
		customer.preference_phase_elapsed = 0.0
		customer.happy_elapsed = 0.0
		customer.waiting_elapsed = 0.0
		customer.restless = false
		customer.yielding = false
		customer.render_offset_x = 0.0
		customer.render_offset_y = 0.0
		customer.fullness = 1.0 if customer.get("phase") == "leaving" else 0.0
		customer.appetite_target = 1.0
		customer.meal_fullness = 1.0 if customer.get("phase") == "eating" else 0.0
		customer.meal_duration = float(config.service.eating_seconds)
		customer.departure_reason = "satisfied" if customer.get("phase") == "leaving" else ""

func _valid_visit(customer: Dictionary, config: Dictionary) -> bool:
	for key in ["visit_legacy", "first_dish_received", "restless", "yielding"]:
		if not customer.get(key) is bool:
			return false
	for key in ["preference_elapsed", "preference_phase_elapsed", "happy_elapsed", "waiting_elapsed", "fullness", "meal_fullness"]:
		if not _finite_number(customer.get(key)) or float(customer[key]) < 0.0:
			return false
	for key in ["appetite_target", "meal_duration"]:
		if not _finite_number(customer.get(key)) or float(customer[key]) <= 0.0:
			return false
	for key in ["render_offset_x", "render_offset_y"]:
		if not _finite_number(customer.get(key)) or absf(float(customer[key])) > float(config.customers.passing_offset) * 2.0 + 0.000001:
			return false
	var pending_admission: bool = customer.get("preferred_recipe_id") == "" and not customer.first_dish_received and customer.get("preference_phase") == "pending" and customer.phase in ["standing", "walking", "waiting", "leaving"]
	if not customer.get("preferred_recipe_id") is String or (not customer.visit_legacy and customer.phase != "entrance_wait" and not pending_admission and not config.recipes.has(customer.preferred_recipe_id)):
		return false
	if not customer.get("preference_phase") in ["pending", "active", "satisfied", "expired", "complete"]:
		return false
	if not customer.get("departure_reason") in ["", "satisfied", "unfed", "seat_unreachable", "no_seat"]:
		return false
	if customer.departure_reason == "no_seat" and (not Doorway.enabled(config.floor) or customer.seat_id != "" or customer.preferred_recipe_id != "" or customer.first_dish_received): return false
	if (customer.phase == "leaving") != (customer.departure_reason != ""):
		return false
	if customer.first_dish_received and customer.preference_phase in ["pending", "active"]:
		return false
	if customer.preference_phase == "satisfied" and not customer.first_dish_received:
		return false
	var preference_seconds := float(config.customers.preference_seconds)
	if customer.preference_phase == "pending" and float(customer.preference_elapsed) != 0.0:
		return false
	if customer.preference_phase == "active" and float(customer.preference_elapsed) >= preference_seconds:
		return false
	if customer.preference_phase == "expired" and absf(float(customer.preference_elapsed) - preference_seconds) > 0.000001:
		return false
	if customer.get("meal_dish") != null:
		if not customer.first_dish_received or float(customer.meal_fullness) <= 0.0:
			return false
	elif float(customer.meal_fullness) != 0.0:
		return false
	if customer.visit_legacy:
		return customer.appetite_target == 1.0 and customer.preference_phase == "complete" and customer.preferred_recipe_id == "" and float(customer.meal_duration) == float(config.service.eating_seconds)
	if float(customer.appetite_target) < float(config.customers.fullness_min) or float(customer.appetite_target) > float(config.customers.fullness_max):
		return false
	if customer.phase != "leaving" and float(customer.fullness) + 0.000000001 >= float(customer.appetite_target):
		return false
	if customer.get("meal_dish") != null and (float(customer.meal_fullness) < float(config.customers.dish_fullness_min) or float(customer.meal_fullness) > float(config.customers.dish_fullness_max)):
		return false
	return absf(float(customer.meal_duration) - float(config.service.eating_seconds)) <= float(config.customers.eating_jitter_seconds) + 0.000001

func _valid_entrance_wait(customer: Dictionary, config: Dictionary) -> bool:
	if customer.get("seat_id") != "" or customer.get("visit_legacy") != false or customer.get("first_dish_received") != false or customer.get("preferred_recipe_id") != "" or customer.get("preference_phase") != "pending":
		return false
	for key in ["x", "y"]:
		if not _finite_number(customer.get(key)) or absf(float(customer[key]) - float(customer.get("door_lane", config.floor.entrance.x) if key == "x" else config.floor.entrance.y)) > 0.000001:
			return false
	for key in ["preference_elapsed", "preference_phase_elapsed", "happy_elapsed", "waiting_elapsed", "fullness", "meal_fullness", "meal_elapsed", "render_offset_x", "render_offset_y", "visual_elapsed"]:
		if not _finite_number(customer.get(key)) or float(customer[key]) != 0.0:
			return false
	if customer.get("meal_dish") != null or customer.get("restless") != false or customer.get("yielding") != false or customer.get("departure_reason") != "":
		return false
	return _finite_number(customer.get("entrance_wait_elapsed")) and float(customer.entrance_wait_elapsed) >= 0.0 and float(customer.entrance_wait_elapsed) < float(config.customers.entrance_wait_seconds)

func _valid_customer_navigation(customer: Dictionary, seat: Dictionary, occupants: Dictionary, config: Dictionary) -> bool:
	if not customer.get("navigation_mode") in ["goal", "wander"]:
		return false
	if not _nonnegative_integer(customer.get("wander_cursor")):
		return false
	if not _finite_number(customer.get("navigation_retry_elapsed")) or float(customer.navigation_retry_elapsed) < 0.0 or float(customer.navigation_retry_elapsed) >= float(config.customers.wander_retry_seconds):
		return false
	if customer.navigation_mode == "goal" and float(customer.navigation_retry_elapsed) != 0.0:
		return false
	var origin: Variant = customer.get("path_origin")
	if not origin is Dictionary or not _finite_number(origin.get("x")) or not _finite_number(origin.get("y")):
		return false
	var previous := Vector2(float(origin.x), float(origin.y))
	if previous.x < 0.0 or previous.y < 0.0 or previous.x > int(config.floor.columns) - 1 or previous.y > int(config.floor.rows) - 1:
		return false
	if absf(previous.x - roundf(previous.x)) > 0.000001 and absf(previous.y - roundf(previous.y)) > 0.000001:
		return false
	var position := Vector2(float(customer.x), float(customer.y))
	var goal := Doorway.anchor(customer, config.floor) if customer.phase in ["leaving", "entrance_wait"] else Vector2i(roundi(customer.x), roundi(customer.y)) if customer.phase == "standing" else _point(seat)
	var index := int(customer.path_index)
	if customer.phase == "standing" and customer.navigation_mode == "goal":
		return customer.path.is_empty() and index == 0 and previous.distance_to(position) <= 0.000001
	if customer.phase in ["waiting", "eating", "entrance_wait"]:
		return customer.navigation_mode == "goal" and customer.path.is_empty() and index == 0 and previous.distance_to(Vector2(goal)) <= 0.000001 and position.distance_to(Vector2(goal)) <= 0.000001
	var segment_start := previous
	var segment_end := previous
	for point_index in range(customer.path.size()):
		var cell := _point(customer.path[point_index])
		var target := Vector2(cell)
		var distance := absf(target.x - previous.x) + absf(target.y - previous.y)
		# Only the first segment may begin between tile centers. All later
		# segments remain exact cardinal neighbors, including traversed history.
		if (absf(target.x - previous.x) > 0.000001 and absf(target.y - previous.y) > 0.000001) or distance <= 0.000001 or distance > 1.000001 or (point_index > 0 and absf(distance - 1.0) > 0.000001):
			return false
		if point_index >= index and occupants.has(cell):
			var destination_seat: bool = customer.navigation_mode == "goal" and customer.phase == "walking" and cell == goal and occupants[cell].id == seat.id
			var starting_seat: bool = point_index == 0 and occupants[cell].id == seat.id and previous.distance_to(target) < 0.5
			if not destination_seat and not starting_seat:
				return false
		if point_index == index:
			segment_start = previous
			segment_end = target
		previous = target
	if index == customer.path.size():
		segment_start = previous
		segment_end = previous
	if customer.navigation_mode == "goal" and previous.distance_to(Vector2(goal)) > 0.000001:
		return false
	if customer.navigation_mode == "wander" and customer.phase not in ["walking", "leaving", "standing"]:
		return false
	if customer.phase == "walking" and customer.navigation_mode == "goal" and index >= customer.path.size():
		return false
	if customer.visual_phase == "stand-up" and position.distance_to(Vector2(_point(seat))) > 0.000001:
		return false
	return position.x >= minf(segment_start.x, segment_end.x) - 0.000001 and position.x <= maxf(segment_start.x, segment_end.x) + 0.000001 and position.y >= minf(segment_start.y, segment_end.y) - 0.000001 and position.y <= maxf(segment_start.y, segment_end.y) + 0.000001

func _valid_legacy_customer_path(customer: Dictionary, seat: Dictionary, occupants: Dictionary, floor_data: Dictionary) -> bool:
	var leaving: bool = customer.phase == "leaving"
	var start := _point(seat) if leaving else _point(floor_data.entrance)
	var goal := _point(floor_data.entrance) if leaving else _point(seat)
	var previous := start
	for point in customer.path:
		var cell := _point(point)
		if absi(cell.x - previous.x) + absi(cell.y - previous.y) != 1:
			return false
		if occupants.has(cell) and not (cell == goal and not leaving and occupants[cell].id == seat.id):
			return false
		previous = cell
	if previous != goal:
		return false
	var index := int(customer.path_index)
	if customer.phase in ["waiting", "eating"] and index != customer.path.size():
		return false
	if customer.phase == "walking" and index == customer.path.size():
		return false
	var segment_start := start if index == 0 else _point(customer.path[index - 1])
	var segment_end := segment_start if index == customer.path.size() else _point(customer.path[index])
	var position := Vector2(float(customer.x), float(customer.y))
	return position.x >= minf(segment_start.x, segment_end.x) - 0.000001 and position.x <= maxf(segment_start.x, segment_end.x) + 0.000001 and position.y >= minf(segment_start.y, segment_end.y) - 0.000001 and position.y <= maxf(segment_start.y, segment_end.y) + 0.000001

func _editor_definition() -> Dictionary:
	if _editor_content.is_empty():
		var loaded: Variant = JSON.parse_string(FileAccess.get_file_as_string(EDITOR_PATH))
		if loaded is Dictionary:
			_editor_content = loaded
	return _editor_content

func _initialize_editor_state(state: Dictionary) -> void:
	# Versioned migration adds owned exhibition supplies once. It does not buy,
	# debit, refund, advance service, change the layout or reset an existing meal.
	var definition := _editor_definition()
	state.mode = "live"
	state.editor = {"layer": definition.get("default_layer", "layout"), "tray_open": true, "selected_id": "", "page": 0, "pages": {"people": 0, "layout": 0, "floor": 0}}
	state.editor.belt_path = []
	state.inventory = definition.get("inventory", []).duplicate(true)
	state.next_object_id = 1
	state.discarded_dishes = 0
	for object in state.objects:
		if object.kind == "chef":
			state.inventory.append({"id": object.id, "kind": "chef", "name": object.get("name", "Chef"), "art_id": object.get("art_id", "chef-lena"), "recipe_id": object.recipe_id, "count": 0, "assigned": true, "facing": object.facing, "stored_object": null})

func _inventory_snapshot() -> Array:
	var result: Array = []
	for entry in _state.inventory:
		var item: Dictionary = entry.duplicate(true)
		item.erase("stored_object")
		result.append(item)
	return result

func _inventory_item(identity: String) -> Dictionary:
	for entry in _state.inventory:
		if entry.id == identity:
			return entry
	return {}

func _editor_layer_for(object: Dictionary) -> String:
	return "people" if object.kind == "chef" else "floor" if object.kind == "floor" else "layout"

func _editor_entries(layer: String, inventory: Array) -> Array:
	return inventory.filter(func(entry): return _editor_layer_for(entry) == layer)

func _editor_page_count(layer: String, inventory: Array) -> int:
	var page_size := int(_editor_definition().get("page_sizes", {}).get(layer, 3))
	return maxi(1, int(ceil(float(_editor_entries(layer, inventory).size()) / maxi(1, page_size))))

func _migrate_editor_paging(state: Dictionary, old_version: int) -> bool:
	# v1 used People 3 / Layout 2 / Floor 2; v2 used three in every layer.
	# Preserve the page containing the prior first visible item. Validate every
	# old page before conversion so malformed saves cannot become valid.
	if not state.get("editor") is Dictionary or not state.get("inventory") is Array:
		return false
	var editor: Dictionary = state.editor
	if not editor.get("layer") in EDITOR_LAYERS or not editor.get("pages") is Dictionary or not _nonnegative_integer(editor.get("page")):
		return false
	if not _nonnegative_integer(editor.pages.get(editor.layer)) or int(editor.page) != int(editor.pages[editor.layer]):
		return false
	for entry in state.inventory:
		if not entry is Dictionary or not entry.get("kind") in ["chef", "belt", "seat", "decor", "floor"]: return false
	for layer in EDITOR_LAYERS:
		var old_size := 3 if old_version == 2 or layer == "people" else 2
		var entry_count := _editor_entries(layer, state.inventory).size()
		var old_count := maxi(1, int(ceil(float(entry_count) / old_size)))
		if not _nonnegative_integer(editor.pages.get(layer)) or int(editor.pages[layer]) >= old_count:
			return false
		var page_size := maxi(1, int(_editor_definition().get("page_sizes", {}).get(layer, 3)))
		editor.pages[layer] = mini(int(floor(float(int(editor.pages[layer]) * old_size) / page_size)), _editor_page_count(layer, state.inventory) - 1)
	editor.page = editor.pages[editor.layer]
	return true

func _valid_editor_state(state: Dictionary, config: Dictionary) -> bool:
	if not state.get("mode") in ["live", "edit"] or not state.get("editor") is Dictionary or not state.get("inventory") is Array:
		return false
	if not _nonnegative_integer(state.get("next_object_id")) or int(state.next_object_id) < 1 or not _nonnegative_integer(state.get("discarded_dishes")):
		return false
	var editor: Dictionary = state.editor
	if not editor.get("layer") in EDITOR_LAYERS or not editor.get("tray_open") is bool or not editor.get("selected_id") is String or not editor.get("pages") is Dictionary:
		return false
	if editor.has("scrolls"):
		if not editor.scrolls is Dictionary: return false
		for layer in editor.scrolls:
			var offset: Variant = editor.scrolls[layer]
			if not layer in EDITOR_LAYERS or not (offset is float or offset is int) or not is_finite(float(offset)) or offset<0 or offset>100000: return false
	if not _nonnegative_integer(editor.get("page")):
		return false
	var objects: Variant = state.get("objects")
	if not objects is Array or not _valid_objects(objects, config):
		return false
	if not BeltRoutes.valid(objects) or not editor.get("belt_path") is Array: return false
	var placed: Dictionary = {}
	for object in objects:
		if not object is Dictionary or not object.get("id") is String:
			return false
		placed[object.id] = object
		if _id_index(object.id, "editor-object-") >= int(state.next_object_id):
			return false
	if not editor.selected_id.is_empty() and not placed.has(editor.selected_id):
		if editor.layer != "people" or not state.get("customers") is Array or not state.customers.any(func(guest): return guest is Dictionary and guest.get("id") == editor.selected_id and _customer_rescuable(guest)):
			return false
	var path_seen := {}
	var previous := ""
	for identity in editor.belt_path:
		if not identity is String or path_seen.has(identity) or not placed.has(identity) or placed[identity].kind != "belt": return false
		if not previous.is_empty() and placed[previous].next_id != identity: return false
		path_seen[identity] = true
		previous = identity
	if not previous.is_empty() and (editor.selected_id != previous or state.mode != "edit" or editor.layer != "layout"): return false
	var inventory_ids := {}
	var known_chefs := {}
	for initial in config.objects:
		if initial.kind == "chef":
			known_chefs[initial.id] = initial
	for id in state.get("staff",{}).get("hired",{}): known_chefs[id] = {}
	var known_stock := {}
	for entry in _editor_definition().get("inventory", []):
		known_stock[entry.id] = entry
	for entry in state.inventory:
		if not entry is Dictionary or not entry.get("id") is String or inventory_ids.has(entry.id) or not _nonnegative_integer(entry.get("count")):
			return false
		inventory_ids[entry.id] = true
		if entry.get("kind") == "chef":
			if not known_chefs.has(entry.id):
				return false
			if not entry.get("assigned") is bool or not entry.get("name") is String or not entry.get("art_id") in CHEF_ART_IDS or not entry.get("recipe_id") is String or (entry.recipe_id != "" and not config.recipes.has(entry.recipe_id)) or not DIRECTIONS.has(entry.get("facing")):
				return false
			if entry.assigned:
				if int(entry.count) != 0 or entry.get("stored_object") != null or not placed.has(entry.id) or placed[entry.id].get("kind") != "chef":
					return false
			else:
				if int(entry.count) != 1 or placed.has(entry.id) or not entry.get("stored_object") is Dictionary:
					return false
				if entry.stored_object.get("id") != entry.id or entry.stored_object.get("kind") != "chef" or not _valid_objects([entry.stored_object], config):
					return false
		elif known_stock.has(entry.id):
			for key in known_stock[entry.id]:
				if key != "count" and entry.get(key) != known_stock[entry.id][key]:
					return false
		else:
			return false
	for identity in known_stock:
		if not inventory_ids.has(identity):
			return false
		var expected := int(known_stock[identity].count)
		var owned := 0
		for initial in config.objects:
			if _owned_stock_id(initial) == identity:
				expected += 1
		for object in objects:
			if _owned_stock_id(object) == identity:
				owned += 1
		for entry in state.inventory:
			if entry.id == identity:
				owned += int(entry.count)
		if owned != expected:
			return false
	for identity in known_chefs:
		if not inventory_ids.has(identity):
			return false
	for object in objects:
		if object.kind == "chef" and not inventory_ids.has(object.id):
			return false
	for layer in EDITOR_LAYERS:
		if not _nonnegative_integer(editor.pages.get(layer)) or int(editor.pages[layer]) >= _editor_page_count(layer, state.inventory):
			return false
	return int(editor.page) == int(editor.pages[editor.layer])

func _editor_fail(reason: String) -> Dictionary:
	return {"ok": false, "reason": reason}

func _editor_command(request: Dictionary) -> Dictionary:
	if _state.mode != "edit":
		return _editor_fail("edit_required")
	var type: String = str(request.get("type", ""))
	match type:
		"editor_layer":
			if not request.get("layer") in EDITOR_LAYERS:
				return _editor_fail("invalid_layer")
			_state.editor.layer = request.layer
			_state.editor.page = _state.editor.pages[request.layer]
			_state.editor.tray_open = true
			_state.editor.belt_path = []
			if not _customer_by_id(_state.editor.selected_id).is_empty(): _state.editor.selected_id = ""
			var selected := _object_by_id(_state.editor.selected_id)
			if not selected.is_empty() and _editor_layer_for(selected) != request.layer: _state.editor.selected_id = ""
			return {"ok": true}
		"editor_toggle_tray":
			_state.editor.tray_open = not _state.editor.tray_open
			return {"ok": true}
		"editor_page":
			if not _nonnegative_integer(request.get("page")) or int(request.page) >= _editor_page_count(_state.editor.layer, _state.inventory):
				return _editor_fail("invalid_page")
			_state.editor.page = int(request.page)
			_state.editor.pages[_state.editor.layer] = int(request.page)
			return {"ok": true}
		"editor_scroll":
			var offset: Variant = request.get("offset")
			if not (offset is float or offset is int) or not is_finite(float(offset)) or offset<0 or offset>100000:
				return _editor_fail("invalid_scroll")
			if not _state.editor.has("scrolls"): _state.editor.scrolls = {}
			_state.editor.scrolls[_state.editor.layer] = float(offset)
			return {"ok":true}
		"editor_pickup":
			var guest := _customer_by_id(str(request.get("id", "")))
			if guest.is_empty(): return _editor_command({"type":"editor_select", "id":request.get("id")})
			_state.editor.layer = "people"
			_state.editor.page = _state.editor.pages.people
			_state.editor.selected_id = guest.id
			_state.editor.belt_path = []
			return {"ok":true}
		"editor_select":
			var identity: Variant = request.get("id")
			if identity == null or identity == "":
				_state.editor.selected_id = ""
				_state.editor.belt_path = []
				return {"ok": true}
			if not identity is String: return _editor_fail("unknown_object")
			var guest := _customer_by_id(identity)
			if not guest.is_empty():
				if _state.editor.layer != "people": return _editor_fail("people_required")
				if not _customer_rescuable(guest): return _editor_fail("seated_customer")
				_state.editor.selected_id = identity
				_state.editor.belt_path = []
				return {"ok": true}
			if _object_by_id(identity).is_empty():
				return _editor_fail("unknown_object")
			_state.editor.selected_id = identity
			_state.editor.layer = _editor_layer_for(_object_by_id(identity))
			_state.editor.page = _state.editor.pages[_state.editor.layer]
			_state.editor.belt_path = [identity] if _object_by_id(identity).kind == "belt" else []
			return {"ok": true}
		"editor_belt_extend":
			return _extend_belt_path(request)
		"editor_belt_end":
			_state.editor.belt_path = []
			_state.editor.selected_id = ""
			_state.editor.tray_open = true
			return {"ok": true}
		"editor_move", "editor_rotate", "editor_remove", "editor_place":
			if not _customer_by_id(str(request.get("id", ""))).is_empty(): return _editor_customer_change(request)
			return _editor_change(request)
	return _editor_fail("unknown_command")

func _editor_cell_rejection(request: Dictionary, excluding_id: String = "") -> String:
	if not _valid_point(request, _configuration.floor):
		return "invalid_position"
	var cell := _point(request)
	if not Doorway.enabled(_configuration.floor) and cell == _point(_configuration.floor.entrance):
		return "entrance"
	var other := _object_at(cell)
	if not other.is_empty() and other.id != excluding_id:
		return "occupied"
	for customer in _state.customers:
		if customer.seat_id == excluding_id and customer.phase in ["waiting", "eating"]: continue
		var center := Vector2(float(customer.x), float(customer.y))
		var rendered := _render_position(customer)
		if cell == Vector2i(floori(center.x + 0.5), floori(center.y + 0.5)) or cell == Vector2i(floori(rendered.x + 0.5), floori(rendered.y + 0.5)) or Vector2(cell).distance_to(rendered) < 0.65:
			if not _customer_displaceable(customer): return "customer_busy"
	return ""

func _belt_target(cell: Vector2i) -> Dictionary:
	var path: Array = _state.editor.belt_path
	var result := {"x": cell.x, "y": cell.y, "kind": "new", "valid": false, "reason": "invalid_position"}
	if path.is_empty(): return result
	var source := _object_by_id(path[-1])
	if source.is_empty() or abs(cell.x - int(source.x)) + abs(cell.y - int(source.y)) != 1: return result
	var target := _object_at(cell)
	if target.get("kind") == "belt":
		result.id = target.id
		result.kind = "close" if target.id == path[0] and path.size() >= 4 else "reuse"
		if path.has(target.id) and result.kind != "close":
			result.reason = "visited_belt"
			return result
		result.valid = true
		result.reason = ""
		return result
	result.reason = _editor_cell_rejection(result)
	if result.reason.is_empty() and int(_inventory_item("belt-tile").count) <= 0: result.reason = "no_belt_tiles"
	result.valid = result.reason.is_empty()
	return result

func _belt_targets() -> Array:
	var path: Array = _state.editor.belt_path
	var result: Array = []
	if path.is_empty(): return result
	var source := _object_by_id(path[-1])
	if source.is_empty(): return result
	for offset in DIRECTIONS.values(): result.append(_belt_target(_point(source) + offset))
	return result

func _extend_belt_path(request: Dictionary) -> Dictionary:
	if _state.editor.belt_path.is_empty(): return _editor_fail("no_belt_path")
	if not _valid_point(request, _configuration.floor): return _editor_fail("invalid_position")
	var candidate := _belt_target(_point(request))
	if not candidate.valid: return _editor_fail(candidate.reason)
	var before := _state.duplicate(true)
	var path: Array = _state.editor.belt_path.duplicate()
	var source := _object_by_id(path[-1])
	var target := _object_at(_point(request))
	if target.is_empty():
		var placed := _editor_change({"type": "editor_place", "inventory_id": "belt-tile", "x": request.x, "y": request.y, "facing": BeltRoutes.direction(_point(request) - _point(source))})
		if not placed.ok: return placed
		target = _object_by_id(placed.id)
	BeltRoutes.connect_tiles(_state.objects, source, target)
	path.append(target.id)
	_state.editor.belt_path = [] if candidate.kind == "close" else path
	_state.editor.selected_id = target.id
	# Reusing a neighbor can replace the input of an earlier route. A path
	# cursor only retains the still-connected suffix; every old tile survives.
	while _state.editor.belt_path.size() > 1:
		var ids: Array = _state.editor.belt_path
		var broken := -1
		for index in range(ids.size() - 1):
			if _object_by_id(ids[index]).next_id != ids[index + 1]: broken = index
		if broken < 0: break
		_state.editor.belt_path = ids.slice(broken + 1)
	if not _valid_saved_state(_state, _configuration):
		_state = before
		_rebuild_access()
		return _editor_fail("invalid_state")
	return {"ok": true, "id": target.id, "reused": candidate.kind != "new", "closed": candidate.kind == "close"}

func _editor_change(request: Dictionary) -> Dictionary:
	var type: String = str(request.type)
	var object: Dictionary = {}
	var stock: Dictionary = {}
	if type == "editor_place":
		if not request.get("inventory_id") is String:
			return _editor_fail("unknown_inventory")
		stock = _inventory_item(request.inventory_id)
		if stock.is_empty():
			return _editor_fail("unknown_inventory")
		if stock.kind == "floor":
			return _editor_fail("unsupported_floor")
		if int(stock.count) <= 0:
			return _editor_fail("no_stock")
	else:
		if not request.get("id") is String:
			return _editor_fail("unknown_object")
		object = _object_by_id(request.id)
		if object.is_empty():
			return _editor_fail("unknown_object")
	if type in ["editor_move", "editor_place"]:
		var reason := _editor_cell_rejection(request, str(object.get("id", "")))
		if not reason.is_empty():
			return _editor_fail(reason)
	if type == "editor_place" and request.has("facing") and not DIRECTIONS.has(request.facing):
		return _editor_fail("invalid_facing")
	if type == "editor_rotate" and request.has("clockwise") and not request.clockwise is bool:
		return _editor_fail("invalid_rotation")
	var before: Dictionary = _state.duplicate(true)
	var carried_progress := float(object.get("travel_elapsed", 0.0))
	var path: Array = _state.editor.belt_path.duplicate()
	if type != "editor_rotate" and type != "editor_remove": _state.editor.belt_path = []
	if type == "editor_rotate" and not path.is_empty() and path[-1] != object.id: _state.editor.belt_path = []
	if object.get("kind") == "belt" and type in ["editor_move", "editor_remove"]:
		BeltRoutes.detach(_state.objects, object)
	if type == "editor_place":
		if stock.kind == "chef":
			object = stock.stored_object.duplicate(true)
			stock.stored_object = null
			stock.assigned = true
		else:
			while not _object_by_id("editor-object-%s" % _state.next_object_id).is_empty():
				_state.next_object_id += 1
			object = {"id": "editor-object-%s" % _state.next_object_id, "kind": stock.kind, "facing": stock.facing, "inventory_id": stock.id}
			_state.next_object_id += 1
			if stock.kind == "belt":
				object.dish = null
				object.travel_elapsed = 0.0
				object.next_id = ""
				object.input_facing = request.get("facing", stock.facing)
			elif stock.kind == "decor":
				object.art_id = stock.art_id
		stock.count -= 1
		object.x = int(request.x)
		object.y = int(request.y)
		if request.has("facing"):
			object.facing = request.facing
		_state.objects.append(object)
	elif type == "editor_move":
		object.x = int(request.x)
		object.y = int(request.y)
	elif type == "editor_rotate":
		var facings := ["north", "east", "south", "west"]
		if object.kind == "belt":
			BeltRoutes.detach(_state.objects, object)
		object.facing = facings[posmod(facings.find(object.facing) + (1 if request.get("clockwise", true) else -1), facings.size())]
		if object.kind == "belt":
			object.input_facing = object.facing
			_state.editor.belt_path = [object.id]
	else:
		var inventory_id := _owned_stock_id(object)
		stock = _inventory_item(inventory_id)
		if stock.is_empty():
			_state = before
			return _editor_fail("unknown_inventory")
		stock.count += 1
		if object.kind == "chef":
			stock.assigned = false
			stock.facing = object.facing
			stock.stored_object = object.duplicate(true)
		elif object.kind == "belt" and object.dish != null:
			_state.discarded_dishes += 1
		_state.objects.erase(object)
	if type == "editor_place" and object.kind == "chef" and _facing_object(object).get("kind") != "belt":
		# An unassigned chef needs a usable neighboring counter; movement of an
		# already assigned chef may intentionally leave them temporarily idle.
		if not request.has("facing"):
			for facing in DIRECTIONS:
				object.facing = facing
				if _facing_object(object).get("kind") == "belt":
					break
		if _facing_object(object).get("kind") != "belt":
			_state = before
			return _editor_fail("no_belt")
	# A moved tile retains its owned plate and transfer clock. Its detached
	# endpoint holds the plate at the new root until a route is connected.
	if type in ["editor_move", "editor_rotate"] and object.kind == "belt":
		object.travel_elapsed = carried_progress if type == "editor_move" else 0.0
		for other in _state.objects:
			if other.kind == "belt" and other.next_id == object.id:
				other.travel_elapsed = 0.0
	if type in ["editor_move", "editor_rotate"] and object.kind == "chef" and object.visual_phase == "load":
		object.loading_elapsed = 0.0
		object.visual_phase = "hold"
		object.visual_elapsed = 0.0
	_state.editor.selected_id = "" if type == "editor_remove" else object.id
	if type == "editor_place" and object.kind == "belt": _state.editor.belt_path = [object.id]
	elif type == "editor_remove":
		if not path.is_empty() and path[-1] == object.id:
			path.pop_back()
			_state.editor.belt_path = path
			_state.editor.selected_id = "" if path.is_empty() else path[-1]
		else: _state.editor.belt_path = []
	if type != "editor_remove":
		_state.editor.layer = _editor_layer_for(object)
		_state.editor.page = _state.editor.pages[_state.editor.layer]
	# Routes belong to a visitor's current position, not the tiles they already
	# crossed. A valid furniture edit may strand a visitor; keep the visit and
	# its original goal, and let Live find room to wander until access returns.
	_rebuild_access()
	_carry_or_release_seat(object, type)
	if type != "editor_remove" and not _resolve_customer_overlaps(object):
		_state = before
		_rebuild_access()
		return _editor_fail("no_customer_space")
	for customer in _state.customers:
		if customer.phase in ["walking", "leaving"]:
			_replan_navigation(customer)
		else:
			_clear_seated_route(customer)
	if not _valid_saved_state(_state, _configuration):
		_state = before
		_rebuild_access()
		return _editor_fail("invalid_state")
	return {"ok": true, "id": object.id}

func _initialize_customer_layout(customer: Dictionary) -> void:
	customer.layout_pending = false
	customer.standing_elapsed = 0.0

func _customer_by_id(identity: String) -> Dictionary:
	for customer in _state.customers:
		if customer.id == identity: return customer
	return {}

func _customer_rescuable(customer: Dictionary) -> bool:
	return customer.get("phase") in ["entrance_wait", "standing", "walking", "waiting", "eating", "leaving"]

func _customer_displaceable(customer: Dictionary) -> bool:
	# Furniture still cannot silently displace a seated customer. Explicit
	# guest pickup is a separate operation that leaves their stool in place.
	return customer.get("phase") in ["standing", "walking", "leaving"] and customer.get("visual_phase") != "stand-up"

func _customer_touches(customer: Dictionary, cell: Vector2i) -> bool:
	var center := Vector2(float(customer.x), float(customer.y))
	var rendered := _render_position(customer)
	return cell == Vector2i(floori(center.x + 0.5), floori(center.y + 0.5)) or cell == Vector2i(floori(rendered.x + 0.5), floori(rendered.y + 0.5)) or Vector2(cell).distance_to(rendered) < 0.65

func _empty_customer_cell(cell: Vector2i, excluding: String = "") -> bool:
	if not _inside(cell, _configuration.floor) or (not Doorway.enabled(_configuration.floor) and cell == _point(_configuration.floor.entrance)) or not _object_at(cell).is_empty(): return false
	return not _state.customers.any(func(guest): return guest.id != excluding and _customer_touches(guest, cell))

func _nearest_customer_cell(customer: Dictionary) -> Dictionary:
	var best := {}
	var distance := INF
	var origin := Vector2(float(customer.x), float(customer.y))
	for y in range(int(_configuration.floor.rows)):
		for x in range(int(_configuration.floor.columns)):
			var cell := Vector2i(x, y)
			var candidate := origin.distance_squared_to(Vector2(cell))
			if candidate + 0.000001 < distance and _empty_customer_cell(cell, customer.id):
				best = {"x": x, "y": y}
				distance = candidate
	return best

func _stand_customer(customer: Dictionary) -> void:
	customer.erase("door_motion")
	customer.seat_id = ""
	if customer.phase != "leaving": customer.phase = "standing"
	customer.render_offset_x = 0.0
	customer.render_offset_y = 0.0
	customer.layout_pending = true
	customer.standing_elapsed = 0.0
	customer.entrance_wait_elapsed = 0.0
	customer.yielding = false
	_clear_seated_route(customer)
	_set_visual(customer, "walk" if customer.phase == "leaving" else "stand")

func _seat_customer(customer: Dictionary, seat: Dictionary) -> void:
	customer.seat_id = seat.id
	customer.x = float(seat.x)
	customer.y = float(seat.y)
	customer.facing = seat.facing
	customer.render_offset_x = 0.0
	customer.render_offset_y = 0.0
	customer.standing_elapsed = 0.0
	customer.yielding = false
	_clear_seated_route(customer)
	if customer.phase == "leaving":
		_set_visual(customer, "stand-up" if _transition_seconds("standing_seconds") > 0.0 else "walk")
		_replan_navigation(customer)
	else:
		customer.phase = "eating" if customer.meal_dish != null else "waiting"
		_set_visual(customer, "eat" if customer.meal_dish != null else "seated-wait")

func _carry_or_release_seat(object: Dictionary, type: String) -> void:
	if object.get("kind") != "seat" or type == "editor_place": return
	for customer in _state.customers:
		if customer.seat_id != object.id: continue
		if type == "editor_remove":
			_stand_customer(customer)
		elif customer.phase in ["waiting", "eating"] or customer.visual_phase == "stand-up":
			# The action and all visit/meal clocks remain on their current frame.
			customer.x = float(object.x)
			customer.y = float(object.y)
			customer.facing = object.facing
			customer.render_offset_x = 0.0
			customer.render_offset_y = 0.0

func _resolve_customer_overlaps(object: Dictionary) -> bool:
	for customer in _state.customers:
		if not _customer_touches(customer, _point(object)): continue
		if customer.seat_id == object.id and (customer.phase in ["waiting", "eating"] or customer.visual_phase == "stand-up"): continue
		if not _customer_displaceable(customer): return false
		if object.kind == "seat" and not _seat_reserved(object.id, customer.id) and _facing_object(object).get("kind") == "belt":
			_seat_customer(customer, object)
			customer.layout_pending = true
			continue
		var cell := _nearest_customer_cell(customer)
		if cell.is_empty(): return false
		customer.x = float(cell.x)
		customer.y = float(cell.y)
		_stand_customer(customer)
	return true

func _editor_customer_change(request: Dictionary) -> Dictionary:
	if _state.editor.layer != "people": return _editor_fail("people_required")
	var customer := _customer_by_id(str(request.get("id", "")))
	if request.type != "editor_move" or not _customer_rescuable(customer): return _editor_fail("seated_customer")
	if not _valid_point(request, _configuration.floor): return _editor_fail("invalid_position")
	var cell := _point(request)
	if not Doorway.enabled(_configuration.floor) and cell == _point(_configuration.floor.entrance): return _editor_fail("entrance")
	var object := _object_at(cell)
	if not object.is_empty() and (object.kind != "seat" or _seat_reserved(object.id, customer.id)): return _editor_fail("occupied")
	if _state.customers.any(func(guest): return guest.id != customer.id and _customer_touches(guest, cell)): return _editor_fail("customer_busy")
	var before := _state.duplicate(true)
	customer.erase("door_motion")
	customer.x = float(cell.x)
	customer.y = float(cell.y)
	customer.render_offset_x = 0.0
	customer.render_offset_y = 0.0
	customer.layout_pending = true
	customer.standing_elapsed = 0.0
	customer.entrance_wait_elapsed = 0.0
	if not object.is_empty():
		_seat_customer(customer, object)
	elif customer.phase in ["standing", "waiting", "eating", "entrance_wait"] or customer.visual_phase == "stand-up":
		_stand_customer(customer)
		if customer.phase == "leaving": _replan_navigation(customer)
	else:
		_replan_navigation(customer)
	_state.editor.selected_id = customer.id if _customer_rescuable(customer) else ""
	if not _valid_saved_state(_state, _configuration):
		_state = before
		return _editor_fail("invalid_state")
	return {"ok": true, "id": customer.id}

func _try_reseat(customer: Dictionary) -> bool:
	var best := {}
	var best_route := {}
	var length := INF
	for seat in _state.objects:
		if seat.kind != "seat" or _seat_reserved(seat.id) or _facing_object(seat).get("kind") != "belt": continue
		var route := _route_from_position(customer, _point(seat), seat.id)
		if route.is_empty(): continue
		var distance := 0.0
		var previous := Vector2(float(customer.x), float(customer.y))
		for point in route.path:
			var target := Vector2(float(point.x), float(point.y))
			distance += previous.distance_to(target)
			previous = target
		if distance < length:
			best = seat
			best_route = route
			length = distance
	if best.is_empty(): return false
	if best_route.path.is_empty():
		_seat_customer(customer, best)
	else:
		customer.seat_id = best.id
		customer.phase = "walking"
		customer.navigation_mode = "goal"
		customer.navigation_retry_elapsed = 0.0
		customer.wander_elapsed = 0.0
		_apply_navigation_route(customer, best_route)
		_set_visual(customer, "walk")
	return true

func _step_standing(customer: Dictionary, delta: float) -> void:
	customer.visual_elapsed = _clock_advance(float(customer.visual_elapsed), delta)
	var trapped := _exit_route(customer).is_empty()
	if not trapped:
		_clear_seated_route(customer)
		if customer.visual_phase != "stand": _set_visual(customer, "stand")
		return
	if customer.navigation_mode != "wander":
		customer.navigation_mode = "wander"
		customer.wander_elapsed = 0.0
		_choose_wander_route(customer)
	customer.wander_elapsed = _clock_advance(float(customer.wander_elapsed), delta)
	if int(customer.path_index) >= customer.path.size(): _choose_wander_route(customer)
	if customer.visual_phase != "walk": _set_visual(customer, "walk")
	_walk_with_traffic(customer, delta)

func _owned_stock_id(object: Dictionary) -> String:
	match object.kind:
		"chef":
			return str(object.id)
		"belt":
			return "belt-tile"
		"seat":
			return "stool-plain"
		"decor":
			return str(object.art_id)
	return ""
