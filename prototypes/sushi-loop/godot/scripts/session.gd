class_name GameSession
extends RefCounted
## The restaurant's public command / elapsed-time / save boundary.
## Construction loads tuneable content; rules have no wall clock or persistence.
## A caller decides when time passes and where snapshots are stored.

const SAVE_VERSION := 1
const BELT_MOTION_VERSION := 1
const CUSTOMER_VISIT_VERSION := 1
const CHEF_ART_IDS := ["chef-lena", "chef-omar"]
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
var _access_paths: Dictionary = {}

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
		"floor": _configuration.floor.duplicate(true),
		"recipes": _configuration.recipes.duplicate(true),
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
			"render_offset_x": customer.render_offset_x, "render_offset_y": customer.render_offset_y,
		})
	return result

func save_data() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"belt_motion_version": BELT_MOTION_VERSION,
		"customer_visit_version": CUSTOMER_VISIT_VERSION,
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
	if data.random_state != str(int(data.random_state)):
		return false
	if not _nonnegative_integer(data.get("belt_motion_version", 0)) or int(data.get("belt_motion_version", 0)) > BELT_MOTION_VERSION:
		return false
	if not _nonnegative_integer(data.get("customer_visit_version", 0)) or int(data.get("customer_visit_version", 0)) > CUSTOMER_VISIT_VERSION:
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
	if not _valid_configuration(restored_configuration):
		return false
	var restored_state: Dictionary = data.state.duplicate(true)
	_migrate_visual_state(restored_state)
	if int(data.get("customer_visit_version", 0)) == 0:
		_migrate_visit_state(restored_state, restored_configuration)
	if not _valid_saved_state(restored_state, restored_configuration):
		return false
	if int(data.get("belt_motion_version", 0)) == 0:
		_migrate_belt_motion(restored_state)
	_configuration = restored_configuration
	_state = restored_state
	_normalize_restored_numbers()
	_remainder = float(data.remainder)
	_random.state = int(data.random_state)
	_rebuild_access()
	return true

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
				object.loading_elapsed = 0.0
				object.visual_phase = "work"
				object.visual_elapsed = 0.0
			"belt":
				object.travel_elapsed = 0.0
				object.dish = null
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
			var duration := float(_configuration.recipes[chef.recipe_id].preparation_seconds)
			chef.preparation_elapsed = minf(duration, _clock_advance(float(chef.preparation_elapsed), delta))
			if float(chef.preparation_elapsed) + 0.000000001 >= duration:
				chef.preparation_elapsed = duration
				chef.held_dish = {"id": "dish-%s" % _state.next_dish_id, "recipe_id": chef.recipe_id}
				_state.next_dish_id += 1
				events.append({"type": "prepared", "chef_id": chef.id, "dish_id": chef.held_dish.id})
		if chef.held_dish == null:
			continue
		var loading := _facing_object(chef)
		if loading.get("kind") != "belt" or loading.dish != null:
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
	var reserved: Dictionary = {}
	# Decide against the same beginning-of-step occupancy. A dish cannot race
	# through multiple tiles just because they occur later in the content array.
	for tile in _state.objects:
		if tile.kind != "belt" or tile.dish == null:
			continue
		var destination := _facing_object(tile)
		if destination.get("kind") != "belt":
			# An open endpoint retains its plate at the tile center indefinitely.
			tile.travel_elapsed = 0.0
			continue
		if destination.dish != null:
			# Do not precharge queued motion. A previously started crossing keeps
			# its position if another input fills the target in a merged layout.
			continue
		tile.travel_elapsed = minf(duration, _clock_advance(float(tile.travel_elapsed), delta))
		if float(tile.travel_elapsed) + 0.000000001 < duration:
			continue
		if not reserved.has(destination.id):
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

func _customer_number(key: String) -> float:
	return float(_configuration.get("customers", {}).get(key, 0.0))

func _rebuild_access() -> void:
	_access_paths.clear()
	var entrance := _point(_configuration.floor.entrance)
	for object in _state.objects:
		if object.kind in ["chef", "seat"]:
			_access_paths[object.id] = _walk_path(entrance, _point(object), object.id)

func _chef_service(chef: Dictionary) -> Dictionary:
	if _facing_object(chef).get("kind") != "belt":
		return {"active": false, "reason": "no_belt"}
	if _access_paths.get(chef.id, []).is_empty():
		return {"active": false, "reason": "no_access"}
	return {"active": true, "reason": ""}

func _belt_reaches(source: Dictionary, target_id: String) -> bool:
	var seen := {}
	var tile := source
	while tile.get("kind") == "belt" and not seen.has(tile.id):
		if tile.id == target_id:
			return true
		seen[tile.id] = true
		tile = _facing_object(tile)
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

func _step_arrivals(delta: float, events: Array) -> void:
	if not _state.entrance_open:
		return
	_state.arrival_remaining = maxf(0.0, float(_state.arrival_remaining) - delta)
	if float(_state.arrival_remaining) > 0.000000001:
		return
	var entrance := _point(_configuration.floor.entrance)
	# A new arrival never materializes inside an existing visitor at the door.
	for customer in _state.customers:
		if _render_position(customer).distance_to(Vector2(entrance)) < _customer_number("personal_space"):
			return
	var choices: Array = []
	for seat in _state.objects:
		if seat.kind != "seat" or _seat_reserved(seat.id):
			continue
		var path: Array = _access_paths.get(seat.id, [])
		var service := _seat_service(seat)
		if not path.is_empty() and service.active:
			choices.append({"seat": seat, "path": path, "service": service})
	if not choices.is_empty():
		var preferred := _preference_for(choices)
		var choice: Dictionary = _choose_useful_seat(choices, preferred)
		var customer := {
			"id": "customer-%s" % _state.next_customer_id,
			"x": float(entrance.x), "y": float(entrance.y),
			"seat_id": choice.seat.id, "phase": "walking",
			"path": choice.path.duplicate(true), "path_index": 0,
			"meal_dish": null, "meal_elapsed": 0.0,
			"appearance": _random.randi_range(0, 3),
			"facing": _direction_toward(Vector2(entrance), Vector2(float(choice.path[0].x), float(choice.path[0].y))),
			"visual_phase": "walk", "visual_elapsed": 0.0,
		}
		_new_visit_fields(customer)
		customer.preferred_recipe_id = preferred
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

func _step_customers(delta: float, events: Array) -> void:
	var departed: Array = []
	for customer in _state.customers:
		customer.visual_elapsed = _clock_advance(float(customer.visual_elapsed), delta)
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
				if _walk_with_traffic(customer, delta):
					if customer.phase == "leaving":
						departed.append(customer)
						events.append({"type": "departed", "customer_id": customer.id, "reason": customer.departure_reason})
					else:
						customer.phase = "waiting"
						customer.facing = _object_by_id(customer.seat_id).facing
						customer.render_offset_x = 0.0
						customer.render_offset_y = 0.0
						_set_visual(customer, "sit-down" if _transition_seconds("sitting_seconds") > 0.0 else "seated-wait")
			"waiting":
				if customer.visual_phase == "sit-down":
					if float(customer.visual_elapsed) + 0.000000001 < _transition_seconds("sitting_seconds"):
						continue
					_set_visual(customer, "seated-wait")
				if customer.preference_phase == "pending":
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
	tile.dish = null
	tile.travel_elapsed = 0.0
	events.append({"type": "eating_started", "customer_id": customer.id, "dish_id": customer.meal_dish.id, "recipe_id": customer.meal_dish.recipe_id, "seat_id": seat.id})

func _begin_leaving(customer: Dictionary, reason: String) -> void:
	customer.phase = "leaving"
	customer.departure_reason = reason
	customer.yielding = false
	_set_visual(customer, "stand-up" if _transition_seconds("standing_seconds") > 0.0 else "walk")
	customer.path = _walk_path(Vector2i(roundi(customer.x), roundi(customer.y)), _point(_configuration.floor.entrance))
	customer.path_index = 0

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

func _traffic_clear(position: Vector2, previous: Vector2, customer: Dictionary) -> bool:
	if not _foot_on_floor(position, customer.seat_id, _state.objects, _configuration.floor):
		return false
	var space := _customer_number("personal_space")
	for other in _state.customers:
		if other.id == customer.id:
			continue
		var occupied := _render_position(other)
		if position.distance_to(occupied) + 0.000000001 < space and position.distance_to(occupied) < previous.distance_to(occupied) - 0.000000001:
			return false
	return true

func _walk_with_traffic(customer: Dictionary, delta: float) -> bool:
	var candidate: Dictionary = customer.duplicate(true)
	var finished := _walk_customer(candidate, delta)
	var direction: Vector2i = DIRECTIONS[candidate.facing]
	var right := Vector2(-direction.y, direction.x)
	var desired := right * _customer_number("passing_offset")
	var goal := _point(_configuration.floor.entrance) if customer.phase == "leaving" else _point(_object_by_id(customer.seat_id))
	# Crossing into the entrance cell completes a departure. Requiring its
	# exact center would make outgoing visitors compete with new arrivals.
	if customer.phase == "leaving" and Vector2(float(candidate.x), float(candidate.y)).distance_to(Vector2(goal)) <= 0.5:
		return true
	# Return to the anchor when arriving at a seat or exiting through the door.
	desired *= minf(1.0, Vector2(float(candidate.x), float(candidate.y)).distance_to(Vector2(goal)))
	var offset := Vector2(float(customer.render_offset_x), float(customer.render_offset_y)).move_toward(desired, delta * float(_configuration.service.walking_cells_per_second))
	candidate.render_offset_x = offset.x
	candidate.render_offset_y = offset.y
	var previous := _render_position(customer)
	if _traffic_clear(_render_position(candidate), previous, customer):
		for field in ["x", "y", "path_index", "facing", "render_offset_x", "render_offset_y"]:
			customer[field] = candidate[field]
		customer.yielding = false
		return finished
	# Yield in place, with a wider side step when two paths meet at a corner.
	# Centerline path progress is retained, so a save can resume either state.
	customer.yielding = true
	for sign_value in [1.0, -1.0]:
		var side: Vector2 = right * _customer_number("passing_offset") * 2.0 * sign_value
		var retreat := Vector2(float(customer.render_offset_x), float(customer.render_offset_y)).move_toward(side, delta * float(_configuration.service.walking_cells_per_second))
		var position := Vector2(float(customer.x), float(customer.y)) + retreat
		if _traffic_clear(position, previous, customer):
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
	var distance := delta * float(_configuration.service.walking_cells_per_second)
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

func _seat_reserved(seat_id: String) -> bool:
	for customer in _state.customers:
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
		if not object.get("kind") in ["chef", "belt", "seat"] or not DIRECTIONS.has(object.get("facing")):
			return false
		if not _valid_point(object, config.floor):
			return false
		var cell := _point(object)
		if cells.has(cell) or cell == _point(config.floor.entrance):
			return false
		if object.kind == "chef" and not config.recipes.has(object.get("recipe_id")):
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

func _valid_saved_state(state: Dictionary, config: Dictionary) -> bool:
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
	for object in state.objects:
		occupants[_point(object)] = object
		if object.kind == "chef":
			if not object.has("held_dish") or not _valid_dish(object.held_dish, config.recipes, dish_ids):
				return false
			var duration := float(config.recipes[object.recipe_id].preparation_seconds)
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
		else:
			seats[object.id] = object
	var customer_ids: Dictionary = {}
	var reservations: Dictionary = {}
	for customer in state.customers:
		if not customer is Dictionary or _id_index(customer.get("id"), "customer-") == 0 or customer_ids.has(customer.id):
			return false
		if _id_index(customer.id, "customer-") >= int(state.next_customer_id):
			return false
		customer_ids[customer.id] = true
		if not seats.has(customer.get("seat_id")) or not customer.get("phase") in ["walking", "waiting", "eating", "leaving"]:
			return false
		if not _valid_visit(customer, config):
			return false
		if not DIRECTIONS.has(customer.get("facing")) or not _finite_number(customer.get("visual_elapsed")) or float(customer.visual_elapsed) < 0.0:
			return false
		var allowed_visuals: Array = {"walking": ["walk"], "waiting": ["sit-down", "seated-wait"], "eating": ["eat"], "leaving": ["stand-up", "walk"]}[customer.phase]
		if not customer.get("visual_phase") in allowed_visuals:
			return false
		if customer.visual_phase in ["sit-down", "stand-up"]:
			var seconds := float(config.service.get("sitting_seconds" if customer.visual_phase == "sit-down" else "standing_seconds", 0.0))
			if seconds <= 0.0 or float(customer.visual_elapsed) >= seconds:
				return false
		if customer.phase != "leaving" or customer.visual_phase == "stand-up":
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
		if not _valid_customer_path(customer, seats[customer.seat_id], occupants, config.floor):
			return false
		if not _foot_on_floor(_render_position(customer), customer.seat_id, state.objects, config.floor):
			return false
		if not _finite_number(customer.get("meal_elapsed")) or float(customer.meal_elapsed) < 0.0:
			return false
		if not customer.has("meal_dish") or not _valid_dish(customer.meal_dish, config.recipes, dish_ids):
			return false
		if (customer.phase == "eating") != (customer.meal_dish != null):
			return false
		if customer.phase == "eating":
			if float(customer.meal_elapsed) >= float(customer.meal_duration):
				return false
		elif float(customer.meal_elapsed) != 0.0:
			return false
	# Every produced plate is either still owned by one actor/tile or was sold.
	# Counters must advance past all surviving IDs before new food/visitors spawn.
	if int(state.next_dish_id) != int(state.stats.sales) + dish_ids.size() + 1:
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
	if not customer.get("preferred_recipe_id") is String or (not customer.visit_legacy and not config.recipes.has(customer.preferred_recipe_id)):
		return false
	if not customer.get("preference_phase") in ["pending", "active", "satisfied", "expired", "complete"]:
		return false
	if not customer.get("departure_reason") in ["", "satisfied", "unfed"]:
		return false
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
	if customer.phase == "eating":
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
	if customer.phase == "eating" and (float(customer.meal_fullness) < float(config.customers.dish_fullness_min) or float(customer.meal_fullness) > float(config.customers.dish_fullness_max)):
		return false
	return absf(float(customer.meal_duration) - float(config.service.eating_seconds)) <= float(config.customers.eating_jitter_seconds) + 0.000001

func _valid_customer_path(customer: Dictionary, seat: Dictionary, occupants: Dictionary, floor_data: Dictionary) -> bool:
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
