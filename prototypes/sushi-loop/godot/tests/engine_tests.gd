extends SceneTree
## Pure tests for the generic state engine (store and machines).
const Store = preload("res://scripts/engine/store.gd")
const Machine = preload("res://scripts/engine/machine.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_test_transactions()
	_test_references()
	_test_hooks_and_effects()
	_test_saving()
	_test_machines()
	if failures.is_empty():
		print("PASS: %s engine checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		printerr("%s of %s engine checks failed" % [failures.size(), checks])
		quit(1)

func check(value: bool, description: String) -> void:
	checks += 1
	if not value: failures.append(description)

func _store() -> Store:
	var store := Store.new()
	store.define_component("placement", {"owner": "layout", "fields": {"x": 0, "y": 0, "facing": "south"}})
	store.define_component("seat", {"owner": "seating"})
	store.define_component("belt", {"owner": "belts", "fields": {"next": ""}, "refs": {"next": {"to": "belt", "on_delete": "clear"}}})
	store.define_component("visit", {"owner": "customers", "durable": false, "version": 3, "fields": {"claim": "", "target": ""},
		"refs": {"claim": {"to": "seat", "on_delete": "notify"}, "target": {"soft": true}}})
	store.define_component("hazard", {"owner": "hazards", "fields": {"on": ""}, "refs": {"on": {"to": "placement", "on_delete": "cascade"}}})
	store.define_component("station", {"owner": "kitchen", "version": 2, "fields": {"recipe_id": "", "progress": 0.0}, "derived": ["speed"],
		"migrations": [func(rows):
			for id in rows:
				rows[id].progress = float(rows[id].get("elapsed", 0.0)) / 4.0
				rows[id].erase("elapsed")
			return rows]})
	store.define_component("anchor", {"owner": "layout", "refs": {"of": {"to": "placement", "on_delete": "restrict"}}})
	store.define_slice("coins", {"owner": "economy", "initial": func(): return {"balance": 10}})
	store.create_world("restaurant")
	return store

func _test_transactions() -> void:
	var store := _store()
	var seat := store.spawn("restaurant", "seat")
	store.set_row("restaurant", "placement", seat, {"x": 2})
	store.settle()
	check(seat == "seat-1" and store.row("restaurant", "placement", seat) == {"x": 2, "y": 0, "facing": "south"}, "spawned rows take declared defaults")
	check(store.revision("restaurant/placement") == 1, "settling a step bumps the written table's revision")
	var failed := store.transaction(func():
		store.write("restaurant", "placement")[seat].x = 5
		store.set_row("restaurant", "seat", store.spawn("restaurant", "seat"), {})
		store.write_slice("coins").balance = 0
		return {"ok": false, "reason": "nope"})
	check(not failed.ok and store.row("restaurant", "placement", seat).x == 2 and store.table("restaurant", "seat").is_empty(), "a failed command leaves every table unchanged")
	check(store.slice("coins").balance == 10 and store.spawn("restaurant", "seat") == "seat-2", "a failed command restores slices and does not consume ids")
	check(store.revision("restaurant/placement") == 1, "a failed command bumps no revision")
	var ok := store.transaction(func():
		store.write("restaurant", "placement")[seat].x = 6
		return {"ok": true})
	check(ok.ok and store.row("restaurant", "placement", seat).x == 6 and store.revision("restaurant/placement") == 2, "a successful command commits and bumps revisions")
	var nested := store.transaction(func():
		var inner := store.transaction(func():
			store.write_slice("coins").balance = 99
			return {"ok": true})
		return {"ok": false, "inner": inner.ok})
	check(nested.inner and store.slice("coins").balance == 10, "a nested request joins the outer transaction and rolls back with it")
	store.transaction(func():
		store.create_world("run")
		store.set_row("run", "placement", store.spawn("run", "ship"), {})
		return {"ok": false})
	check(not store.worlds.has("run"), "a failed command removes a world it created")

func _test_references() -> void:
	var store := _store()
	var w := "restaurant"
	var a := store.spawn(w, "belt"); var b := store.spawn(w, "belt")
	store.set_row(w, "belt", a, {"next": b}); store.set_row(w, "belt", b, {"next": a})
	var seat := store.spawn(w, "seat"); store.set_row(w, "seat", seat, {}); store.set_row(w, "placement", seat, {})
	var guest := store.spawn(w, "customer"); store.set_row(w, "visit", guest, {"claim": seat, "target": seat})
	var fire := store.spawn(w, "fire"); store.set_row(w, "hazard", fire, {"on": seat})
	var notified: Array = []
	store.on_ref_removed("visit", func(world, referrer, component, field, removed): notified.append([referrer, field, removed]))
	check(store.delete(w, b) and store.row(w, "belt", a).next == "" and not store.has_row(w, "belt", b), "clear: removing a belt empties links to it")
	check(store.delete(w, seat), "deleting a seat succeeds")
	check(notified == [[guest, "claim", seat]] and store.row(w, "visit", guest).claim == "", "notify: the claim is cleared and its owner is told")
	check(store.row(w, "visit", guest).target == seat, "soft references are left for their readers to handle")
	check(not store.has_row(w, "hazard", fire), "cascade: a fire on removed equipment goes out with it")
	var pillar := store.spawn(w, "pillar"); store.set_row(w, "placement", pillar, {})
	store.set_row(w, "anchor", store.spawn(w, "sign"), {"of": pillar})
	var refused := store.transaction(func(): return {"ok": store.delete(w, pillar)})
	check(not refused.ok and store.has_row(w, "placement", pillar), "restrict: an anchored entity cannot be deleted")
	check(store.dangling(w).is_empty(), "no hard reference dangles after deletions")

func _test_hooks_and_effects() -> void:
	var store := _store()
	var order: Array = []
	store.on_hook("dish_served", func(payload): order.append("critic:" + payload.recipe))
	store.on_hook("dish_served", func(payload): order.append("celebrity"); return 3)
	var results := store.hook("dish_served", {"recipe": "tamago"})
	check(order == ["critic:tamago", "celebrity"] and results[1] == 3, "hook handlers run in registration order and return results")
	store.add_effect("restaurant", "guest-1", {"id": "tea", "stat": "patience_rate", "op": "mul", "value": 0.5, "remaining": 2.0})
	store.add_effect("restaurant", "world", {"id": "praise", "stat": "patience_rate", "op": "add", "value": 1.0})
	check(is_equal_approx(store.stat("restaurant", "guest-1", "patience_rate", 1.0), 1.0), "effects add then multiply, including world effects")
	check(is_equal_approx(store.stat("restaurant", "guest-2", "patience_rate", 1.0), 2.0), "world effects apply to every entity")
	var expired := store.tick_effects("restaurant", 2.0)
	check(expired == [{"entity": "guest-1", "id": "tea"}] and is_equal_approx(store.stat("restaurant", "guest-1", "patience_rate", 1.0), 2.0), "timed effects expire inside the step")
	store.add_effect("restaurant", "world", {"id": "praise", "stat": "patience_rate", "op": "add", "value": 2.0})
	check(store.table("restaurant", Store.EFFECTS).world.size() == 1, "re-adding an effect id replaces it")

func _test_saving() -> void:
	var store := _store()
	var w := "restaurant"
	var chef := store.spawn(w, "chef"); store.set_row(w, "station", chef, {"recipe_id": "salmon", "progress": 0.5, "speed": 1.7})
	var guest := store.spawn(w, "customer"); store.set_row(w, "visit", guest, {})
	var saved := store.save()
	check(not saved.worlds[w].tables.station.rows[chef].has("speed"), "derived fields are never saved")
	var text := JSON.stringify(saved, "", true, true)
	var reopened := _store()
	check(reopened.load_saved(JSON.parse_string(text)) and reopened.row(w, "station", chef).progress == 0.5 and reopened.spawn(w, "x") == "x-3", "a save reopens with rows and the id counter")
	var tampered: Dictionary = JSON.parse_string(text); tampered.worlds[w].tables.station.rows[chef].speed = 9
	check(not reopened.load_saved(tampered) and reopened.row(w, "station", chef).progress == 0.5, "a save containing a derived field is rejected and changes nothing")
	var old: Dictionary = JSON.parse_string(text)
	old.worlds[w].tables.station = {"version": 1, "rows": {chef: {"recipe_id": "salmon", "elapsed": 2.0}}}
	old.worlds[w].tables.visit.version = 2
	var migrated := _store()
	check(migrated.load_saved(old) and is_equal_approx(float(migrated.row(w, "station", chef).progress), 0.5), "durable tables migrate step by step")
	check(not migrated.table(w, "visit").has(guest), "transient tables from another version are dropped, not migrated")
	var broken: Dictionary = JSON.parse_string(text)
	broken.worlds[w].tables["belt"] = {"version": 1, "rows": {"belt-9": {"next": "belt-404"}}}
	check(not _store().load_saved(broken), "a hard reference to a missing entity is a load error")
	check(_store().load_saved({"worlds": {}, "slices": {}}) , "missing slices start from their initial value")
	var timed := _store()
	timed.add_effect(w, "guest-1", {"id": "tea", "stat": "patience_rate", "op": "mul", "value": 0.5, "remaining": 2.0})
	var with_effect := _store()
	check(with_effect.load_saved(JSON.parse_string(JSON.stringify(timed.save(), "", true, true))) and is_equal_approx(with_effect.stat(w, "guest-1", "patience_rate", 1.0), 0.5), "timed effects are saved and reopen")

func _test_machines() -> void:
	var station := {"initial": "idle", "states": {
		"idle": {"on": {"assign": {"to": "working", "guard": "has_recipe"}}},
		"working": {"progress": "duration", "done": "holding", "emit": "prepared"},
		"holding": {"on": {"belt_free": "loading"}},
		"loading": {"after": "loading_seconds", "to": "idle", "emit": "loaded"}}}
	var speed := {"value": 1.0}
	var resolve := func(name, row):
		match name:
			"has_recipe": return not str(row.get("recipe_id", "")).is_empty()
			"duration": return 4.0 / speed.value
			"loading_seconds": return 0.5
		return 0.0
	var row := {"recipe_id": ""}
	Machine.start(station, row)
	check(not Machine.send(station, row, "assign", resolve) and Machine.is_in(row, "idle"), "guards block a transition")
	row.recipe_id = "salmon"
	check(Machine.send(station, row, "assign", resolve) and Machine.is_in(row, "working"), "events move to their target")
	check(Machine.step(station, row, 2.0, resolve).is_empty() and is_equal_approx(float(row.progress), 0.5), "progress is a fraction of the duration")
	speed.value = 2.0
	var emitted := Machine.step(station, row, 1.5, resolve)
	check(emitted == ["prepared"] and Machine.is_in(row, "holding"), "a faster cook finishes the remaining half sooner, with no rescaling")
	check(not Machine.send(station, row, "assign", resolve), "states ignore events they do not accept")
	Machine.send(station, row, "belt_free")
	check(Machine.step(station, row, 0.7, resolve) == ["loaded"] and Machine.is_in(row, "idle") and is_equal_approx(float(row.elapsed), 0.2), "leftover time carries into the next state")
	check(Machine.valid(station, row) and not Machine.valid(station, {"machine": "cooking", "elapsed": 0.0, "progress": 0.0}), "a stored state must be declared")
