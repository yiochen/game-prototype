extends RefCounted
## Pure recipe rules. Content/balance lives in recipe_catalog.json, never in UI.
const PATH := "res://content/recipe_catalog.json"
const LEGACY := {"Wood":"White", "Steel":"Yellow", "Copper":"Red", "Silver":"Blue", "Gold":"Black"}

static var _catalog: Dictionary = {}

static func catalog() -> Dictionary:
	if _catalog.is_empty(): _catalog = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _catalog

static func tier(value: String) -> String:
	return str(LEGACY.get(value.capitalize(), value.capitalize()))

static func initialize(config: Dictionary, state: Dictionary) -> bool:
	if not state.get("objects") is Array or not state.get("inventory") is Array: return false
	for stock in state.inventory:
		if not stock is Dictionary: return false
	var definition := catalog()
	var previously_known: Array = config.recipes.keys()
	for id in definition.recipes:
		if not config.recipes.has(id): config.recipes[id] = definition.recipes[id].duplicate(true)
	for id in config.recipes:
		var recipe: Dictionary = config.recipes[id]
		var source: Dictionary = definition.recipes.get(id, {})
		recipe.tier = tier(str(recipe.get("tier", source.get("tier", "White"))))
		recipe.food_cell = int(recipe.get("food_cell", source.get("food_cell", 2)))
	if not state.has("recipe_book"):
		state.recipe_book = {"discovered": previously_known, "new": []}
	for objects in [config.objects, state.objects]:
		for object in objects:
			if object.kind == "chef": _initialize_chef(object, config)
	for stock in state.get("inventory", []):
		if stock.get("kind") != "chef": continue
		if stock.get("stored_object") is Dictionary: _initialize_chef(stock.stored_object, config)
		var actor := chef(state, str(stock.get("id", "")))
		for key in ["level", "level_cap", "cooking_speed"]: stock[key] = actor.get(key, 1)
	return true

static func _initialize_chef(actor: Dictionary, config: Dictionary) -> void:
	if not actor.has("level"): actor.level = required_level(config.recipes.get(actor.get("recipe_id", ""), {}))
	if not actor.has("level_cap"): actor.level_cap = maxi(12, int(actor.level))
	if not actor.has("cooking_speed"): actor.cooking_speed = 1.0

static func chef(state: Dictionary, id: String) -> Dictionary:
	for object in state.get("objects", []):
		if object.get("kind") == "chef" and object.id == id: return object
	for stock in state.get("inventory", []):
		if stock.get("kind") == "chef" and stock.id == id and stock.get("stored_object") is Dictionary: return stock.stored_object
	return {}

static func seconds(recipe: Dictionary, actor: Dictionary) -> float:
	return float(recipe.get("preparation_seconds", 0.0)) / float(actor.get("cooking_speed", 1.0))

static func required_level(recipe: Dictionary) -> int:
	var definition := catalog()
	var index: int = definition.tiers.find(tier(str(recipe.get("tier", "White"))))
	return int(definition.required_levels[maxi(0, index)])

static func eligible(config: Dictionary, state: Dictionary, actor: Dictionary, id: String) -> bool:
	return not actor.is_empty() and config.recipes.has(id) and id in state.recipe_book.discovered and mini(int(actor.get("level", 1)), int(actor.get("level_cap", 12))) >= required_level(config.recipes[id])

static func valid(config: Dictionary, state: Dictionary) -> bool:
	if not state.get("objects") is Array or not state.get("inventory") is Array: return false
	for object in state.objects + state.inventory:
		if not object is Dictionary: return false
	var definition := catalog()
	for recipe in config.recipes.values():
		if not recipe.get("tier") in definition.tiers: return false
		if not recipe.get("food_cell") is float and not recipe.get("food_cell") is int: return false
		if float(recipe.food_cell) != floor(float(recipe.food_cell)) or int(recipe.food_cell) < 0 or int(recipe.food_cell) > 3: return false
	if not state.get("recipe_book") is Dictionary: return false
	var book: Dictionary = state.recipe_book
	for field in ["discovered", "new"]:
		if not book.get(field) is Array: return false
		var unique := {}
		for id in book[field]:
			if not id is String or not config.recipes.has(id) or unique.has(id): return false
			unique[id] = true
	for id in book.new:
		if not id in book.discovered: return false
	var actors: Array = state.objects.duplicate()
	for stock in state.get("inventory", []):
		if stock.get("kind") == "chef" and stock.get("stored_object") is Dictionary: actors.append(stock.stored_object)
	for stock in state.get("inventory", []):
		if stock.get("kind") != "chef": continue
		var owner := chef(state, str(stock.get("id", "")))
		if owner.is_empty() or stock.get("recipe_id") != owner.get("recipe_id"): return false
		for field in ["level", "level_cap", "cooking_speed"]:
			if stock.get(field) != owner.get(field): return false
	for actor in actors:
		if actor.get("kind") != "chef": continue
		for key in ["level", "level_cap"]:
			var value: Variant = actor.get(key)
			if not (value is float or value is int) or not is_finite(float(value)) or float(value) != floor(float(value)) or float(value) < 1 or float(value) > 100: return false
		if actor.level > actor.level_cap: return false
		var speed: Variant = actor.get("cooking_speed")
		if not (speed is float or speed is int) or not is_finite(float(speed)) or float(speed) <= 0: return false
		if actor.recipe_id != "" and not eligible(config, state, actor, actor.recipe_id): return false
	return true

static func command(config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	var id := str(request.get("recipe_id", ""))
	if not config.recipes.has(id): return {"ok":false, "reason":"unknown_recipe"}
	if request.type == "discover_recipe":
		if not id in state.recipe_book.discovered:
			state.recipe_book.discovered.append(id)
			state.recipe_book.new.append(id)
		return {"ok":true}
	var actor := chef(state, str(request.get("chef_id", "")))
	if actor.is_empty(): return {"ok":false, "reason":"unknown_chef"}
	if not id in state.recipe_book.discovered: return {"ok":false, "reason":"undiscovered_recipe"}
	if request.type == "inspect_recipe":
		state.recipe_book.new.erase(id)
		return {"ok":true}
	if not state.objects.any(func(object): return object.kind == "chef" and object.id == actor.id): return {"ok":false,"reason":"chef_unassigned"}
	if not eligible(config, state, actor, id): return {"ok":false, "reason":"recipe_ineligible"}
	if actor.recipe_id == id: return {"ok":true, "changed":false}
	actor.recipe_id = id
	# A completed held dish is replaced immediately, retaining its unique ID.
	# Incomplete preparation restarts; dishes already on the belt are untouched.
	if actor.held_dish is Dictionary: actor.held_dish.recipe_id = id
	actor.preparation_elapsed = seconds(config.recipes[id], actor) if actor.held_dish is Dictionary else 0.0
	actor.loading_elapsed = 0.0
	actor.visual_phase = "hold" if actor.held_dish is Dictionary else "work"
	actor.visual_elapsed = 0.0
	for stock in state.inventory:
		if stock.id == actor.id: stock.recipe_id = id
	state.recipe_book.new.erase(id)
	return {"ok":true, "changed":true}
