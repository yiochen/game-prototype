extends RefCounted
## Generic game state: worlds of component tables plus named singleton slices.
## Features own tables and slices; the store holds no game rules. It provides
## transactions, entity references with deletion policies, declared hooks,
## timed effects, revisions for derived caches, and versioned saving.
## See docs/state-architecture.md.

const EFFECTS := "effects"
## Returned for missing tables and rows, so lookups never allocate. Read-only.
const NONE := {}

## component -> {owner, durable, version, fields: {name: default}, refs: {field: {to, on_delete, soft}}, derived: [names], migrations: [Callable]}
var components: Dictionary = {}
## slice -> {owner, version, initial: Callable, migrations: [Callable], validate: Callable}
var slice_specs: Dictionary = {}
## world -> {"next_id": int, "tables": {component: {id: row}}}
var worlds: Dictionary = {}
var slices: Dictionary = {}
## "world/component" or "slice:name" -> int, bumped on every committed write.
var revisions: Dictionary = {}
var _hooks: Dictionary = {}
var _ref_handlers: Dictionary = {}
var _undo = null
var _touched: Dictionary = {}

## "persist": false keeps a table out of save(); its owner saves it elsewhere.
## JSON writers may sort keys, so a table whose row order matters declares
## "ordered": true and is saved as a list of rows, each carrying its "id".
func define_component(name: String, spec: Dictionary) -> void:
	var full := {"owner": "", "durable": true, "version": 1, "fields": {}, "refs": {}, "derived": [], "migrations": [], "persist": true, "ordered": false}
	full.merge(spec, true)
	components[name] = full

func define_slice(name: String, spec: Dictionary) -> void:
	# "persist": false keeps a slice out of save(); its owner saves it elsewhere.
	# "encode" and "decode" convert between the live value and its saved form.
	var full := {"owner": "", "version": 1, "initial": func(): return {}, "migrations": [], "validate": Callable(), "persist": true, "encode": Callable(), "decode": Callable()}
	full.merge(spec, true)
	slice_specs[name] = full
	if not slices.has(name): slices[name] = full.initial.call()

func create_world(name: String) -> void:
	if worlds.has(name): return
	_remember_world(name)
	worlds[name] = {"next_id": 1, "tables": {}}

func drop_world(name: String) -> void:
	if not worlds.has(name): return
	_remember_world(name)
	worlds.erase(name)

## A new entity id, unique for the life of the world. Ids are never reused.
func spawn(world: String, prefix: String) -> String:
	if _undo != null and not _undo.has("next_id:" + world): _undo["next_id:" + world] = {"value": worlds[world].next_id, "present": true}
	var data: Dictionary = worlds[world]
	var id := "%s-%s" % [prefix, int(data.next_id)]
	data.next_id = int(data.next_id) + 1
	return id

# --- Reading and writing ----------------------------------------------------

func table(world: String, component: String) -> Dictionary:
	var data: Variant = worlds.get(world)
	if data == null: return NONE
	var rows: Variant = data.tables.get(component)
	return NONE if rows == null else rows

func row(world: String, component: String, id: String) -> Dictionary:
	var found: Variant = table(world, component).get(id)
	return NONE if found == null else found

func has_row(world: String, component: String, id: String) -> bool:
	return table(world, component).has(id)

## The mutable table. Call before changing it, so a transaction can roll back.
func write(world: String, component: String) -> Dictionary:
	var tables: Dictionary = worlds[world].tables
	var key := world + "/" + component
	_remember(key, tables.get(component))
	if not tables.has(component): tables[component] = {}
	_touched[key] = true
	return tables[component]

## Stores `value` itself (callers may keep editing it), adding missing defaults.
func set_row(world: String, component: String, id: String, value: Dictionary) -> void:
	value.merge(components.get(component, {}).get("fields", {}).duplicate(true), false)
	write(world, component)[id] = value

func remove_row(world: String, component: String, id: String) -> void:
	if has_row(world, component, id): write(world, component).erase(id)

func entity_ids(world: String) -> Array:
	var seen := {}
	for component in worlds.get(world, {}).get("tables", {}).values():
		for id in component: seen[id] = true
	var ids := seen.keys()
	ids.sort()
	return ids

func slice(name: String) -> Variant:
	return slices.get(name)

func write_slice(name: String) -> Variant:
	_remember("slice:" + name, slices.get(name))
	_touched["slice:" + name] = true
	return slices[name]

func set_slice(name: String, value: Variant) -> void:
	_remember("slice:" + name, slices.get(name))
	_touched["slice:" + name] = true
	slices[name] = value

## Counts pending writes too, so a cache read mid-command sees the change.
func revision(key: String) -> int:
	return int(revisions.get(key, 0)) + (1 if _touched.has(key) else 0)

## Bumps revisions for everything written outside a transaction (fixed steps).
func settle() -> void:
	if _undo != null: return
	for key in _touched: revisions[key] = int(revisions.get(key, 0)) + 1
	_touched.clear()

# --- Transactions -----------------------------------------------------------

## Runs `body` (returning {ok, ...}). On failure every write is undone.
func transaction(body: Callable) -> Dictionary:
	if _undo != null: return body.call()
	_undo = {}
	var touched_before := _touched.duplicate()
	_touched.clear()
	var result = body.call()
	if not result is Dictionary: result = {"ok": false, "reason": "invalid_result"}
	if result.get("ok", false):
		for key in _touched: revisions[key] = int(revisions.get(key, 0)) + 1
	else:
		_rollback()
	_undo = null
	_touched = touched_before
	return result

func in_transaction() -> bool:
	return _undo != null

func _remember(key: String, value: Variant) -> void:
	if _undo == null or _undo.has(key): return
	_undo[key] = {"value": value.duplicate(true) if (value is Dictionary or value is Array) else value, "present": value != null}

func _remember_world(world: String) -> void:
	if _undo == null or _undo.has("world:" + world): return
	_undo["world:" + world] = {"value": worlds[world].duplicate(true) if worlds.has(world) else null, "present": worlds.has(world)}

func _rollback() -> void:
	# Whole worlds first; table and counter originals then apply on top, since
	# a world may have been remembered after some of its tables changed.
	for key in _undo:
		if not key.begins_with("world:"): continue
		var name: String = key.trim_prefix("world:")
		if _undo[key].present: worlds[name] = _undo[key].value
		else: worlds.erase(name)
	for key in _undo:
		var saved: Dictionary = _undo[key]
		if key.begins_with("world:"): continue
		if key.begins_with("slice:"):
			slices[key.trim_prefix("slice:")] = saved.value
		elif key.begins_with("next_id:"):
			if worlds.has(key.trim_prefix("next_id:")): worlds[key.trim_prefix("next_id:")].next_id = saved.value
		else:
			var parts: PackedStringArray = key.split("/", true, 1)
			if not worlds.has(parts[0]): continue
			if saved.present: worlds[parts[0]].tables[parts[1]] = saved.value
			else: worlds[parts[0]].tables.erase(parts[1])

# --- References -------------------------------------------------------------

## `handler(world, referrer_id, component, field, removed_id)` for "notify" refs.
func on_ref_removed(component: String, handler: Callable) -> void:
	_ref_handlers[component] = handler

## Removes an entity and applies every declared reference policy. Returns
## false (changing nothing outside a transaction's rollback) on "restrict".
func delete(world: String, id: String) -> bool:
	var pending := [id]
	var removed := {}
	while not pending.is_empty():
		var target: String = pending.pop_front()
		if removed.has(target): continue
		removed[target] = true
		for component in components:
			var spec: Dictionary = components[component]
			for field in spec.refs:
				var reference: Dictionary = spec.refs[field]
				if reference.get("soft", false): continue
				for referrer in table(world, component).keys():
					if removed.has(referrer) or str(row(world, component, referrer).get(field, "")) != target: continue
					match str(reference.get("on_delete", "clear")):
						"restrict": return false
						"cascade": pending.append(referrer)
						"notify":
							write(world, component)[referrer][field] = ""
							if _ref_handlers.has(component): _ref_handlers[component].call(world, referrer, component, field, target)
						_: write(world, component)[referrer][field] = ""
		for component in worlds[world].tables.keys():
			remove_row(world, component, target)
	return true

## Every hard reference that names a missing entity, as "component.field:id".
func dangling(world: String) -> Array:
	var problems: Array = []
	var known := {}
	for id in entity_ids(world): known[id] = true
	for component in components:
		for field in components[component].refs:
			if components[component].refs[field].get("soft", false): continue
			for id in table(world, component):
				var target := str(table(world, component)[id].get(field, ""))
				if not target.is_empty() and not known.has(target): problems.append("%s.%s:%s" % [component, field, id])
	return problems

# --- Hooks ------------------------------------------------------------------

## Handlers run in registration order; the feature registry fixes that order.
func on_hook(name: String, handler: Callable) -> void:
	if not _hooks.has(name): _hooks[name] = []
	_hooks[name].append(handler)

func hook(name: String, payload: Dictionary) -> Array:
	var results: Array = []
	for handler in _hooks.get(name, []): results.append(handler.call(payload))
	return results

# --- Effects ----------------------------------------------------------------

## effect: {id, stat, op: "add"|"mul", value, remaining (optional seconds), source}
func add_effect(world: String, id: String, effect: Dictionary) -> void:
	var effects: Dictionary = write(world, EFFECTS)
	var list: Array = effects.get(id, [])
	list = list.filter(func(existing): return existing.id != effect.id)
	list.append(effect.duplicate(true))
	effects[id] = list

func remove_effect(world: String, id: String, effect_id: String) -> void:
	if not has_row(world, EFFECTS, id): return
	var effects: Dictionary = write(world, EFFECTS)
	effects[id] = effects[id].filter(func(effect): return effect.id != effect_id)
	if effects[id].is_empty(): effects.erase(id)

## Base value with the entity's and the world's effects: adds, then multiplies.
func stat(world: String, id: String, name: String, base: float) -> float:
	var added := 0.0
	var factor := 1.0
	for owner in [id, "world"]:
		var list: Array = table(world, EFFECTS).get(owner, [])
		for effect in list:
			if effect.stat != name: continue
			if effect.op == "mul": factor *= float(effect.value)
			else: added += float(effect.value)
	return (base + added) * factor

func tick_effects(world: String, dt: float) -> Array:
	var expired: Array = []
	var effects: Dictionary = table(world, EFFECTS)
	if effects.is_empty(): return expired
	effects = write(world, EFFECTS)
	var owners := effects.keys()
	owners.sort()
	for owner in owners:
		var kept: Array = []
		for effect in effects[owner]:
			if effect.has("remaining"):
				effect.remaining = float(effect.remaining) - dt
				if float(effect.remaining) <= 0.000000001:
					expired.append({"entity": owner, "id": effect.id})
					continue
			kept.append(effect)
		if kept.is_empty(): effects.erase(owner)
		else: effects[owner] = kept
	return expired

# --- Saving -----------------------------------------------------------------

func save() -> Dictionary:
	var result := {"worlds": {}, "slices": {}}
	for world in worlds:
		var tables := {}
		for component in worlds[world].tables:
			var spec: Dictionary = components.get(component, {"version": 1, "derived": [], "persist": true})
			if not spec.persist: continue
			var rows: Dictionary = worlds[world].tables[component].duplicate(true)
			for id in rows:
				for field in spec.derived: rows[id].erase(field)
			tables[component] = {"version": int(spec.version), "rows": rows.values() if spec.get("ordered", false) else rows}
		result.worlds[world] = {"next_id": int(worlds[world].next_id), "tables": tables}
	for name in slice_specs:
		var spec: Dictionary = slice_specs[name]
		if not spec.persist: continue
		var value: Variant = spec.encode.call(slices.get(name)) if spec.encode.is_valid() else _copy(slices.get(name))
		result.slices[name] = {"version": int(spec.version), "data": value}
	return result

## Loads saved data, migrating durable tables and slices. Transient tables
## saved with another version are dropped. Returns false if any part is
## structurally invalid; the store is unchanged in that case.
func load_saved(data: Dictionary) -> bool:
	var loaded_worlds := {}
	var loaded_slices := {}
	if not data.get("worlds", {}) is Dictionary or not data.get("slices", {}) is Dictionary: return false
	for world in data.get("worlds", {}):
		var saved = data.worlds[world]
		if not saved is Dictionary or not _whole(saved.get("next_id")) or not saved.get("tables") is Dictionary: return false
		var tables := {}
		for component in saved.tables:
			var entry = saved.tables[component]
			var spec: Dictionary = components.get(component, {})
			if (spec.is_empty() and component != EFFECTS) or not spec.get("persist", true): return false
			if not entry is Dictionary or not _whole(entry.get("version")): return false
			var rows: Dictionary = {}
			if spec.get("ordered", false):
				if not entry.get("rows") is Array: return false
				for item in entry.rows:
					if not item is Dictionary or not item.get("id") is String or rows.has(item.id): return false
					rows[item.id] = _copy(item)
			elif entry.get("rows") is Dictionary: rows = _copy(entry.rows)
			else: return false
			var version := int(entry.version)
			if component != EFFECTS and version != int(spec.version):
				if not spec.durable: continue
				if version > int(spec.version) or version < 1: return false
				for step in range(version, int(spec.version)):
					rows = spec.migrations[step - 1].call(rows)
			for id in rows:
				if component == EFFECTS:
					if not rows[id] is Array or not rows[id].all(func(effect): return effect is Dictionary and effect.get("id") is String and effect.get("stat") is String): return false
					continue
				if not rows[id] is Dictionary: return false
				if component != EFFECTS:
					for field in spec.derived:
						if rows[id].has(field): return false
					var full: Dictionary = spec.fields.duplicate(true)
					full.merge(rows[id], true)
					rows[id] = full
			tables[component] = rows
		loaded_worlds[world] = {"next_id": int(saved.next_id), "tables": tables}
	for name in slice_specs:
		var spec: Dictionary = slice_specs[name]
		if not spec.persist and data.slices.has(name): return false
		if not data.slices.has(name):
			loaded_slices[name] = spec.initial.call()
			continue
		var entry = data.slices[name]
		if not entry is Dictionary or not _whole(entry.get("version")): return false
		var value = _copy(entry.get("data"))
		var version := int(entry.version)
		if version > int(spec.version) or version < 1: return false
		for step in range(version, int(spec.version)): value = spec.migrations[step - 1].call(value)
		if spec.decode.is_valid(): value = spec.decode.call(value)
		if spec.validate.is_valid() and not spec.validate.call(value): return false
		loaded_slices[name] = value
	var previous := [worlds, slices]
	worlds = loaded_worlds
	slices = loaded_slices
	for world in worlds:
		if not dangling(world).is_empty():
			worlds = previous[0]
			slices = previous[1]
			return false
	revisions.clear()
	return true

static func _whole(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) >= 0.0 and float(value) == floorf(float(value))

static func _copy(value: Variant) -> Variant:
	return value.duplicate(true) if (value is Dictionary or value is Array) else value
