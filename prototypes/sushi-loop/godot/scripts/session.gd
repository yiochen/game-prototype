class_name GameSession
extends RefCounted
## The restaurant's public command / elapsed-time / save boundary.
## Construction loads tuneable content; rules have no wall clock or persistence.
## A caller decides when time passes and where snapshots are stored.

## The only save format this game reads; there are no released saves to upgrade.
const SAVE_VERSION := 3
const Doorway = preload("res://scripts/doorway.gd")
const RecipeBook = preload("res://scripts/recipe_book.gd")
const StaffBook = preload("res://scripts/staff_book.gd")
const Development = preload("res://scripts/chef_development.gd")
const FloorBook = preload("res://scripts/floor_book.gd")
const ShopBook = preload("res://scripts/shop_book.gd")
const Expansion = preload("res://scripts/expansion_book.gd")
const ExpeditionBook = preload("res://scripts/expedition/expedition_book.gd")
const Store = preload("res://scripts/engine/store.gd")
const Chefs = preload("res://scripts/features/chefs.gd")
const Layout = preload("res://scripts/features/layout.gd")
const Customers = preload("res://scripts/features/customers.gd")
const Navigation = preload("res://scripts/features/navigation.gd")
const Tips = preload("res://scripts/features/tips.gd")
const WorkshopBook = preload("res://scripts/workshop_book.gd")
const Tea = preload("res://scripts/features/tea.gd")
## Self-contained features whose records are store slices. `_state` is the
## session's own `core` slice; it also refers to these slices under their
## names so older code can read them, but never holds a copy.
const SLICES := {"shop": 2, "floor_styles": 1, "recipe_book": 1, "staff": 1, "expansion": 1, "inventory": 2, "editor": 1, "expedition": 1, "tips": 1, "workshop": 1}
## Commands that may place, move or remove layout objects.
const LAYOUT_COMMANDS := ["staff_place", "unassign_chef", "fire_chef"]
const BeltRoutes = preload("res://scripts/belt_routes.gd")
const EDITOR_PATH := "res://content/editor.json"
const EDITOR_LAYERS := ["people", "layout", "floor"]
const DECOR_ART_IDS := ["plant-angular", "crate-wood", "barrel-wood", "tip-jar"]
const TIP_COMMANDS := ["tea_pour_open", "tea_pour_cancel", "tea_pour_finish", "collect_cash", "collect_jar", "tip_jar_upgrade"]
const CHEF_ART_IDS := ["chef-lena", "chef-omar", "chef-ama", "chef-mateo", "chef-noor", "chef-dalia", "chef-ellis", "chef-rowan"]
const MAX_EXACT_INTEGER := 9007199254740991
const CONTENT_PATH := "res://content/starter.json"
const DIRECTIONS := {
	"north": Vector2i(0, -1), "east": Vector2i(1, 0),
	"south": Vector2i(0, 1), "west": Vector2i(-1, 0),
}

var _configuration: Dictionary = {}
var _state: Dictionary = {}
## Features that have moved off the single dictionary keep their state here.
var _store := _new_store()
var _random := RandomNumberGenerator.new()
var _remainder := 0.0
var _staff_seed := 1
var _access_paths: Dictionary = {}
## Usable floor cells, rebuilt when the floor or the expansion slice changes.
var _walkable_cells: Dictionary = {}
var _walkable_key: Array = []
var _editor_content: Dictionary = {}
var _expansion_view_state: Dictionary = {}
var _expansion_view_cache: Dictionary = {}
## Events decided outside a step's own event list (a tip on leaving); flushed
## into the next advance() or command result.
var _pending_events: Array = []
var _swept_cash: Array = []

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

static func _new_store() -> Store:
	var store := Store.new()
	Chefs.define(store)
	Layout.define(store)
	Customers.define(store)
	# Version 2 of shop and inventory adds the tip jar (#61) to saves made before it.
	var migrations := {"shop": [ShopBook.add_missing_offers], "inventory": [_add_missing_stock]}
	for name in SLICES: store.define_slice(name, {"version": SLICES[name], "initial": func(): return null, "migrations": migrations.get(name, [])})
	# The session's own values: coins, clock, counters, camera, mode and stats.
	store.define_slice("core", {"owner": "session", "initial": func(): return null, "encode": _encode_core})
	store.create_world(Chefs.WORLD)
	return store

## Inventory entries from content/editor.json that an older save lacks.
static func _add_missing_stock(inventory: Variant) -> Variant:
	if not inventory is Array: return inventory
	var definition: Variant = JSON.parse_string(FileAccess.get_file_as_string(EDITOR_PATH))
	var known := {}
	for entry in inventory:
		if entry is Dictionary: known[entry.get("id")] = true
	for entry in definition.get("inventory", []):
		if not known.has(entry.id): inventory.append(entry.duplicate(true))
	return inventory

## Every command is all or nothing for state in the store.
func command(request: Dictionary) -> Dictionary:
	var type := str(request.get("type", ""))
	var result := _store.transaction(func():
		for name in _slices_written(type):
			if _store.slice(name) != null: _store.write_slice(name)
		if type.begins_with("editor_") or type in LAYOUT_COMMANDS:
			_store.write(Layout.WORLD, "layout")
			_store.write(Customers.WORLD, "customer")
		if type.begins_with("tea_pour_"): _store.write(Customers.WORLD, "customer")
		_swept_cash.clear()
		var outcome := _command(request)
		# Furniture never sits on cash: an edit that covers a pile collects it.
		if outcome.get("ok", false) and (type.begins_with("editor_") or type in LAYOUT_COMMANDS):
			_swept_cash.append_array(_sweep_cash())
			if not _swept_cash.is_empty(): outcome.cash_collected = _swept_cash.duplicate(true)
		_swept_cash.clear()
		return outcome)
	if result.get("ok", false) and not _pending_events.is_empty(): result.events = _pending_events.duplicate(true)
	_pending_events.clear()
	# A rollback replaces slices, and older code may replace a whole record.
	if result.get("ok", false): _relink_slices()
	else:
		_bind_slices()
		# Routes computed during a rejected edit described the undone layout.
		if type.begins_with("editor_") or type in LAYOUT_COMMANDS: _rebuild_access()
	return result

## Slices a command may change, so a failed command restores them.
static func _slices_written(type: String) -> Array:
	if type.begins_with("floor_"): return ["floor_styles", "editor"]
	# Steering and advancing run every frame and never fail after a change.
	if type.begins_with("expedition_"): return [] if type in ["expedition_advance", "expedition_steer"] else ["expedition", "floor_styles", "recipe_book"]
	if type.begins_with("editor_"): return ["editor", "inventory", "tips"]
	if type in TIP_COMMANDS: return ["tips"]
	if type.begins_with("workshop_"): return ["workshop", "expedition"]
	match type:
		"shop_purchase": return ["shop", "inventory"]
		"clear_trash", "reveal_dock", "dock_access": return ["expansion"]
		"hire_applicant", "refresh_applicants", "staff_seen": return ["staff", "inventory"]
		"fire_chef": return ["staff", "inventory", "editor", "tips"]
		"staff_place", "unassign_chef": return ["editor", "inventory", "tips"]
		"set_mode": return ["editor", "inventory"]
		"discover_recipe", "inspect_recipe", "prepare_recipe": return ["recipe_book"]
	return []

func _bind_slices() -> void:
	_store.slices["core"] = _state
	for name in SLICES:
		var value: Variant = _store.slice(name)
		if value == null: _state.erase(name)
		else: _state[name] = value

## After a successful command the store adopts any record `_state` replaced.
func _relink_slices() -> void:
	_store.slices["core"] = _state
	for name in SLICES:
		if not is_same(_store.slice(name), _state.get(name)): _store.slices[name] = _state.get(name)

## The saved form of the core slice: no slice references, nothing derived.
static func _encode_core(core: Variant) -> Variant:
	if not core is Dictionary: return null
	var saved := {}
	for key in core:
		if SLICES.has(key) or key in ["elapsed", "next_customer_id"]: continue
		saved[key] = core[key].duplicate(true) if (core[key] is Dictionary or core[key] is Array) else core[key]
	if saved.get("stats") is Dictionary: saved.stats.erase("served")
	return saved

## Moves feature records out of a single-dictionary state into slices.
static func _extract_slices(state: Dictionary, store: Store) -> void:
	for name in SLICES: store.set_slice(name, state.get(name))
	store.set_slice("core", state)

func _command(request: Dictionary) -> Dictionary:
	if str(request.get("type", "")).begins_with("floor_"): return FloorBook.command(_configuration,_state,request)
	if str(request.get("type", "")).begins_with("expedition_"):
		var outcome := ExpeditionBook.command(_configuration,_state,request,_store)
		# The run's transient world ends with the run.
		if _state.expedition.run == null: _store.drop_world(ExpeditionBook.WORLD)
		return outcome
	if request.get("type") in ["clear_trash","dock_access","reveal_dock"]:
		var result := Expansion.command(_configuration,_state,request)
		if result.get("ok",false) and result.get("changed",false): _rebuild_access()
		return result
	if request.get("type") == "shop_purchase": return ShopBook.command(_state, request)
	if str(request.get("type", "")).begins_with("workshop_"): return WorkshopBook.command(_state, request)
	if request.get("type") in TIP_COMMANDS: return _tip_command(request)
	if request.get("type") in ["level_up_chef","fire_chef"]:
		var result:=Chefs.level_up(_store,_state,request) if request.type=="level_up_chef" else Chefs.fire(_store,_state,request)
		# Only firing changes the layout and inventory; a level-up changes neither.
		if result.get("ok",false) and request.type=="fire_chef":
			for layer in EDITOR_LAYERS:_state.editor.pages[layer]=mini(int(_state.editor.pages[layer]),_editor_page_count(layer,_state.inventory)-1)
			_state.editor.page=_state.editor.pages[_state.editor.layer]
			_rebuild_access()
		return result
	if request.get("type")=="unassign_chef":
		var actor:=_object_by_id(str(request.get("chef_id","")))
		if not Chefs.exists(_store,str(request.get("chef_id",""))):return {"ok":false,"reason":"unknown_chef"}
		if actor.get("kind")!="chef":return {"ok":true,"changed":false}
		var old_mode:String=_state.mode
		var old_editor:Dictionary=_state.editor.duplicate(true)
		_state.mode="edit";_state.editor.layer="people"
		var result:=_editor_change({"type":"editor_remove","id":actor.id})
		_state.mode=old_mode;_state.editor=old_editor
		if _state.editor.selected_id==actor.id:_state.editor.selected_id=""
		return result
	if request.get("type") in ["hire_applicant", "refresh_applicants", "staff_seen"]:
		return StaffBook.command(_configuration, _state, request, _store)
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
		if result.get("ok",false):
			if Chefs.reset_station(_store,str(request.inventory_id)):_state.discarded_dishes=int(_state.discarded_dishes)+1
		return result
	if request.get("type") in ["inspect_recipe", "prepare_recipe"]:
		return Chefs.prepare(_store, _configuration, _state, request)
	if request.get("type") == "discover_recipe":
		return RecipeBook.command(_configuration, _state, request)
	if str(request.get("type", "")).begins_with("editor_"):
		return _editor_command(request)
	match request.get("type", ""):
		"set_mode":
			if not request.get("mode") in ["live", "edit"]:
				return {"ok": false, "reason": "invalid_mode"}
			_state.mode = request.mode
			if request.mode == "live":
				_state.editor.erase("floor_brush")
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
	# Belts and chefs move dishes along layout rows; guests move every step.
	if count > 0:
		_store.write(Layout.WORLD, "layout")
		_store.write(Customers.WORLD, "customer")
	for index in range(count):
		_state.step_index += 1
		_state.elapsed = int(_state.step_index) * step
		_step_customers(step, events)
		_step_belts(step, events)
		_step_chefs(step, events)
		_step_arrivals(step, events)
		events.append_array(_pending_events)
		_pending_events.clear()
	_store.settle()
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
		"inventory": [],
		"floor": _configuration.floor.duplicate(true),
		"recipes": _configuration.recipes.duplicate(true),
		"loading_seconds": float(_configuration.service.get("loading_seconds", 0.0)),
		"recipe_book": _state.recipe_book.duplicate(true),
		"staff": StaffBook.snapshot(_state,_configuration),
		"shop": ShopBook.snapshot(_state),
		"floor_styles": FloorBook.snapshot(_state),
		"expansion": _expansion_view(),
		"expedition": ExpeditionBook.snapshot(_state, _store),
		"objects": [],
		"customers": [],
		"stats": _state.stats.duplicate(true),
		"tips": Tips.snapshot(_state, _objects()),
		"workshop": WorkshopBook.snapshot(_state),
	}
	var floor_offer := FloorBook.offer(_state)
	if not floor_offer.is_empty(): result.shop.offers.push_front(floor_offer)
	var jar_offer := Tips.upgrade_offer(_state)
	if not jar_offer.is_empty(): result.shop.offers.append(jar_offer)
	var index := _service_index()
	var chef_views := {}
	for original in _objects():
		var object: Dictionary = original.duplicate(true)
		if object.kind in ["chef", "seat"]:
			var service := _chef_service(original, index) if object.kind == "chef" else _seat_service(original, index)
			object.active = service.active
			object.inactive_reason = service.reason
		if object.kind == "chef":
			object.merge(_chef_view(chef_views, object.id), true)
			object.preparation_seconds = Chefs.duration(_store, _configuration, object.id)
			object.preparation = clampf(float(Chefs.station(_store, object.id).progress), 0.0, 1.0) if float(object.preparation_seconds) > 0.0 else 0.0
			object.erase("preparation_elapsed")
		elif object.kind == "belt":
			object.travel_progress = clampf(float(object.travel_elapsed) / float(_configuration.service.belt_seconds_per_cell), 0.0, 1.0)
			object.incoming_id = str(index.upstream.get(object.id, [{}])[0].get("id", ""))
			object.erase("travel_elapsed")
		result.objects.append(object)
	result.inventory = _inventory_snapshot(chef_views)
	result.editor.belt_targets = _belt_targets()
	for customer in _customers():
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
			"tea_phase": customer.tea_phase, "tea_cup": customer.tea_cup,
			"tea_progress": clampf(1.0 - float(customer.tea_elapsed) / maxf(0.001, float(Tips.definition().tea.request_seconds)), 0.0, 1.0) if customer.tea_phase == "requested" else 0.0,
		}
		Doorway.present(visible, customer, float(_configuration.service.walking_cells_per_second))
		result.customers.append(visible)
	return result

func _expansion_view() -> Dictionary:
	# Only clearance/reveal and floor geometry affect this map. Service clocks,
	# coins and camera change every frame; none needs another neighborhood scan.
	var stamp := {"store": _store.get_instance_id(), "expansion": _store.revision("slice:expansion"), "floor": _configuration.floor.hash()}
	if _expansion_view_cache.is_empty() or _expansion_view_state != stamp:
		_expansion_view_cache = Expansion.snapshot(_configuration, _state)
		_expansion_view_state = stamp
	# Snapshot consumers own their dictionaries and cannot change later frames.
	return _expansion_view_cache.duplicate(true)

func save_data() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"configuration": _configuration.duplicate(true),
		"engine": _store.save(),
		"remainder": _remainder,
		# JSON numbers cannot exactly hold a 64-bit generator state.
		"random_state": str(_random.state),
	}

## A save in one flat dictionary, for tools, tests and inspection: `state`
## holds the session's values, every slice, and the layout and guest lists;
## `engine` keeps the chef tables and the run world. restore() accepts it.
static func flat_view(data: Dictionary) -> Dictionary:
	var store := _new_store()
	if data.get("format") == "flat" or not data.get("engine") is Dictionary or not store.load_saved(data.engine) or not store.slice("core") is Dictionary:
		return data.duplicate(true)
	var state: Dictionary = store.slice("core").duplicate(true)
	for name in SLICES:
		if store.slice(name) != null: state[name] = store.slice(name).duplicate(true)
	Layout.hydrate(state, store)
	Customers.hydrate(state, store)
	var engine: Dictionary = data.engine.duplicate(true)
	engine.slices = {}
	for component in ["layout", "customer"]: engine.get("worlds", {}).get(Chefs.WORLD, {}).get("tables", {}).erase(component)
	return {"format": "flat", "version": data.get("version"), "configuration": data.get("configuration", {}).duplicate(true), "state": state,
		"engine": engine, "remainder": data.get("remainder"), "random_state": data.get("random_state")}

## The save a flat view describes. Pure conversion; restore() validates it.
static func _from_flat(flat: Dictionary) -> Dictionary:
	if not flat.get("state") is Dictionary or not flat.get("engine") is Dictionary: return {}
	var state: Dictionary = flat.state.duplicate(true)
	var engine: Dictionary = flat.engine.duplicate(true)
	if not engine.get("worlds") is Dictionary: return {}
	engine.slices = {}
	for name in SLICES:
		if state.has(name): engine.slices[name] = {"version": SLICES[name], "data": state[name]}
		state.erase(name)
	if not engine.worlds.get(Chefs.WORLD) is Dictionary: engine.worlds[Chefs.WORLD] = {"next_id": 1, "tables": {}}
	var tables: Dictionary = engine.worlds[Chefs.WORLD].get("tables", {})
	tables.layout = {"version": 1, "rows": state.get("objects", [])}
	tables.customer = {"version": 1, "rows": state.get("customers", [])}
	engine.worlds[Chefs.WORLD].tables = tables
	state.erase("objects")
	state.erase("customers")
	engine.slices.core = {"version": 1, "data": state}
	return {"version": flat.get("version"), "configuration": flat.get("configuration"), "engine": engine, "remainder": flat.get("remainder"), "random_state": flat.get("random_state")}

## Values a save leaves out because they follow from others.
func _derive(state: Dictionary, store: Store, config: Dictionary) -> bool:
	if not _nonnegative_integer(state.get("step_index")) or not state.get("stats") is Dictionary or not _nonnegative_integer(state.stats.get("sales")) or not _nonnegative_integer(state.stats.get("arrivals")) or not state.get("inventory") is Array: return false
	state.elapsed = int(state.step_index) * float(config.service.step_seconds)
	state.stats.served = int(state.stats.sales)
	state.next_customer_id = int(state.stats.arrivals) + 1
	if state.get("tips") == null:
		state.tips = Tips.initial(1)
		store.set_slice("tips", state.tips)
	# Saves from before the Workshop (#28) start with every level at 1.
	if state.get("workshop") == null:
		state.workshop = WorkshopBook.initial()
		store.set_slice("workshop", state.workshop)
	for stock in state.inventory:
		if stock is Dictionary and stock.get("kind") == "chef": stock.assigned = store.has_row(Layout.WORLD, "layout", str(stock.get("id")))
	return true

## A saved configuration with the current content's cell scale, or {} if invalid.
func _upgraded_configuration(saved: Dictionary) -> Dictionary:
	var current_content: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONTENT_PATH))
	if not current_content is Dictionary or not current_content.get("floor") is Dictionary:
		return {}
	var viewport_columns: Variant = current_content.floor.get("viewport_columns", current_content.floor.get("columns"))
	if not _nonnegative_integer(viewport_columns) or int(viewport_columns) < 1:
		return {}
	var configuration: Dictionary = saved.duplicate(true)
	# Cell scale is presentation, independent of the saved restaurant footprint.
	configuration.floor.viewport_columns = int(viewport_columns)
	return configuration if _valid_configuration(configuration) else {}

## Loads a save (or a flat view of one): everything comes from the store,
## derived values are recalculated, and every feature's rules are checked
## before anything changes. Any other format is rejected.
func restore(data: Dictionary) -> bool:
	if data.get("format") == "flat": data = _from_flat(data)
	if data.get("version") != SAVE_VERSION or not data.get("configuration") is Dictionary or not _valid_configuration(data.configuration) or not data.get("engine") is Dictionary:
		return false
	if not _finite_number(data.get("remainder")) or float(data.remainder) < 0.0 or float(data.remainder) >= float(data.configuration.service.step_seconds):
		return false
	if not data.get("random_state") is String or not data.random_state.is_valid_int() or data.random_state != str(int(data.random_state)):
		return false
	var configuration := _upgraded_configuration(data.configuration)
	if configuration.is_empty(): return false
	var store := _new_store()
	if not store.load_saved(data.engine) or not store.slice("core") is Dictionary: return false
	var state: Dictionary = store.slice("core")
	for name in SLICES:
		if store.slice(name) != null: state[name] = store.slice(name)
	if not _derive(state, store, configuration) or not _valid_store(store, configuration, state): return false
	_configuration = configuration
	_state = state
	_store = store
	_bind_store()
	_state.editor.erase("floor_brush")
	_normalize_restored_numbers()
	_remainder = float(data.remainder)
	_random.state = int(data.random_state)
	_rebuild_access()
	return true

## Every feature's rules on the store as it is: after loading, and after an
## edit. Reads the live tables and slices; copies nothing.
func _valid_store(store: Store, config: Dictionary, state: Dictionary = {}) -> bool:
	var view: Dictionary = (_state if state.is_empty() else state).duplicate()
	view.objects = Layout.rows(store)
	view.customers = Customers.rows(store)
	if not view.get("recipe_book") is Dictionary or not view.get("editor") is Dictionary: return false
	if not Chefs.valid(store, config) or not Chefs.matches(view, store) or not Chefs.valid_recipes(store, config, view.recipe_book) or not ExpeditionBook.shield_valid(store): return false
	if not FloorBook.valid(config, view) or not view.editor.get("floor_brush", "") is String: return false
	if view.editor.get("floor_brush", "") != "" and not view.editor.floor_brush in view.floor_styles.owned: return false
	if not ShopBook.valid(view) or not Expansion.valid(config, view) or not ExpeditionBook.valid(view): return false
	if not Tips.valid(view) or not _valid_cash(view, config) or not WorkshopBook.valid(view): return false
	if not StaffBook.valid(config, view, store) or not RecipeBook.valid(config, view): return false
	return _valid_saved_state(view, config, store)

func _normalize_restored_numbers() -> void:
	ShopBook.normalize(_state)
	ExpeditionBook.normalize(_state)
	Tips.normalize(_state)
	WorkshopBook.normalize(_state)
	# A pour sheet is not saved: a guest saved mid-pour is asking again.
	for customer in Customers.rows(_store):
		if customer.get("tea_phase") == "pouring": customer.tea_phase = "requested"
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
		if entry.kind == "chef" and entry.get("stored_object") is Dictionary:
			entry.stored_object.x = int(entry.stored_object.x)
			entry.stored_object.y = int(entry.stored_object.y)
	for field in _state.stats:
		_state.stats[field] = int(_state.stats[field])
	for objects in [_configuration.objects, _objects()]:
		for object in objects:
			object.x = int(object.x)
			object.y = int(object.y)
	for customer in _customers():
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
	Development.initialize(_state)
	ShopBook.initialize(_state)
	_state.tips = Tips.initial(_staff_seed)
	FloorBook.initialize(_state,_staff_seed)
	Expansion.initialize(_configuration,_state)
	ExpeditionBook.initialize(_state,_staff_seed)
	_state.workshop = WorkshopBook.initial()
	BeltRoutes.initialize(_state.objects)
	_store = _new_store()
	Chefs.extract(_state, _store, _configuration)
	Layout.extract(_state, _store)
	Customers.extract(_state, _store)
	_extract_slices(_state, _store)
	_bind_store()
	_remainder = 0.0
	_rebuild_access()

func _transition_seconds(key: String) -> float:
	# A configuration without a duration (small test fixtures) uses an
	# instant transition.
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
	var stations: Dictionary = {}
	for chef in _objects():
		if chef.kind != "chef":
			continue
		if stations.is_empty(): stations = _store.write(Chefs.WORLD, "station")
		var work: Dictionary = stations[chef.id]
		work.elapsed = _clock_advance(float(work.elapsed), delta)
		if not _chef_service(chef).active:
			_enter_station(work, "idle")
			continue
		if work.held_dish == null:
			_enter_station(work, "working")
			# Progress is a fraction of the dish, so a level-up never rescales it.
			var duration := Chefs.duration(_store, _configuration, chef.id)
			work.progress = minf(1.0, _clock_advance(float(work.progress), delta / duration))
			if float(work.progress) + 0.000000001 >= 1.0:
				work.progress = 1.0
				work.held_dish = {"id": "dish-%s" % _state.next_dish_id, "recipe_id": work.recipe_id}
				_state.next_dish_id += 1
				events.append({"type": "prepared", "chef_id": chef.id, "dish_id": work.held_dish.id})
		if work.held_dish == null:
			continue
		var loading := _facing_object(chef)
		var approaching := BeltRoutes.incoming(_objects(), str(loading.get("id", "")))
		if loading.get("kind") != "belt" or loading.dish != null or (not approaching.is_empty() and approaching.dish != null and float(approaching.travel_elapsed) > 0.0):
			_enter_station(work, "holding")
			continue
		var loading_duration := _transition_seconds("loading_seconds")
		if loading_duration > 0.0:
			if work.machine != "loading":
				_enter_station(work, "loading")
				continue
			work.elapsed = minf(loading_duration, float(work.elapsed))
			if float(work.elapsed) + 0.000000001 < loading_duration:
				continue
		# One ownership transfer after the visible loading motion. The plate is
		# never simultaneously present in the chef's hands and on the belt.
		loading.dish = work.held_dish
		loading.travel_elapsed = 0.0
		work.held_dish = null
		work.progress = 0.0
		_enter_station(work, "working")
		events.append({"type": "loaded", "chef_id": chef.id, "belt_id": loading.id, "dish_id": loading.dish.id})

## Station states double as the chef's animation; the clock restarts on change.
static func _enter_station(work: Dictionary, state: String) -> void:
	if work.machine != state:
		work.machine = state
		work.elapsed = 0.0

func _step_belts(delta: float, events: Array) -> void:
	var duration := float(_configuration.service.belt_seconds_per_cell)
	var transfers: Array = []
	var moving := {}
	for tile in _objects():
		if tile.kind == "belt" and tile.dish != null and not tile.next_id.is_empty(): moving[tile.id] = true
	moving = BeltRoutes.vacating_tiles(_objects(), moving)
	var ready := {}
	# A free endpoint releases its upstream train; a closed occupied cycle can
	# advance as one train. A blocked endpoint freezes its complete queue.
	for tile in _objects():
		if tile.kind != "belt" or tile.dish == null:
			continue
		if tile.next_id.is_empty():
			continue
		if not moving.get(tile.id, false): continue
		tile.travel_elapsed = minf(duration, _clock_advance(float(tile.travel_elapsed), delta))
		if float(tile.travel_elapsed) + 0.000000001 >= duration: ready[tile.id] = true
	ready = BeltRoutes.vacating_tiles(_objects(), ready)
	for tile in _objects():
		if tile.kind == "belt" and ready.get(tile.id, false):
			transfers.append({"from": tile, "to": _object_by_id(tile.next_id), "dish": tile.dish})
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

func _entrance_path(entrance: Vector2i, seat: Dictionary, cells := {}) -> Array:
	# Prefer walking straight off this side of the threshold before turning
	# toward the seat. Furniture may require a valid sideways alternative.
	if cells.is_empty(): cells = _occupancy()
	if Doorway.enabled(_configuration.floor):
		var apron := entrance + Vector2i.DOWN
		if not cells.has(apron):
			var onward := _walk_path(apron, _point(seat), seat.id, cells)
			if not onward.is_empty():
				onward.push_front({"x": apron.x, "y": apron.y})
				return onward
	return _walk_path(entrance, _point(seat), seat.id, cells)

func _rebuild_access() -> void:
	_access_paths.clear()
	var cells := _occupancy()
	for object in _objects():
		if object.kind != "seat": continue
		_access_paths[object.id] = []
		for entrance in _entrance_lanes():
			var route := _entrance_path(entrance, object, cells)
			if not route.is_empty():
				_access_paths[object.id] = route
				break

func _chef_recipe(chef: Dictionary, index := {}) -> String:
	if index.has("recipes"): return str(index.recipes.get(chef.id, ""))
	return str(Chefs.station(_store, str(chef.id)).get("recipe_id", ""))

func _chef_service(chef: Dictionary, index := {}) -> Dictionary:
	if _chef_recipe(chef, index).is_empty(): return {"active":false, "reason":"no_recipe"}
	var front := _facing_object(chef) if index.is_empty() else _indexed_facing(chef, index)
	if front.get("kind") != "belt":
		return {"active": false, "reason": "no_belt"}
	return {"active": true, "reason": ""}

func _service_index() -> Dictionary:
	# One pass serves a batch of read-only service queries: cell occupancy and
	# reverse belt links, replacing a linear lookup per cell and route step.
	var upstream := {}
	for object in _objects():
		if object.kind == "belt" and not str(object.get("next_id", "")).is_empty():
			if not upstream.has(object.next_id): upstream[object.next_id] = []
			upstream[object.next_id].append(object)
	var recipes := {}
	var stations: Dictionary = _store.table(Chefs.WORLD, "station")
	for id in stations: recipes[id] = stations[id].recipe_id
	return {"cells": _occupancy(), "upstream": upstream, "recipes": recipes}

func _indexed_facing(object: Dictionary, index: Dictionary) -> Dictionary:
	if object.is_empty(): return {}
	return index.cells.get(_point(object) + DIRECTIONS[object.facing], {})

func _upstream_belts(target_id: String, index: Dictionary) -> Dictionary:
	# Belts whose route reaches target_id, including the target itself.
	var reached := {target_id: true}
	var queue: Array = [target_id]
	var cursor := 0
	while cursor < queue.size():
		for tile in index.upstream.get(queue[cursor], []):
			if not reached.has(tile.id):
				reached[tile.id] = true
				queue.append(tile.id)
		cursor += 1
	return reached

func _seat_service(seat: Dictionary, index := {}) -> Dictionary:
	var result := {"active": false, "reason": "no_belt", "ready": [], "menu": [], "front": ""}
	if index.is_empty(): index = _service_index()
	var front := _indexed_facing(seat, index)
	if front.get("kind") != "belt":
		return result
	result.front = front.dish.recipe_id if front.dish != null else ""
	if _access_paths.get(seat.id, []).is_empty():
		result.reason = "no_access"
		return result
	var reaching := _upstream_belts(front.id, index)
	for object in _objects():
		if object.kind == "belt" and object.dish != null and reaching.has(object.id):
			if not result.ready.has(object.dish.recipe_id):
				result.ready.append(object.dish.recipe_id)
		elif object.kind == "chef" and _chef_service(object, index).active and reaching.has(_indexed_facing(object, index).id):
			var recipe := _chef_recipe(object, index)
			if not result.menu.has(recipe):
				result.menu.append(recipe)
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
	customer.merge(Tips.VISIT_FIELDS.duplicate(true), true)

func _arrival_seat_choices(customer: Dictionary = {}) -> Array:
	var choices: Array = []
	var index := _service_index()
	for seat in _objects():
		if seat.kind != "seat" or _seat_reserved(seat.id):
			continue
		var path: Array = _entrance_path(Doorway.anchor(customer, _configuration.floor), seat, index.cells) if customer.has("door_lane") else _access_paths.get(seat.id, [])
		var service := _seat_service(seat, index)
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
	for customer in _customers():
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
	_store.set_row(Customers.WORLD, "customer", str(customer.id), customer)
	_state.stats.arrivals += 1
	events.append({"type": "arrived", "customer_id": customer.id, "seat_id": customer.seat_id, "preferred_recipe_id": preferred})
	var jitter := float(_configuration.service.arrival_jitter_seconds)
	var multiplier := 1.0
	if Expansion.enabled(_configuration.floor): multiplier = Expansion.arrival_multiplier(_state,_configuration.floor)
	_state.arrival_remaining = (float(_configuration.service.arrival_seconds) + _random.randf_range(-jitter, jitter)) / multiplier

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
	for customer in _customers():
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
					if customer.preferred_recipe_id.is_empty():
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
				_step_tea(customer, delta, events)
				# Waiting for tea: passing dishes stay on the belt and impatience pauses.
				if customer.tea_phase in ["requested", "pouring"]: continue
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
		_store.remove_row(Customers.WORLD, "customer", str(customer.id))

func _take_dish(customer: Dictionary, seat: Dictionary, tile: Dictionary, events: Array) -> void:
	var matched: bool = not customer.first_dish_received and customer.preference_phase == "active" and tile.dish.recipe_id == customer.preferred_recipe_id
	customer.meal_dish = tile.dish
	customer.meal_elapsed = 0.0
	customer.meal_duration = float(_configuration.service.eating_seconds)
	customer.meal_fullness = 1.0
	var jitter := _customer_number("eating_jitter_seconds")
	customer.meal_duration += _random.randf_range(-jitter, jitter)
	customer.meal_fullness = _random.randf_range(_customer_number("dish_fullness_min"), _customer_number("dish_fullness_max"))
	customer.first_dish_received = true
	customer.waiting_elapsed = 0.0
	customer.restless = false
	customer.phase = "eating"
	_set_visual(customer, "eat")
	if matched:
		customer.requested_dish_id = str(customer.meal_dish.id)
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
	_decide_tip(customer)
	customer.yielding = false
	_set_visual(customer, "stand-up" if _transition_seconds("standing_seconds") > 0.0 else "walk")
	_replan_navigation(customer)

func _finish_meal(customer: Dictionary, events: Array) -> void:
	var dish: Dictionary = customer.meal_dish
	var price := int(_configuration.recipes[dish.recipe_id].price)
	_state.coins += price
	_state.stats.sales += 1
	_state.stats.served += 1
	customer.bill = int(customer.bill) + price
	# Eating the dish they asked for raises the tip chance; serving it is not enough.
	if str(dish.id) == str(customer.requested_dish_id): customer.request_eaten = true
	customer.fullness += customer.meal_fullness
	# Consume and credit together: no reward is left pending in a save.
	customer.meal_dish = null
	customer.meal_elapsed = 0.0
	customer.meal_fullness = 0.0
	if float(customer.fullness) + 0.000000001 >= float(customer.appetite_target):
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

func _foot_on_floor(position: Vector2, seat_id: String, objects: Array, floor_data: Dictionary, saved_state: Dictionary = {}) -> bool:
	var cell := Vector2i(floori(position.x + 0.5), floori(position.y + 0.5))
	if not _inside(cell, floor_data, saved_state):
		return false
	for object in objects:
		if _point(object) == cell:
			return object.kind == "seat" and object.id == seat_id
	return true

func _walking_position_clear(position: Vector2, customer: Dictionary) -> bool:
	# Guests can pass through each other. Only furniture and floor boundaries
	# constrain walking, so another visitor can never deadlock a valid route.
	return _foot_on_floor(position, customer.seat_id, _objects(), _configuration.floor)

func _initialize_navigation(customer: Dictionary, origin: Vector2) -> void:
	customer.navigation_mode = "goal"
	customer.wander_elapsed = 0.0
	customer.path_origin = {"x": origin.x, "y": origin.y}
	customer.navigation_retry_elapsed = 0.0
	customer.wander_cursor = 0

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
				if not _foot_on_floor(position.lerp(Vector2(cell), fraction), customer.seat_id, _objects(), _configuration.floor):
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
	if customer.phase != "leaving" and _seat_reserved(str(customer.seat_id), customer.id):
		# Another guest took the stool while this one was cut off from it.
		return _try_reseat(customer)
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
	_decide_tip(customer)
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
	for object in _objects():
		blocked[_point(object)] = true
	# Each of the at most two adjacent anchors needs one flood fill; only the
	# selected target's route is rebuilt from its predecessor map.
	reachable = Navigation.flood(_navigation_anchors(customer), position, _walkable(), blocked)
	var choices: Array[Vector2i] = []
	# Preserve stable row order independently of flood-fill and Dictionary order.
	for y in range(int(_configuration.floor.rows)):
		for x in range(Expansion.columns(_configuration.floor)):
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
	var route := Navigation.route_to(reachable, target)
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

func _walk_path(start: Vector2i, goal: Vector2i, goal_object_id: String = "", cells := {}) -> Array:
	if cells.is_empty(): cells = _occupancy()
	# The goal may be the stool itself; any other occupied cell blocks.
	var occupant: Dictionary = cells.get(goal, {})
	var goals := {} if not occupant.is_empty() and occupant.id != goal_object_id else {goal: true}
	return Navigation.find_path(start, goals, _walkable(), cells)

func _walkable() -> Dictionary:
	var key := [_store.get_instance_id(), _store.revision("slice:expansion"), _configuration.floor.hash()]
	if key != _walkable_key:
		_walkable_cells = {}
		for y in range(int(_configuration.floor.rows)):
			for x in range(Expansion.columns(_configuration.floor)):
				if _inside(Vector2i(x, y), _configuration.floor): _walkable_cells[Vector2i(x, y)] = true
		_walkable_key = key
	return _walkable_cells

func _seat_reserved(seat_id: String, excluding_customer: String = "") -> bool:
	if seat_id.is_empty():
		return false
	for customer in _customers():
		if customer.id == excluding_customer: continue
		if customer.seat_id == seat_id and _holds_seat(customer):
			return true
	return false

static func _holds_seat(customer: Dictionary) -> bool:
	return Customers.holds_seat(customer)

func _object_by_id(object_id: String) -> Dictionary:
	var found: Variant = _store.table(Layout.WORLD, "layout").get(object_id)
	return {} if found == null else found

## Layout rows in placement order.
func _objects() -> Array:
	return Layout.rows(_store)

## Guests in arrival order.
func _customers() -> Array:
	return Customers.rows(_store)

func _occupancy() -> Dictionary:
	# The first object per cell, as _object_at finds it.
	var cells := {}
	for object in _objects():
		var cell := _point(object)
		if not cells.has(cell): cells[cell] = object
	return cells

func _object_at(cell: Vector2i) -> Dictionary:
	for object in _objects():
		if int(object.x) == cell.x and int(object.y) == cell.y:
			return object
	return {}

func _facing_object(object: Dictionary) -> Dictionary:
	if object.is_empty():
		return {}
	return _object_at(Vector2i(int(object.x), int(object.y)) + DIRECTIONS[object.facing])

func _point(value: Dictionary) -> Vector2i:
	return Vector2i(int(value.x), int(value.y))

func _inside(cell: Vector2i, floor_data: Dictionary, saved_state: Dictionary = {}) -> bool:
	return Expansion.usable(_state if saved_state.is_empty() else saved_state,floor_data,cell,true)

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

## `placements_only`: chef rows carry only their placement (store mode).
func _valid_objects(objects: Array, config: Dictionary, placements_only := false) -> bool:
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
		if object.kind == "chef" and not placements_only and (not object.get("recipe_id") is String or (object.recipe_id != "" and not config.recipes.has(object.recipe_id))):
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
	return int(value.x) < Expansion.columns(floor_data) and int(value.y) >= int(floor_data.get("backdrop_rows",0)) and int(value.y) < int(floor_data.rows)

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

## Validates the live restaurant after an edit, with chef records rebuilt for
## the validators of features that have not moved to the store yet.
## Checks the live state after an edit. Cash an edit covered is collected
## first (furniture never sits on cash), and reported by command().
func _valid_runtime_state() -> bool:
	_swept_cash.append_array(_sweep_cash())
	return _valid_store(_store, _configuration)

## Layout, guests and the session's own values. Chefs are read from the store;
## layout rows carry only their placement.
func _valid_saved_state(state: Dictionary, config: Dictionary, store: Store) -> bool:
	if not _valid_editor_state(state, config, store):
		return false
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
	if not state.get("objects") is Array or not state.get("customers") is Array or not _valid_objects(state.objects, config, true):
		return false
	if int(state.stats.arrivals) < state.customers.size():
		return false
	var dish_ids: Dictionary = {}
	var seats: Dictionary = {}
	var occupants: Dictionary = {}
	for id in Chefs.ids(store):
		if not _valid_dish(Chefs.station(store, id).held_dish, config.recipes, dish_ids): return false
	for object in state.objects:
		occupants[_point(object)] = object
		# Chef stations are checked by the chef feature.
		if object.kind == "chef": continue
		if object.kind == "belt":
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
		var entrance_wait: bool = customer.get("phase") == "entrance_wait"
		if entrance_wait:
			if entrance_wait_reserved or not _valid_entrance_wait(customer, config):
				return false
			entrance_wait_reserved = true
		elif customer.get("phase") == "standing":
			if customer.get("seat_id") != "": return false
		elif customer.get("phase") == "leaving" and customer.get("seat_id") == "":
			if customer.get("visual_phase") != "walk": return false
		elif not seats.has(customer.get("seat_id")) or not Customers.is_phase(customer.get("phase")) or customer.phase in ["standing", "entrance_wait"]:
			return false
		if not customer.get("layout_pending") is bool or not _finite_number(customer.get("standing_elapsed")) or float(customer.standing_elapsed) < 0.0: return false
		if (not _finite_number(customer.get("entrance_wait_elapsed")) or (not entrance_wait and float(customer.entrance_wait_elapsed) != 0.0)):
			return false
		if (not _finite_number(customer.get("wander_elapsed")) or float(customer.wander_elapsed) < 0.0 or (customer.get("navigation_mode") != "wander" and float(customer.wander_elapsed) != 0.0)):
			return false
		if not _valid_visit(customer, config):
			return false
		if not DIRECTIONS.has(customer.get("facing")) or not _finite_number(customer.get("visual_elapsed")) or float(customer.visual_elapsed) < 0.0:
			return false
		if not customer.get("visual_phase") in Customers.visuals(customer.phase):
			return false
		if customer.visual_phase in ["sit-down", "stand-up"]:
			var seconds := float(config.service.get("sitting_seconds" if customer.visual_phase == "sit-down" else "standing_seconds", 0.0))
			if seconds <= 0.0 or float(customer.visual_elapsed) >= seconds:
				return false
		if not entrance_wait and not customer.seat_id.is_empty() and _holds_seat(customer):
			if reservations.has(customer.seat_id):
				return false
			reservations[customer.seat_id] = true
		if not _finite_number(customer.get("x")) or not _finite_number(customer.get("y")):
			return false
		if not _inside(Vector2i(floori(customer.x), floori(customer.y)), config.floor, state):
			return false
		if not _nonnegative_integer(customer.get("appearance")) or int(customer.appearance) > 3 or not _nonnegative_integer(customer.get("path_index")):
			return false
		if not customer.get("path") is Array or int(customer.path_index) > customer.path.size():
			return false
		for point in customer.path:
			if not _valid_point(point, config.floor) or not Expansion.usable(state,config.floor,_point(point),true):
				return false
		if entrance_wait:
			if not _valid_customer_navigation(customer, {}, occupants, config):
				return false
		elif not _valid_customer_navigation(customer, seats.get(customer.seat_id, {}), occupants, config):
			return false
		if not _foot_on_floor(Vector2(float(customer.x), float(customer.y)), customer.seat_id, state.objects, config.floor, state) or not _foot_on_floor(_render_position(customer), customer.seat_id, state.objects, config.floor, state):
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
	# The counter must advance past every surviving ID before new food spawns.
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

func _valid_visit(customer: Dictionary, config: Dictionary) -> bool:
	if not Tips.valid_visit(customer): return false
	for key in ["first_dish_received", "restless", "yielding"]:
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
	if not customer.get("preferred_recipe_id") is String or (customer.phase != "entrance_wait" and not pending_admission and not config.recipes.has(customer.preferred_recipe_id)):
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
	if float(customer.appetite_target) < float(config.customers.fullness_min) or float(customer.appetite_target) > float(config.customers.fullness_max):
		return false
	if customer.phase != "leaving" and float(customer.fullness) + 0.000000001 >= float(customer.appetite_target):
		return false
	if customer.get("meal_dish") != null and (float(customer.meal_fullness) < float(config.customers.dish_fullness_min) or float(customer.meal_fullness) > float(config.customers.dish_fullness_max)):
		return false
	return absf(float(customer.meal_duration) - float(config.service.eating_seconds)) <= float(config.customers.eating_jitter_seconds) + 0.000001

func _valid_entrance_wait(customer: Dictionary, config: Dictionary) -> bool:
	if customer.get("seat_id") != "" or customer.get("first_dish_received") != false or customer.get("preferred_recipe_id") != "" or customer.get("preference_phase") != "pending":
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
	if previous.x < 0.0 or previous.y < 0.0 or previous.x > Expansion.columns(config.floor) - 1 or previous.y > int(config.floor.rows) - 1:
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

func _chef_view(views: Dictionary, id: String) -> Dictionary:
	if not views.has(id): views[id] = Chefs.record(_store, _configuration, id)
	return views[id]

func _inventory_snapshot(chef_views := {}) -> Array:
	var result: Array = []
	for entry in _state.inventory:
		var item: Dictionary = entry.duplicate(true)
		if entry.kind == "chef": Chefs.present_stock(item, _chef_view(chef_views, entry.id))
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

func _valid_editor_state(state: Dictionary, config: Dictionary, store: Store = null) -> bool:
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
	if not objects is Array or not _valid_objects(objects, config, store != null):
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
	for id in state.get("staff",{}).get("dismissed",{}):known_chefs.erase(id)
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
			if store != null:
				# The chef's own records are checked by the chef feature.
				if not entry.get("assigned") is bool or entry.assigned != placed.has(entry.id) or not Chefs.exists(store, entry.id) or not DIRECTIONS.has(entry.get("facing")): return false
				if int(entry.count) != (0 if entry.assigned else 1) or (entry.assigned and placed[entry.id].get("kind") != "chef"): return false
				continue
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
		var expected := int(known_stock[identity].count) + int(state.get("shop",{}).get("purchased",{}).get(identity,0))
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
			_state.editor.erase("floor_brush")
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
	if not Expansion.usable(_state,_configuration.floor,cell,true): return "uncleared_floor"
	if not Doorway.enabled(_configuration.floor) and cell == _point(_configuration.floor.entrance):
		return "entrance"
	var other := _object_at(cell)
	if not other.is_empty() and other.id != excluding_id:
		return "occupied"
	for customer in _customers():
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
	BeltRoutes.connect_tiles(_objects(), source, target)
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
	if not _valid_runtime_state():
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
		BeltRoutes.detach(_objects(), object)
	if type == "editor_place":
		if stock.kind == "chef":
			object = {"id": stock.id, "kind": "chef", "facing": stock.facing}
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
		_store.set_row(Layout.WORLD, "layout", str(object.id), object)
	elif type == "editor_move":
		object.x = int(request.x)
		object.y = int(request.y)
	elif type == "editor_rotate":
		var facings := ["north", "east", "south", "west"]
		if object.kind == "belt":
			BeltRoutes.detach(_objects(), object)
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
		elif object.kind == "belt" and object.dish != null:
			_state.discarded_dishes += 1
		# An unassigned chef keeps their staff records; anything else returned
		# to inventory leaves the restaurant, and references to it follow their
		# declared policies (a guest on a removed stool stands up).
		if object.kind == "chef": _store.remove_row(Layout.WORLD, "layout", str(object.id))
		else: _store.delete(Layout.WORLD, str(object.id))
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
		for other in _objects():
			if other.kind == "belt" and other.next_id == object.id:
				other.travel_elapsed = 0.0
	if type in ["editor_move", "editor_rotate"] and object.kind == "chef":
		Chefs.interrupt_loading(_store, object.id)
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
	for customer in _customers():
		if customer.phase in ["walking", "leaving"]:
			_replan_navigation(customer)
		else:
			_clear_seated_route(customer)
	if not _valid_runtime_state():
		_state = before
		_rebuild_access()
		return _editor_fail("invalid_state")
	return {"ok": true, "id": object.id}

func _initialize_customer_layout(customer: Dictionary) -> void:
	customer.layout_pending = false
	customer.standing_elapsed = 0.0

func _customer_by_id(identity: String) -> Dictionary:
	var found: Variant = _store.table(Customers.WORLD, "customer").get(identity)
	return {} if found == null else found

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
	return not _customers().any(func(guest): return guest.id != excluding and _customer_touches(guest, cell))

func _nearest_customer_cell(customer: Dictionary) -> Dictionary:
	var best := {}
	var distance := INF
	var origin := Vector2(float(customer.x), float(customer.y))
	for y in range(int(_configuration.floor.rows)):
		for x in range(Expansion.columns(_configuration.floor)):
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

## A guest on a removed stool stands up (the `customer.seat_id` reference policy).
func _on_seat_removed(_world: String, referrer: String, _component: String, _field: String, _seat: String) -> void:
	_stand_customer(_customer_by_id(referrer))

func _bind_store() -> void:
	_store.on_ref_removed("customer", _on_seat_removed)

## Occupied stools carry their seated guest when moved.
func _carry_or_release_seat(object: Dictionary, type: String) -> void:
	if object.get("kind") != "seat" or type in ["editor_place", "editor_remove"]: return
	for customer in _customers():
		if customer.seat_id != object.id: continue
		if customer.phase in ["waiting", "eating"] or customer.visual_phase == "stand-up":
			# The action and all visit/meal clocks remain on their current frame.
			customer.x = float(object.x)
			customer.y = float(object.y)
			customer.facing = object.facing
			customer.render_offset_x = 0.0
			customer.render_offset_y = 0.0

func _resolve_customer_overlaps(object: Dictionary) -> bool:
	for customer in _customers():
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
	if _customers().any(func(guest): return guest.id != customer.id and _customer_touches(guest, cell)): return _editor_fail("customer_busy")
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
	if not _valid_runtime_state():
		_state = before
		return _editor_fail("invalid_state")
	return {"ok": true, "id": customer.id}

func _try_reseat(customer: Dictionary) -> bool:
	var best := {}
	var best_route := {}
	var length := INF
	for seat in _objects():
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

# ---------------------------------------------------------------- tips (#61)

## Seated guests who have had a dish may ask for tea once, between dishes (a
## dish already being eaten finishes first) and only once their other bubbles
## are done. Ignoring it lets the request lapse; an open pour stops its clock.
func _step_tea(customer: Dictionary, delta: float, events: Array) -> void:
	if not customer.first_dish_received or customer.tea_phase in ["served", "skipped", "missed", "pouring"]: return
	var tea: Dictionary = Tips.definition().tea
	if customer.tea_phase == "none":
		# One bubble at a time: a happy or preference bubble finishes first.
		if customer.preference_phase != "complete": return
		customer.tea_elapsed = _clock_advance(float(customer.tea_elapsed), delta)
		var delay := lerpf(float(tea.delay_min_seconds), float(tea.delay_max_seconds), Tips.roll(_state, str(customer.id), "tea-delay"))
		if float(customer.tea_elapsed) + 0.000000001 < delay: return
		customer.tea_elapsed = 0.0
		if Tips.roll(_state, str(customer.id), "tea") < float(tea.request_chance):
			var cups := Tea.cup_ids()
			customer.tea_cup = str(cups[mini(cups.size() - 1, int(Tips.roll(_state, str(customer.id), "tea-cup") * cups.size()))])
			customer.tea_phase = "requested"
			events.append(_customer_event("tea_requested", customer))
		else:
			customer.tea_phase = "skipped"
		return
	customer.tea_elapsed = _clock_advance(float(customer.tea_elapsed), delta)
	if float(customer.tea_elapsed) + 0.000000001 >= float(tea.request_seconds): _miss_tea(customer, events)

## An unanswered request lapses: the bubble goes and the guest eats again.
func _miss_tea(customer: Dictionary, events: Array) -> void:
	customer.tea_phase = "missed"
	customer.tea_elapsed = 0.0
	events.append(_customer_event("tea_missed", customer))

## Decided once, as a guest who bought food gets up to leave.
func _decide_tip(customer: Dictionary) -> void:
	if customer.tea_phase in ["requested", "pouring"]:
		customer.tea_phase = "missed"
		customer.tea_elapsed = 0.0
	if customer.tip_evaluated or int(customer.bill) <= 0: return
	customer.tip_evaluated = true
	if Tips.roll(_state, str(customer.id), "tip") >= Tips.chance(customer): return
	var value := Tips.amount(int(customer.bill))
	var seat := _object_by_id(str(customer.seat_id))
	var center := _point(seat) if not seat.is_empty() else Vector2i(roundi(float(customer.x)), roundi(float(customer.y)))
	var event := {"type": "tip", "customer_id": customer.id, "amount": value, "from_x": float(customer.x), "from_y": float(customer.y)}
	var open: Array[Vector2i] = []
	for cell in Tips.around(center):
		if _cash_cell_open(cell): open.append(cell)
	if not open.is_empty():
		var cell: Vector2i = open[mini(open.size() - 1, int(Tips.roll(_state, str(customer.id), "drop") * open.size()))]
		_state.tips.cash.append({"x": cell.x, "y": cell.y, "amount": value})
		event.merge({"destination": "floor", "accepted": value, "x": cell.x, "y": cell.y})
	else:
		var jar := Tips.jar_object(_objects())
		var accepted := mini(value, Tips.jar_room(_state)) if not jar.is_empty() else 0
		if accepted > 0:
			_state.tips.jar.balance = int(_state.tips.jar.balance) + accepted
			event.merge({"destination": "jar", "accepted": accepted, "x": int(jar.x), "y": int(jar.y), "full": Tips.jar_room(_state) == 0})
		else:
			event.merge({"destination": "lost", "accepted": 0})
	_pending_events.append(event)

## A floor tile that can hold a new pile: inside the open restaurant, not a
## doorway, free of furniture, belts and other cash.
func _cash_cell_open(cell: Vector2i) -> bool:
	if not Expansion.usable(_state, _configuration.floor, cell, true): return false
	if cell.y == int(_configuration.floor.entrance.y) and (cell == _point(_configuration.floor.entrance) or (Doorway.enabled(_configuration.floor) and cell.x in [4, 5])): return false
	return _object_at(cell).is_empty() and Tips.pile_at(_state, cell) < 0

## Collects piles a layout change has covered; returns them for presentation.
func _sweep_cash() -> Array:
	var covered: Array = []
	var kept: Array = []
	for pile in _state.tips.cash:
		var cell := Vector2i(int(pile.x), int(pile.y))
		if _object_at(cell).is_empty() and Expansion.usable(_state, _configuration.floor, cell, true): kept.append(pile)
		else: covered.append(pile)
	if covered.is_empty(): return []
	_state.tips.cash = kept
	_state.coins = int(_state.coins) + Tips.total(covered)
	return covered

func _valid_cash(state: Dictionary, config: Dictionary) -> bool:
	var occupied := {}
	for object in state.objects: occupied[_point(object)] = true
	for pile in state.tips.cash:
		var cell := Vector2i(int(pile.x), int(pile.y))
		if occupied.has(cell) or not Expansion.usable(state, config.floor, cell, true): return false
	return true

func _tip_command(request: Dictionary) -> Dictionary:
	match request.type:
		"tip_jar_upgrade":
			if _state.mode != "edit": return {"ok": false, "reason": "edit_required"}
			if not Tips.jar_owned(_state): return {"ok": false, "reason": "no_tip_jar"}
			var level := int(_state.tips.jar.level)
			if request.get("expected_level") != level: return {"ok": false, "reason": "stale_upgrade"}
			var cost := Tips.upgrade_cost(level)
			if cost < 0: return {"ok": false, "reason": "max_level"}
			if int(_state.coins) < cost: return {"ok": false, "reason": "not_enough_coins"}
			_state.coins = int(_state.coins) - cost
			_state.tips.jar.level = level + 1
			return {"ok": true, "level": level + 1, "cost": cost, "capacity": Tips.capacity(level + 1)}
	if _state.mode != "live": return {"ok": false, "reason": "live_required"}
	match request.type:
		"tea_pour_open":
			# Tapping the bubble dismisses it and stops its patience while the sheet is open.
			var customer := _customer_by_id(str(request.get("customer_id", "")))
			if customer.is_empty() or customer.tea_phase != "requested": return {"ok": false, "reason": "no_tea_request"}
			if not _customers().filter(func(c): return c.tea_phase == "pouring").is_empty(): return {"ok": false, "reason": "pour_open"}
			customer.tea_phase = "pouring"
			return {"ok": true, "customer_id": customer.id, "cup": customer.tea_cup}
		"tea_pour_cancel":
			# Closed before any tea flowed: the bubble returns with the patience it had.
			var customer := _customer_by_id(str(request.get("customer_id", "")))
			if customer.is_empty() or customer.tea_phase != "pouring": return {"ok": false, "reason": "no_pour"}
			customer.tea_phase = "requested"
			return {"ok": true, "customer_id": customer.id}
		"tea_pour_finish":
			var customer := _customer_by_id(str(request.get("customer_id", "")))
			if customer.is_empty() or customer.tea_phase != "pouring": return {"ok": false, "reason": "no_pour"}
			var grade := str(request.get("grade", ""))
			if not grade in Tea.GRADES or not _finite_number(request.get("fill")) or float(request.fill) < 0.0: return {"ok": false, "reason": "invalid_grade"}
			customer.tea_phase = "served"
			customer.tea_elapsed = 0.0
			customer.tea_grade = grade
			customer.tea_qualifies = Tea.qualifies(grade, float(request.fill))
			return {"ok": true, "customer_id": customer.id, "grade": grade, "qualifies": customer.tea_qualifies, "x": customer.x, "y": customer.y}
		"collect_cash":
			if not _finite_number(request.get("x")) or not _finite_number(request.get("y")): return {"ok": false, "reason": "invalid_cell"}
			var taken := Tips.take_around(_state, Vector2i(int(request.x), int(request.y)))
			if taken.is_empty(): return {"ok": false, "reason": "no_cash"}
			var value := Tips.total(taken)
			_state.coins = int(_state.coins) + value
			return {"ok": true, "amount": value, "piles": taken}
		"collect_jar":
			var jar := Tips.jar_object(_objects())
			if jar.is_empty(): return {"ok": false, "reason": "no_tip_jar"}
			var value := int(_state.tips.jar.balance)
			if value <= 0: return {"ok": false, "reason": "empty_jar"}
			_state.tips.jar.balance = 0
			_state.coins = int(_state.coins) + value
			return {"ok": true, "amount": value, "x": int(jar.x), "y": int(jar.y)}
	return {"ok": false, "reason": "unknown_command"}
