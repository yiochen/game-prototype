class_name GameSession
extends RefCounted
## The restaurant's public command / elapsed-time / save boundary.
## There is no wall clock or file I/O here. A caller decides when time passes.

const SAVE_VERSION := 1
const CONTENT_PATH := "res://content/starter.json"
const DIRECTIONS := {
	"north": Vector2i(0, -1), "east": Vector2i(1, 0),
	"south": Vector2i(0, 1), "west": Vector2i(-1, 0),
}

var _configuration: Dictionary = {}
var _state: Dictionary = {}
var _random := RandomNumberGenerator.new()
var _remainder := 0.0

static func new_session(seed_value: int = 1, configuration: Dictionary = {}) -> GameSession:
	var session := GameSession.new()
	var defaults: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONTENT_PATH))
	if not defaults is Dictionary:
		push_error("The restaurant starter content could not be read.")
		return null
	session._configuration = session._merge_configuration(defaults, configuration)
	if not session._valid_configuration(session._configuration):
		push_error("The restaurant starter configuration is invalid.")
		return null
	session._random.seed = seed_value
	session._start()
	return session

func command(request: Dictionary) -> Dictionary:
	match request.get("type", ""):
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
	if not is_finite(elapsed) or elapsed <= 0.0 or _state.is_empty():
		return events
	var step := float(_configuration.service.step_seconds)
	_remainder += elapsed
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
		"floor": _configuration.floor.duplicate(true),
		"recipes": _configuration.recipes.duplicate(true),
		"objects": [],
		"customers": [],
		"stats": _state.stats.duplicate(true),
	}
	for original in _state.objects:
		var object: Dictionary = original.duplicate(true)
		if object.kind == "chef":
			object.preparation_seconds = _configuration.recipes[object.recipe_id].preparation_seconds
			object.preparation = clampf(float(object.preparation_elapsed) / float(object.preparation_seconds), 0.0, 1.0)
			object.erase("preparation_elapsed")
		elif object.kind == "belt":
			object.travel_progress = clampf(float(object.travel_elapsed) / float(_configuration.service.belt_seconds_per_cell), 0.0, 1.0)
			object.erase("travel_elapsed")
		result.objects.append(object)
	for customer in _state.customers:
		result.customers.append({
			"id": customer.id, "x": customer.x, "y": customer.y,
			"seat_id": customer.seat_id, "phase": customer.phase,
			"meal_progress": clampf(float(customer.meal_elapsed) / float(_configuration.service.eating_seconds), 0.0, 1.0),
			"meal_dish": customer.meal_dish.duplicate(true) if customer.meal_dish is Dictionary else null,
			"appearance": customer.appearance,
		})
	return result

func save_data() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"configuration": _configuration.duplicate(true),
		"state": _state.duplicate(true),
		"remainder": _remainder,
		# JSON numbers cannot exactly hold a 64-bit generator state.
		"random_state": str(_random.state),
	}

func restore(data: Dictionary) -> bool:
	# Validate before changing anything. Restoring is a state replacement, never
	# elapsed-time simulation or event playback, even when called repeatedly.
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
	if not _valid_saved_state(data.state, data.configuration):
		return false
	_configuration = data.configuration.duplicate(true)
	_state = data.state.duplicate(true)
	_normalize_restored_numbers()
	_remainder = float(data.remainder)
	_random.state = int(data.random_state)
	return true

func _normalize_restored_numbers() -> void:
	# JSON represents integers and floats with the same number type. Normalize
	# counters before future ID creation, and cell coordinates before rendering.
	_configuration.starting_coins = int(_configuration.starting_coins)
	for field in ["columns", "rows", "world_columns"]:
		_configuration.floor[field] = int(_configuration.floor[field])
	for field in ["x", "y"]:
		_configuration.floor.entrance[field] = int(_configuration.floor.entrance[field])
	for recipe in _configuration.recipes.values():
		recipe.price = int(recipe.price)
	for field in ["coins", "step_index", "next_customer_id", "next_dish_id"]:
		_state[field] = int(_state[field])
	for field in _state.stats:
		_state.stats[field] = int(_state.stats[field])
	for objects in [_configuration.objects, _state.objects]:
		for object in objects:
			object.x = int(object.x)
			object.y = int(object.y)
	for customer in _state.customers:
		customer.path_index = int(customer.path_index)
		customer.appearance = int(customer.appearance)
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
			"belt":
				object.travel_elapsed = 0.0
				object.dish = null
	_remainder = 0.0

func _step_chefs(delta: float, events: Array) -> void:
	for chef in _state.objects:
		if chef.kind != "chef":
			continue
		if chef.held_dish == null:
			var duration := float(_configuration.recipes[chef.recipe_id].preparation_seconds)
			chef.preparation_elapsed = minf(duration, float(chef.preparation_elapsed) + delta)
			if float(chef.preparation_elapsed) + 0.000000001 >= duration:
				chef.preparation_elapsed = duration
				chef.held_dish = {"id": "dish-%s" % _state.next_dish_id, "recipe_id": chef.recipe_id}
				_state.next_dish_id += 1
				events.append({"type": "prepared", "chef_id": chef.id, "dish_id": chef.held_dish.id})
		if chef.held_dish != null:
			var loading := _facing_object(chef)
			if loading.get("kind") == "belt" and loading.dish == null:
				loading.dish = chef.held_dish
				loading.travel_elapsed = 0.0
				chef.held_dish = null
				chef.preparation_elapsed = 0.0
				events.append({"type": "loaded", "chef_id": chef.id, "belt_id": loading.id, "dish_id": loading.dish.id})

func _step_belts(delta: float, events: Array) -> void:
	var duration := float(_configuration.service.belt_seconds_per_cell)
	var transfers: Array = []
	var reserved: Dictionary = {}
	# Decide against the same beginning-of-step occupancy. A dish cannot race
	# through multiple tiles just because they occur later in the content array.
	for tile in _state.objects:
		if tile.kind != "belt" or tile.dish == null:
			continue
		tile.travel_elapsed = minf(duration, float(tile.travel_elapsed) + delta)
		if float(tile.travel_elapsed) + 0.000000001 < duration:
			continue
		var destination := _facing_object(tile)
		if destination.get("kind") == "belt" and destination.dish == null and not reserved.has(destination.id):
			transfers.append({"from": tile, "to": destination})
			reserved[destination.id] = true
	for transfer in transfers:
		var source: Dictionary = transfer.from
		var destination: Dictionary = transfer.to
		destination.dish = source.dish
		destination.travel_elapsed = 0.0
		source.dish = null
		source.travel_elapsed = 0.0
		events.append({"type": "belt_moved", "dish_id": destination.dish.id, "from_id": source.id, "to_id": destination.id})

func _step_arrivals(delta: float, events: Array) -> void:
	if not _state.entrance_open:
		return
	_state.arrival_remaining = maxf(0.0, float(_state.arrival_remaining) - delta)
	if float(_state.arrival_remaining) > 0.000000001:
		return
	var entrance := _point(_configuration.floor.entrance)
	var choices: Array = []
	for seat in _state.objects:
		if seat.kind != "seat" or _seat_reserved(seat.id):
			continue
		var path := _walk_path(entrance, Vector2i(int(seat.x), int(seat.y)), seat.id)
		if not path.is_empty():
			choices.append({"seat": seat, "path": path})
	if not choices.is_empty():
		var choice: Dictionary = choices[_random.randi_range(0, choices.size() - 1)]
		var customer := {
			"id": "customer-%s" % _state.next_customer_id,
			"x": float(entrance.x), "y": float(entrance.y),
			"seat_id": choice.seat.id, "phase": "walking",
			"path": choice.path, "path_index": 0,
			"meal_dish": null, "meal_elapsed": 0.0,
			"appearance": _random.randi_range(0, 3),
		}
		_state.next_customer_id += 1
		_state.customers.append(customer)
		_state.stats.arrivals += 1
		events.append({"type": "arrived", "customer_id": customer.id, "seat_id": customer.seat_id})
	var jitter := float(_configuration.service.arrival_jitter_seconds)
	_state.arrival_remaining = float(_configuration.service.arrival_seconds) + _random.randf_range(-jitter, jitter)

func _step_customers(delta: float, events: Array) -> void:
	var departed: Array = []
	for customer in _state.customers:
		match customer.phase:
			"walking", "leaving":
				if _walk_customer(customer, delta):
					if customer.phase == "leaving":
						departed.append(customer)
						events.append({"type": "departed", "customer_id": customer.id})
					else:
						customer.phase = "waiting"
			"waiting":
				var seat := _object_by_id(customer.seat_id)
				var tile := _facing_object(seat)
				if tile.get("kind") == "belt" and tile.dish != null:
					customer.meal_dish = tile.dish
					customer.meal_elapsed = 0.0
					customer.phase = "eating"
					tile.dish = null
					tile.travel_elapsed = 0.0
					events.append({"type": "eating_started", "customer_id": customer.id, "dish_id": customer.meal_dish.id, "seat_id": seat.id})
			"eating":
				customer.meal_elapsed += delta
				if float(customer.meal_elapsed) + 0.000000001 >= float(_configuration.service.eating_seconds):
					_finish_meal(customer, events)
	for customer in departed:
		_state.customers.erase(customer)

func _finish_meal(customer: Dictionary, events: Array) -> void:
	var dish: Dictionary = customer.meal_dish
	var price := int(_configuration.recipes[dish.recipe_id].price)
	_state.coins += price
	_state.stats.sales += 1
	_state.stats.served += 1
	# The dish is consumed in the same state transition that credits its price.
	# Saves contain the resulting state, never a pending sale to replay.
	customer.meal_dish = null
	customer.meal_elapsed = 0.0
	customer.phase = "leaving"
	customer.path = _walk_path(Vector2i(roundi(customer.x), roundi(customer.y)), _point(_configuration.floor.entrance))
	customer.path_index = 0
	events.append({
		"type": "sale", "customer_id": customer.id, "seat_id": customer.seat_id,
		"dish_id": dish.id, "recipe_id": dish.recipe_id, "price": price,
		"x": customer.x, "y": customer.y,
	})

func _walk_customer(customer: Dictionary, delta: float) -> bool:
	var distance := delta * float(_configuration.service.walking_cells_per_second)
	while distance > 0.0 and int(customer.path_index) < customer.path.size():
		var point: Dictionary = customer.path[int(customer.path_index)]
		var target := Vector2(float(point.x), float(point.y))
		var position := Vector2(float(customer.x), float(customer.y))
		var remaining := position.distance_to(target)
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

func _seat_reserved(seat_id: String) -> bool:
	for customer in _state.customers:
		if customer.seat_id == seat_id and customer.phase != "leaving":
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
	return cell.x >= 0 and cell.y >= 0 and cell.x < int(floor_data.columns) and cell.y < int(floor_data.rows)

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
	return _finite_number(value) and float(value) >= 0.0 and float(value) == floor(float(value))

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
	if not _valid_point(config.floor.get("entrance"), config.floor):
		return false
	for field in ["step_seconds", "belt_seconds_per_cell", "arrival_seconds", "walking_cells_per_second", "eating_seconds"]:
		if not _finite_number(config.service.get(field)) or float(config.service[field]) <= 0.0:
			return false
	for field in ["first_arrival_seconds", "arrival_jitter_seconds"]:
		if not _finite_number(config.service.get(field)) or float(config.service[field]) < 0.0:
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
	return _valid_objects(config.objects, config)

func _valid_objects(objects: Array, config: Dictionary) -> bool:
	var ids: Dictionary = {}
	var cells: Dictionary = {}
	for object in objects:
		if not object is Dictionary or not object.get("id") is String or object.id.is_empty() or ids.has(object.id):
			return false
		if not object.get("kind") in ["chef", "belt", "seat"] or not DIRECTIONS.has(object.get("facing")):
			return false
		if not _valid_point(object, config.floor):
			return false
		var cell := _point(object)
		if cells.has(cell) or cell == _point(config.floor.entrance):
			return false
		if object.kind == "chef" and not config.recipes.has(object.get("recipe_id")):
			return false
		ids[object.id] = true
		cells[cell] = true
	return true

func _valid_point(value: Variant, floor_data: Dictionary) -> bool:
	if not value is Dictionary or not _nonnegative_integer(value.get("x")) or not _nonnegative_integer(value.get("y")):
		return false
	return _inside(_point(value), floor_data)

func _valid_dish(value: Variant, recipes: Dictionary, dish_ids: Dictionary) -> bool:
	if value == null:
		return true
	if not value is Dictionary or not value.get("id") is String or not recipes.has(value.get("recipe_id")):
		return false
	if value.id.is_empty() or dish_ids.has(value.id):
		return false
	dish_ids[value.id] = true
	return true

func _valid_saved_state(state: Dictionary, config: Dictionary) -> bool:
	for field in ["coins", "step_index", "next_customer_id", "next_dish_id"]:
		if not _nonnegative_integer(state.get(field)):
			return false
	if not _finite_number(state.get("elapsed")) or not _finite_number(state.get("arrival_remaining")):
		return false
	if float(state.elapsed) < 0.0 or float(state.arrival_remaining) < 0.0:
		return false
	if not state.get("camera") is Dictionary or not state.get("stats") is Dictionary or not state.get("entrance_open") is bool:
		return false
	if not _finite_number(state.camera.get("x")) or not _finite_number(state.camera.get("y")):
		return false
	for field in ["sales", "served", "arrivals"]:
		if not _nonnegative_integer(state.stats.get(field)):
			return false
	if not state.get("objects") is Array or not state.get("customers") is Array or not _valid_objects(state.objects, config):
		return false
	var dish_ids: Dictionary = {}
	var seats: Dictionary = {}
	for object in state.objects:
		if object.kind == "chef":
			if not object.has("held_dish") or not _valid_dish(object.held_dish, config.recipes, dish_ids):
				return false
			if not _finite_number(object.get("preparation_elapsed")) or float(object.preparation_elapsed) < 0.0:
				return false
		elif object.kind == "belt":
			if not object.has("dish") or not _valid_dish(object.dish, config.recipes, dish_ids):
				return false
			if not _finite_number(object.get("travel_elapsed")) or float(object.travel_elapsed) < 0.0:
				return false
		else:
			seats[object.id] = true
	var customer_ids: Dictionary = {}
	var reservations: Dictionary = {}
	for customer in state.customers:
		if not customer is Dictionary or not customer.get("id") is String or customer_ids.has(customer.id):
			return false
		customer_ids[customer.id] = true
		if not seats.has(customer.get("seat_id")) or not customer.get("phase") in ["walking", "waiting", "eating", "leaving"]:
			return false
		if customer.phase != "leaving":
			if reservations.has(customer.seat_id):
				return false
			reservations[customer.seat_id] = true
		if not _finite_number(customer.get("x")) or not _finite_number(customer.get("y")):
			return false
		if not _inside(Vector2i(floori(customer.x), floori(customer.y)), config.floor):
			return false
		if not _nonnegative_integer(customer.get("appearance")) or not _nonnegative_integer(customer.get("path_index")):
			return false
		if not customer.get("path") is Array or int(customer.path_index) > customer.path.size():
			return false
		for point in customer.path:
			if not _valid_point(point, config.floor):
				return false
		if not _finite_number(customer.get("meal_elapsed")) or float(customer.meal_elapsed) < 0.0:
			return false
		if not customer.has("meal_dish") or not _valid_dish(customer.meal_dish, config.recipes, dish_ids):
			return false
		if (customer.phase == "eating") != (customer.meal_dish != null):
			return false
	return true
