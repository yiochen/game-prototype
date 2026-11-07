extends RefCounted
## Chefs: identity, purchased development and the cooking station. This feature
## owns the `staff`, `development` and `station` tables of the restaurant world;
## a chef's grid position is still a layout object until layout moves to the
## store. Speed and durations are calculated, never saved, and preparation is a
## 0..1 fraction, so a level-up needs no rescaling. See docs/state-architecture.md.
const Machine = preload("res://scripts/engine/machine.gd")
const RecipeBook = preload("res://scripts/recipe_book.gd")
const Development = preload("res://scripts/chef_development.gd")
const WORLD := "restaurant"
const TABLES := ["staff", "development", "station"]
## Station lifecycle. Time and transitions advance in GameSession._step_chefs,
## which still reads the belt layout; the definition validates stored states.
const STATION := {"initial": "working", "states": {
	"idle": {"on": {"serve": "working"}},
	"working": {"progress": "duration", "done": "holding", "emit": "prepared"},
	"holding": {"on": {"belt_free": "loading", "idle": "idle"}},
	"loading": {"after": "loading_seconds", "to": "working", "emit": "loaded", "on": {"belt_busy": "holding"}},
}}
const VISUALS := {"idle": "idle", "working": "work", "holding": "hold", "loading": "load"}
const STATES := {"idle": "idle", "work": "working", "hold": "holding", "load": "loading"}
## Fields a chef record carried before the store; views still present them.
const LEGACY_FIELDS := ["name", "full_name", "art_id", "recipe_id", "level", "level_cap", "cooking_speed", "growth_rate", "base_cooking_speed",
	"preparation_elapsed", "held_dish", "loading_elapsed", "visual_phase", "visual_elapsed"]

static func define(store) -> void:
	store.define_component("staff", {"owner": "chefs", "fields": {"name": "Chef", "full_name": "", "art_id": "chef-lena"}})
	store.define_component("development", {"owner": "chefs", "fields": {"level": 1, "level_cap": 12, "growth": 0.0, "base_speed": 1.0}, "derived": ["cooking_speed"]})
	store.define_component("station", {"owner": "chefs", "fields": {"machine": "working", "elapsed": 0.0, "progress": 0.0, "recipe_id": "", "held_dish": null},
		"derived": ["preparation_elapsed", "loading_elapsed", "visual_phase"]})

static func ids(store) -> Array:
	var result: Array = store.table(WORLD, "staff").keys()
	result.sort()
	return result

static func exists(store, id: String) -> bool:
	return store.has_row(WORLD, "staff", id)

static func station(store, id: String) -> Dictionary:
	return store.row(WORLD, "station", id)

static func speed(store, id: String) -> float:
	return _speed(store.row(WORLD, "development", id))

static func _speed(development: Dictionary) -> float:
	return float(development.base_speed) + (int(development.level) - 1) * float(development.growth)

static func duration(store, config: Dictionary, id: String) -> float:
	return _duration(config, station(store, id), store.row(WORLD, "development", id))

static func _duration(config: Dictionary, work: Dictionary, development: Dictionary) -> float:
	var recipe: Variant = config.recipes.get(work.recipe_id)
	return (0.0 if recipe == null else float(recipe.get("preparation_seconds", 0.0))) / _speed(development)

## The chef as screens and recipe rules see it, derived values included.
static func record(store, config: Dictionary, id: String) -> Dictionary:
	if not exists(store, id): return {}
	var identity: Dictionary = store.row(WORLD, "staff", id)
	var development: Dictionary = store.row(WORLD, "development", id)
	var work: Dictionary = station(store, id)
	var result := {"name": identity.name, "art_id": identity.art_id, "recipe_id": work.recipe_id,
		"level": int(development.level), "level_cap": int(development.level_cap), "cooking_speed": _speed(development),
		"growth_rate": float(development.growth), "base_cooking_speed": float(development.base_speed),
		"preparation_elapsed": float(work.progress) * _duration(config, work, development),
		"held_dish": work.held_dish.duplicate(true) if work.held_dish is Dictionary else null,
		"loading_elapsed": float(work.elapsed) if work.machine == "loading" else 0.0,
		"visual_phase": VISUALS[work.machine], "visual_elapsed": float(work.elapsed)}
	if not str(identity.full_name).is_empty(): result.full_name = identity.full_name
	return result

## Adds a chef from a configuration-style record. `seconds` is the dish's full
## preparation time at the record's speed, used to turn elapsed time into progress.
static func add(store, id: String, actor: Dictionary, seconds := 0.0) -> void:
	store.set_row(WORLD, "staff", id, {"name": str(actor.get("name", "Chef")), "full_name": str(actor.get("full_name", "")), "art_id": str(actor.get("art_id", "chef-lena"))})
	var level := int(actor.get("level", 1))
	var growth := float(actor.get("growth_rate", 0.0))
	var base := float(actor.get("base_cooking_speed", float(actor.get("cooking_speed", 1.0)) - (level - 1) * growth))
	store.set_row(WORLD, "development", id, {"level": level, "level_cap": int(actor.get("level_cap", 12)), "growth": growth, "base_speed": base})
	var held: Variant = actor.held_dish.duplicate(true) if actor.get("held_dish") is Dictionary else null
	var progress := 1.0 if held is Dictionary else (clampf(float(actor.get("preparation_elapsed", 0.0)) / seconds, 0.0, 1.0) if seconds > 0.0 else 0.0)
	store.set_row(WORLD, "station", id, {"machine": STATES.get(str(actor.get("visual_phase", "work")), "working"), "elapsed": float(actor.get("visual_elapsed", 0.0)),
		"progress": progress, "recipe_id": str(actor.get("recipe_id", "")), "held_dish": held})

static func remove(store, id: String) -> void:
	for table in TABLES: store.remove_row(WORLD, table, id)

## Back to the start of a dish after a fresh placement. True if a held dish was discarded.
static func reset_station(store, id: String) -> bool:
	var work: Dictionary = store.write(WORLD, "station")[id]
	var discarded: bool = work.held_dish is Dictionary
	work.merge({"machine": "idle", "elapsed": 0.0, "progress": 0.0, "recipe_id": "", "held_dish": null}, true)
	return discarded

## A moved chef stops a loading motion and holds the plate again.
static func interrupt_loading(store, id: String) -> void:
	var work: Dictionary = station(store, id)
	if work.machine != "loading": return
	work = store.write(WORLD, "station")[id]
	work.machine = "holding"
	work.elapsed = 0.0

static func level_up(store, state: Dictionary, request: Dictionary) -> Dictionary:
	var id := str(request.get("chef_id", ""))
	if not exists(store, id): return {"ok": false, "reason": "unknown_chef"}
	var development: Dictionary = store.row(WORLD, "development", id)
	var expected: Variant = request.get("expected_level")
	if not (expected is int or expected is float) or not is_finite(float(expected)) or float(expected) != int(development.level): return {"ok": false, "reason": "stale_level"}
	if int(development.level) >= int(development.level_cap): return {"ok": false, "reason": "chef_max"}
	var price := Development.cost({"level": int(development.level)})
	if int(state.coins) < price: return {"ok": false, "reason": "not_enough_coins"}
	state.coins = int(state.coins) - price
	# Progress is a fraction of the dish, so a faster chef simply finishes sooner.
	store.write(WORLD, "development")[id].level = int(development.level) + 1
	return {"ok": true, "level": int(development.level) + 1, "cost": price, "chef_id": id}

static func fire(store, state: Dictionary, request: Dictionary) -> Dictionary:
	var id := str(request.get("chef_id", ""))
	if not exists(store, id): return {"ok": false, "reason": "unknown_chef"}
	state.staff.dismissed[id] = str(store.row(WORLD, "staff", id).art_id)
	state.staff.hired.erase(id)
	if station(store, id).held_dish is Dictionary: state.discarded_dishes = int(state.discarded_dishes) + 1
	remove(store, id)
	store.remove_row(WORLD, "layout", id)
	for index in range(state.inventory.size() - 1, -1, -1):
		if state.inventory[index].id == id: state.inventory.remove_at(index)
	if state.editor.selected_id == id: state.editor.selected_id = ""
	return {"ok": true, "chef_id": id}

static func prepare(store, config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	var id := str(request.get("recipe_id", ""))
	var chef_id := str(request.get("chef_id", ""))
	if not config.recipes.has(id): return {"ok": false, "reason": "unknown_recipe"}
	if not exists(store, chef_id): return {"ok": false, "reason": "unknown_chef"}
	if not id in state.recipe_book.discovered: return {"ok": false, "reason": "undiscovered_recipe"}
	if request.type == "inspect_recipe":
		state.recipe_book.new.erase(id)
		return {"ok": true}
	if not store.has_row(WORLD, "layout", chef_id): return {"ok": false, "reason": "chef_unassigned"}
	if not RecipeBook.eligible(config, state, record(store, config, chef_id), id): return {"ok": false, "reason": "recipe_ineligible"}
	var work: Dictionary = station(store, chef_id)
	if work.recipe_id == id: return {"ok": true, "changed": false}
	work = store.write(WORLD, "station")[chef_id]
	work.recipe_id = id
	# A completed held dish is replaced immediately, retaining its unique ID.
	# Incomplete preparation restarts; dishes already on the belt are untouched.
	if work.held_dish is Dictionary: work.held_dish.recipe_id = id
	work.machine = "holding" if work.held_dish is Dictionary else "working"
	work.elapsed = 0.0
	work.progress = 1.0 if work.held_dish is Dictionary else 0.0
	state.recipe_book.new.erase(id)
	return {"ok": true, "changed": true}

# --- New games -----------------------------------------------------------------

## A new game's chefs start as full records in the configuration's layout.
## This moves them into the store, leaving only placement and inventory
## bookkeeping behind.
static func extract(state: Dictionary, store, config: Dictionary) -> void:
	var actors := {}
	for object in state.objects:
		if object.kind == "chef": actors[object.id] = object
	for stock in state.inventory:
		if stock.kind == "chef" and stock.get("stored_object") is Dictionary: actors[stock.id] = stock.stored_object
	for id in actors:
		add(store, id, actors[id], RecipeBook.seconds(config.recipes.get(actors[id].get("recipe_id", ""), {}), actors[id]))
	strip(state)

static func strip(state: Dictionary) -> void:
	for object in state.objects:
		if object.kind != "chef": continue
		for field in object.keys():
			if not field in ["id", "kind", "x", "y", "facing"]: object.erase(field)
	for stock in state.inventory:
		if stock.kind != "chef": continue
		for field in stock.keys():
			if not field in ["id", "kind", "count", "assigned", "facing", "staff_new"]: stock.erase(field)

## A chef may only prepare a discovered recipe their level allows.
static func valid_recipes(store, config: Dictionary, recipe_book: Dictionary) -> bool:
	for id in ids(store):
		var recipe: String = station(store, id).recipe_id
		if recipe != "" and not RecipeBook.eligible(config, {"recipe_book": recipe_book}, record(store, config, id), recipe): return false
	return true

## Every chef in the layout or inventory has store rows, and nothing else does.
static func matches(state: Dictionary, store) -> bool:
	if not state.get("objects") is Array or not state.get("inventory") is Array: return false
	var listed := {}
	for stock in state.inventory:
		if stock is Dictionary and stock.get("kind") == "chef": listed[str(stock.get("id", ""))] = true
	for object in state.objects:
		if object is Dictionary and object.get("kind") == "chef" and not listed.has(str(object.get("id", ""))): return false
	var known := ids(store)
	return known.size() == listed.size() and known.all(func(id): return listed.has(id))

## Inventory entries as the People tray shows them.
static func present_stock(item: Dictionary, actor: Dictionary) -> void:
	for field in ["name", "full_name", "art_id", "recipe_id", "level", "level_cap", "cooking_speed", "growth_rate", "base_cooking_speed"]:
		if actor.has(field): item[field] = actor[field]

## Structural checks only: every stored state exists and every chef has all rows.
static func valid(store, config: Dictionary) -> bool:
	for id in ids(store):
		for table in TABLES:
			if not store.has_row(WORLD, table, id): return false
		var development: Dictionary = store.row(WORLD, "development", id)
		var work: Dictionary = station(store, id)
		if not Machine.valid(STATION, work): return false
		for field in ["level", "level_cap"]:
			var value: Variant = development.get(field)
			if not (value is int or value is float) or float(value) != floorf(float(value)) or float(value) < 1: return false
		for field in ["growth", "base_speed"]:
			if not (development.get(field) is float or development.get(field) is int) or not is_finite(float(development[field])): return false
		if speed(store, id) <= 0.0 or not work.recipe_id is String or (work.recipe_id != "" and not config.recipes.has(work.recipe_id)): return false
		if int(development.level) > int(development.level_cap) or int(development.level_cap) > 100: return false
		if work.held_dish != null:
			if not work.held_dish is Dictionary or not work.held_dish.get("id") is String or work.held_dish.get("recipe_id") != work.recipe_id: return false
			if float(work.progress) != 1.0 or work.machine == "working": return false
		elif not work.machine in ["working", "idle"]: return false
		if work.machine == "loading" and (float(config.service.get("loading_seconds", 0.0)) <= 0.0 or float(work.elapsed) >= float(config.service.loading_seconds)): return false
	for table in TABLES:
		for id in store.table(WORLD, table):
			if not exists(store, id): return false
	return true
