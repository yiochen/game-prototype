class_name RestaurantModel
extends RefCounted
## Deterministic, serializable restaurant simulation; independent of presentation.

const GRID_W := 8
const GRID_H := 9
const DIRECTIONS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
const ENTRY := Vector2i(3, 8)
const DEFAULT_RECIPES := {
	"cucumber": {"price": 8, "prep": 3.4, "level": 1, "tier": "Wood"},
	"salmon": {"price": 14, "prep": 4.2, "level": 1, "tier": "Wood"},
	"shrimp": {"price": 24, "prep": 4.7, "level": 3, "tier": "Steel"},
	"eel": {"price": 38, "prep": 5.1, "level": 5, "tier": "Copper"},
}
const DEFAULT_COSTS := {"belt": 12, "seat": 28, "chef": 90, "expand": 180}

var data: Dictionary = {}
var recipes: Dictionary = DEFAULT_RECIPES.duplicate(true)
var costs: Dictionary = DEFAULT_COSTS.duplicate(true)
var _rng := RandomNumberGenerator.new()
var _next_id := 1
var _spawn_clock := 0.0
var _belt_clock := 0.0
var _belt_period := 0.8
var _spawn_period := 4.0
var _events: Array = []

func _init() -> void:
	_rng.seed = 418731
	_read_balance()
	_reset()

func _read_balance() -> void:
	if not FileAccess.file_exists("res://balance.json"):
		return
	var source: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://balance.json"))
	if not source is Dictionary:
		return
	var defs: Variant = source.get("recipes", {})
	if defs is Dictionary:
		for key in defs:
			if defs[key] is Dictionary and recipes.has(key):
				recipes[key].merge(defs[key], true)
	elif defs is Array:
		for definition in defs:
			if definition is Dictionary and recipes.has(definition.get("id", "")):
				recipes[definition.id].merge(definition, true)
	var settings: Dictionary = source.get("restaurant", {})
	costs.merge(settings.get("costs", {}), true)
	_belt_period = float(settings.get("belt_period", 0.8))
	_spawn_period = float(settings.get("spawn_period", 4.0))

func _reset() -> void:
	data = {
		"version": 1, "coins": 180.0, "objects": [], "customers": [],
		"inventory": {"belt": 8, "seat": 2, "chef": 0}, "recipes": ["cucumber"],
		"unassigned_chefs": [], "expanded": false, "time": 0.0,
		"stats": {"sales": 0, "revenue": 0.0, "visitors": 0, "served": 0, "missed": 0},
	}
	_next_id = 1
	_spawn_clock = _spawn_period - 1.5
	_belt_clock = 0.0
	for cell in [[2,2,1],[3,2,1],[4,2,1],[5,2,2],[5,3,2],[5,4,2],[5,5,2]]:
		_add_object("belt", cell[0], cell[1], cell[2])
	_add_object("chef", 2, 3, 0)
	_add_object("seat", 3, 1, 2)
	_add_object("seat", 6, 3, 3)
	_add_object("seat", 6, 5, 3)
	object_at(3, 2)["dish"] = "cucumber"
	object_at(5, 4)["dish"] = "cucumber"

func _add_object(kind: String, x: int, y: int, direction: int = 1) -> Dictionary:
	var obj := {
		"id": _next_id, "kind": kind, "x": x, "y": y, "dir": direction,
		"level": 1, "max_level": 12, "recipe": "cucumber" if kind == "chef" else "",
		"progress": 0.0, "dish": "", "customer": {}, "reserved": 0,
	}
	_next_id += 1
	data.objects.append(obj)
	return obj

func serialize() -> Dictionary:
	var result: Dictionary = data.duplicate(true)
	result["_rng_state"] = str(_rng.state)
	result["_next_id"] = _next_id
	result["_spawn_clock"] = _spawn_clock
	result["_belt_clock"] = _belt_clock
	return result

func restore(saved: Dictionary) -> void:
	if not saved.get("objects", null) is Array or not saved.get("inventory", null) is Dictionary:
		return
	data = saved.duplicate(true)
	data["customers"] = data.get("customers", [])
	data["unassigned_chefs"] = data.get("unassigned_chefs", [])
	data["expanded"] = data.get("expanded", false)
	data["time"] = float(data.get("time", 0.0))
	data["recipes"] = data.get("recipes", ["cucumber"])
	data["stats"] = data.get("stats", {"sales":0,"revenue":0.0,"visitors":0,"served":0,"missed":0})
	data["coins"] = float(data.get("coins", 0.0))
	for key in ["sales", "visitors", "served", "missed"]:
		data.stats[key] = int(data.stats.get(key, 0))
	data.stats["revenue"] = float(data.stats.get("revenue", 0.0))
	for key in data.inventory:
		data.inventory[key] = int(data.inventory[key])
	_next_id = int(data.get("_next_id", 1))
	_spawn_clock = float(data.get("_spawn_clock", 0.0))
	_belt_clock = float(data.get("_belt_clock", 0.0))
	_rng.state = int(data.get("_rng_state", str(_rng.state)))
	for obj in data.objects:
		obj["id"] = int(obj.id)
		_next_id = maxi(_next_id, int(obj.id) + 1)
		obj["customer"] = {}
		obj["reserved"] = int(obj.get("reserved", 0))
	for person in data.customers:
		_next_id = maxi(_next_id, int(person.id) + 1)
		var seat := get_object(int(person.get("seat_id", 0)))
		if not seat.is_empty() and person.state == "seated":
			seat["customer"] = person

func get_object(id: int) -> Dictionary:
	for obj in data.objects:
		if int(obj.id) == id:
			return obj
	return {}

func object_at(x: int, y: int) -> Dictionary:
	for obj in data.objects:
		if int(obj.x) == x and int(obj.y) == y:
			return obj
	return {}

func facing_cell(obj: Dictionary) -> Vector2i:
	var cell := Vector2i(int(obj.get("x", -9)), int(obj.get("y", -9)))
	var direction := int(obj.get("dir", -1))
	return cell + DIRECTIONS[direction] if direction >= 0 and direction < 4 else Vector2i(-99, -99)

func is_floor(x: int, y: int) -> bool:
	if x < 0 or y < 0 or x >= GRID_W or y >= GRID_H:
		return false
	return bool(data.get("expanded", false)) or (x >= 1 and x <= 6 and y >= 1 and y <= 7) or Vector2i(x,y) == ENTRY

func can_place(kind: String, x: int, y: int) -> bool:
	if not kind in ["belt", "seat", "chef"] or not is_floor(x,y) or not object_at(x,y).is_empty():
		return false
	if Vector2i(x,y) == ENTRY:
		return false
	for person in data.customers:
		if Vector2i(roundi(person.x), roundi(person.y)) == Vector2i(x,y) and kind != "seat":
			if _nearest_empty(Vector2i(x,y), Vector2i(x,y)) == Vector2i(-1,-1):
				return false
	return true

func price_for(kind: String) -> int:
	return int(costs.get(kind, 0))

func buy(kind: String) -> bool:
	if not kind in ["belt", "seat", "chef"]:
		return false
	if kind == "chef" and _staff_count() >= (4 if data.expanded else 3):
		return false
	var cost := price_for(kind)
	if float(data.coins) < cost:
		return false
	data.coins -= cost
	data.inventory[kind] = int(data.inventory.get(kind, 0)) + 1
	return true

func place(kind: String, x: int, y: int) -> bool:
	if int(data.inventory.get(kind,0)) <= 0 or not can_place(kind,x,y):
		return false
	var obj: Dictionary
	if kind == "chef" and not data.unassigned_chefs.is_empty():
		obj = data.unassigned_chefs.pop_front()
		obj.x = x
		obj.y = y
		data.objects.append(obj)
	else:
		obj = _add_object(kind, x, y)
		if kind == "chef":
			obj.recipe = ""
	if kind in ["chef", "seat"]:
		for d in range(4):
			var neighbor: Vector2i = Vector2i(x,y) + DIRECTIONS[d]
			if object_at(neighbor.x, neighbor.y).get("kind", "") == "belt":
				obj.dir = d
				break
	data.inventory[kind] -= 1
	_displace_customers(obj)
	_invalidate_walks()
	return true

func move_object(id: int, x: int, y: int) -> bool:
	var obj := get_object(id)
	if obj.is_empty():
		return move_customer(id,x,y)
	if int(obj.x) == x and int(obj.y) == y:
		return true
	if not can_place(obj.kind,x,y):
		return false
	obj.x = x
	obj.y = y
	if not obj.customer.is_empty():
		obj.customer.x = float(x)
		obj.customer.y = float(y)
	_displace_customers(obj)
	_invalidate_walks()
	return true

func move_customer(id: int, x: int, y: int) -> bool:
	if not is_floor(x,y):
		return false
	var obj := object_at(x,y)
	if not obj.is_empty() and (obj.kind != "seat" or not obj.customer.is_empty() or int(obj.reserved) != 0):
		return false
	for person in data.customers:
		if int(person.id) == id:
			_release_seat(person)
			person.x = float(x)
			person.y = float(y)
			person.path = []
			if obj.get("kind", "") == "seat":
				_seat_customer(person,obj)
			else:
				person.state = "searching"
			return true
	return false

func rotate_object(id: int) -> bool:
	var obj := get_object(id)
	if obj.is_empty():
		return false
	obj.dir = (int(obj.dir) + 1) % 4
	return true

func connect_belt(from_id: int, to_id: int) -> bool:
	var source := get_object(from_id)
	var target := get_object(to_id)
	if source.get("kind", "") != "belt" or target.get("kind", "") != "belt":
		return false
	var delta := Vector2i(int(target.x) - int(source.x), int(target.y) - int(source.y))
	var direction := DIRECTIONS.find(delta)
	if direction == -1:
		return false
	# Reusing a tile in a new path relinquishes its old incoming route.
	for other in data.objects:
		if other.kind == "belt" and int(other.id) != from_id and facing_cell(other) == Vector2i(int(target.x),int(target.y)):
			other.dir = -1
	source.dir = direction
	return true

func remove_object(id: int) -> bool:
	var obj := get_object(id)
	if obj.is_empty():
		return false
	if obj.kind == "seat":
		for person in data.customers:
			if int(person.seat_id) == id:
				person.seat_id = 0
				person.state = "searching"
				person.path = []
	if obj.kind == "chef":
		data.unassigned_chefs.append(obj)
	data.inventory[obj.kind] = int(data.inventory.get(obj.kind,0)) + 1
	data.objects.erase(obj)
	_invalidate_walks()
	return true

func upgrade_cost(id: int) -> int:
	var obj := get_object(id)
	if obj.get("kind", "") != "chef" or int(obj.level) >= int(obj.get("max_level",12)):
		return 0
	return int(round(32.0 * pow(float(obj.level), 1.3)))

func upgrade_chef(id: int) -> bool:
	var cost := upgrade_cost(id)
	if cost <= 0 or float(data.coins) < cost:
		return false
	data.coins -= cost
	get_object(id).level += 1
	return true

func assign_recipe(id: int, recipe: String) -> bool:
	var obj := get_object(id)
	if obj.get("kind", "") != "chef" or not data.recipes.has(recipe) or not recipes.has(recipe):
		return false
	if int(obj.level) < int(recipes[recipe].get("level", 1)):
		return false
	if obj.recipe == recipe:
		return true
	obj.recipe = recipe
	obj.progress = 0.0
	obj.dish = ""
	return true

func chef_prep_time(obj: Dictionary, recipe: String = "") -> float:
	var key: String = recipe if recipe != "" else str(obj.get("recipe", "cucumber"))
	var definition: Dictionary = recipes.get(key, recipes.cucumber)
	return float(definition.get("prep", 3.4)) / (1.0 + 0.13 * (int(obj.get("level",1)) - 1))

func expand() -> bool:
	if bool(data.expanded) or float(data.coins) < price_for("expand"):
		return false
	data.coins -= price_for("expand")
	data.expanded = true
	return true

func _staff_count() -> int:
	var count := int(data.inventory.get("chef",0))
	for obj in data.objects:
		if obj.kind == "chef":
			count += 1
	return count

func tick(delta: float) -> Array:
	_events = []
	var left := maxf(0.0,delta)
	while left > 0.00001:
		var step := minf(left,0.2)
		_step(step)
		left -= step
	return _events

func _step(delta: float) -> void:
	data.time += delta
	_belt_clock += delta
	_spawn_clock += delta
	if _belt_clock >= _belt_period:
		_belt_clock -= _belt_period
		_move_belts()
	for obj in data.objects:
		if obj.kind == "chef" and obj.recipe != "":
			_cook(obj,delta)
	for person in data.customers.duplicate():
		_update_customer(person,delta)
	if _spawn_clock >= _spawn_period:
		_spawn_clock -= _spawn_period
		_spawn_customer()

func _move_belts() -> void:
	var edges := {}
	var incoming := {}
	var belts := {}
	for obj in data.objects:
		if obj.kind == "belt":
			belts[int(obj.id)] = obj
			var at := facing_cell(obj)
			var target := object_at(at.x,at.y)
			if target.get("kind", "") == "belt":
				edges[int(obj.id)] = int(target.id)
				incoming[int(target.id)] = int(incoming.get(int(target.id),0)) + 1
	# Ambiguous junctions hold locally. The editor's connect_belt guarantees a
	# single incoming edge; rotating manually never creates an implicit merge.
	for id in edges.keys():
		if int(incoming[edges[id]]) > 1:
			edges.erase(id)
	var moving := {}
	for id in belts:
		if belts[id].dish == "":
			continue
		var visited := {}
		var cursor: int = id
		var may_move := false
		while edges.has(cursor):
			visited[cursor] = true
			cursor = int(edges[cursor])
			if belts[cursor].dish == "" or visited.has(cursor):
				may_move = true
				break
		if may_move:
			moving[id] = str(belts[id].dish)
	for id in moving:
		belts[id].dish = ""
	for id in moving:
		var target: Dictionary = belts[edges[id]]
		target.dish = moving[id]
		target["from_x"] = belts[id].x
		target["from_y"] = belts[id].y
		target["moved_at"] = data.time

func _cook(chef: Dictionary, delta: float) -> void:
	if chef.dish == "":
		chef.progress = minf(1.0, float(chef.progress) + delta / chef_prep_time(chef))
		if chef.progress >= 1.0:
			chef.dish = chef.recipe
			_events.append({"type":"cook", "id":chef.id, "x":chef.x,"y":chef.y,"recipe":chef.recipe})
	if chef.dish != "":
		var at := facing_cell(chef)
		var belt := object_at(at.x,at.y)
		if belt.get("kind", "") == "belt" and belt.dish == "":
			belt.dish = chef.dish
			belt["from_x"] = chef.x
			belt["from_y"] = chef.y
			belt["moved_at"] = data.time
			chef.dish = ""
			chef.progress = 0.0

func _spawn_customer() -> void:
	if data.customers.size() >= 12:
		return
	var person := {
		"id":_next_id, "x":float(ENTRY.x), "y":float(ENTRY.y), "seat_id":0,
		"state":"searching", "wish":str(data.recipes[_rng.randi_range(0,data.recipes.size()-1)]),
		"preference_time":_rng.randf_range(9.0,15.0), "preference_total":15.0,
		"appetite":_rng.randf_range(1.3,3.8), "eaten":0, "eating_time":0.0,
		"wait_time":0.0,"happy_time":0.0,"path":[],"color":_rng.randi_range(0,5),
	}
	person.preference_total = person.preference_time
	_next_id += 1
	if not _find_seat(person):
		return
	data.customers.append(person)
	data.stats.visitors += 1
	_events.append({"type":"arrive", "id":person.id})

func _find_seat(person: Dictionary) -> bool:
	var start := Vector2i(roundi(person.x),roundi(person.y))
	var chosen: Dictionary = {}
	var chosen_path: Array = []
	var best_score := -INF
	for obj in data.objects:
		if obj.kind != "seat" or not obj.customer.is_empty() or int(obj.get("reserved",0)) != 0:
			continue
		var route := _path(start,Vector2i(int(obj.x),int(obj.y)))
		if route.is_empty() and start != Vector2i(int(obj.x),int(obj.y)):
			continue
		var score := -float(route.size()) * 0.3
		var at := facing_cell(obj)
		var belt := object_at(at.x,at.y)
		if belt.get("kind", "") == "belt":
			score += 3.0
			if belt.dish == person.wish:
				score += 4.0
		for chef in data.objects:
			if chef.kind == "chef" and chef.recipe == person.wish:
				score += maxf(0, 2.5 - Vector2(chef.x-obj.x,chef.y-obj.y).length() * 0.5)
		if score > best_score:
			best_score = score
			chosen = obj
			chosen_path = route
	if chosen.is_empty():
		return false
	chosen.reserved = person.id
	person.seat_id = chosen.id
	person.path = chosen_path
	person.state = "walking"
	if chosen_path.is_empty():
		_seat_customer(person,chosen)
	return true

func _seat_customer(person: Dictionary, seat: Dictionary) -> void:
	seat.customer = person
	seat.reserved = 0
	person.seat_id = seat.id
	person.state = "seated"
	person.x = float(seat.x)
	person.y = float(seat.y)
	person.path = []
	_events.append({"type":"seat", "id":person.id,"x":seat.x,"y":seat.y})

func _update_customer(person: Dictionary, delta: float) -> void:
	person.happy_time = maxf(0,float(person.happy_time)-delta)
	if person.state in ["walking", "leaving"]:
		_walk(person,delta)
		return
	if person.state in ["searching", "trapped"]:
		if _find_seat(person):
			return
		var route := _path(Vector2i(roundi(person.x),roundi(person.y)),ENTRY)
		if route.is_empty():
			person.state = "trapped"
		else:
			person.state = "leaving"
			person.path = route
		return
	if person.state != "seated":
		return
	var seat := get_object(int(person.seat_id))
	if seat.is_empty():
		person.state = "searching"
		return
	person.preference_time = maxf(0,float(person.preference_time)-delta)
	if float(person.eating_time) > 0.0:
		person.eating_time = maxf(0,float(person.eating_time)-delta)
		if float(person.eating_time) <= 0.0 and float(person.appetite) <= 0.0:
			data.stats.served += 1
			_leave(person, false)
		return
	person.wait_time += delta
	var at := facing_cell(seat)
	var belt := object_at(at.x,at.y)
	var dish := str(belt.get("dish", ""))
	if dish != "" and (int(person.eaten) > 0 or float(person.preference_time) <= 0 or dish == person.wish):
		belt.dish = ""
		var price := int(recipes.get(dish,recipes.cucumber).get("price",8))
		data.coins += price
		data.stats.sales += 1
		data.stats.revenue += price
		var preferred: bool = int(person.eaten) == 0 and dish == person.wish
		person.eaten += 1
		person.appetite -= _rng.randf_range(0.85,1.25)
		person.eating_time = _rng.randf_range(2.1,3.0)
		person.wait_time = 0.0
		if preferred:
			person.happy_time = 1.6
		_events.append({"type":"sale","id":person.id,"x":seat.x,"y":seat.y,"amount":price,"recipe":dish,"happy":preferred})
	elif float(person.wait_time) >= 28.0:
		data.stats.missed += 1
		_leave(person,true)

func _leave(person: Dictionary, restless: bool) -> void:
	_release_seat(person)
	person.state = "leaving"
	person.path = _path(Vector2i(roundi(person.x),roundi(person.y)),ENTRY)
	person["restless"] = restless
	if person.path.is_empty():
		person.state = "trapped"
	_events.append({"type":"leave","id":person.id,"x":person.x,"y":person.y,"restless":restless})

func _release_seat(person: Dictionary) -> void:
	var seat := get_object(int(person.get("seat_id",0)))
	if not seat.is_empty():
		seat.customer = {}
		seat.reserved = 0
	person.seat_id = 0

func _walk(person: Dictionary, delta: float) -> void:
	var distance := delta * 2.4
	while distance > 0.0 and not person.path.is_empty():
		var next: Array = person.path[0]
		var target := Vector2(float(next[0]),float(next[1]))
		var from := Vector2(float(person.x),float(person.y))
		var gap := from.distance_to(target)
		if gap <= distance:
			person.x = target.x
			person.y = target.y
			person.path.pop_front()
			distance -= gap
		else:
			var pos := from.move_toward(target,distance)
			person.x = pos.x
			person.y = pos.y
			distance = 0.0
	if not person.path.is_empty():
		return
	if person.state == "leaving":
		data.customers.erase(person)
	elif person.state == "walking":
		var seat := get_object(int(person.seat_id))
		if seat.is_empty():
			person.state = "searching"
		else:
			_seat_customer(person,seat)

func _path(start: Vector2i, goal: Vector2i) -> Array:
	if start == goal:
		return []
	var queue: Array[Vector2i] = [start]
	var parent := {start:start}
	var index := 0
	while index < queue.size():
		var current := queue[index]
		index += 1
		for direction in DIRECTIONS:
			var next: Vector2i = current + direction
			if parent.has(next) or not is_floor(next.x,next.y):
				continue
			if next != goal and not object_at(next.x,next.y).is_empty():
				continue
			parent[next] = current
			if next == goal:
				var route: Array = []
				var cursor := goal
				while cursor != start:
					route.push_front([cursor.x,cursor.y])
					cursor = parent[cursor]
				return route
			queue.append(next)
	return []

func _nearest_empty(start: Vector2i, forbidden: Vector2i) -> Vector2i:
	var best := Vector2i(-1,-1)
	var distance := INF
	for y in range(GRID_H):
		for x in range(GRID_W):
			var cell := Vector2i(x,y)
			if cell == forbidden or not is_floor(x,y) or not object_at(x,y).is_empty():
				continue
			var gap := Vector2(cell-start).length()
			if gap < distance:
				distance = gap
				best = cell
	return best

func _displace_customers(obj: Dictionary) -> void:
	for person in data.customers:
		if Vector2i(roundi(person.x),roundi(person.y)) != Vector2i(int(obj.x),int(obj.y)):
			continue
		if not obj.customer.is_empty() and int(obj.customer.id) == int(person.id):
			continue
		_release_seat(person)
		if obj.kind == "seat" and obj.customer.is_empty():
			_seat_customer(person,obj)
		else:
			var free := _nearest_empty(Vector2i(int(obj.x),int(obj.y)),Vector2i(int(obj.x),int(obj.y)))
			person.x = float(free.x)
			person.y = float(free.y)
			person.state = "searching"
			person.path = []

func _invalidate_walks() -> void:
	for person in data.customers:
		if person.state == "walking":
			var seat := get_object(int(person.seat_id))
			if not seat.is_empty():
				var start := Vector2i(roundi(person.x),roundi(person.y))
				var goal := Vector2i(int(seat.x),int(seat.y))
				person.path = _path(start,goal)
				if person.path.is_empty() and start != goal:
					_release_seat(person)
					person.state = "searching"
		elif person.state == "leaving":
			person.path = _path(Vector2i(roundi(person.x),roundi(person.y)),ENTRY)
			if person.path.is_empty():
				person.state = "trapped"

func offline_income(seconds: float) -> int:
	if seconds <= 0.0:
		return 0
	# Measure this committed layout, including its actual routes, bottlenecks,
	# recipes and chef speeds. Extrapolation has no absence cap.
	var probe: RefCounted = get_script().new()
	probe.restore(serialize())
	var duration := minf(seconds,180.0)
	var before := float(probe.data.coins)
	probe.tick(duration)
	var earned := maxf(0,float(probe.data.coins)-before)
	var result := int(floor(earned * seconds / duration))
	data.coins += result
	data.stats.revenue += result
	return result
