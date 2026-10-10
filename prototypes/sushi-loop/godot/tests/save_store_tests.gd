extends SceneTree

const Store = preload("res://scripts/save_store.gd")
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures := 0
var test_directory := "user://save-store-test-%s" % Time.get_ticks_usec()

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var store := Store.new(test_directory)
	_expect(store.load_session(_valid_session).is_empty() and store.source == "none", "An absent save starts empty")
	var original := Session.new_session(813)
	original.advance(16.023456789)
	original.command({"type": "set_camera", "x": 12.5, "y": 32.125})
	var before := original.snapshot()
	_expect(not before.customers.is_empty() and before.stats.sales > 0, "The save scenario contains real customers and previously credited sales")
	_expect(store.save_session(original.save_data()), "An operating restaurant saves to disk")
	var restored := Session.new_session(2)
	_expect(restored.restore(store.load_session()), "A fresh public session restores the disk save")
	_expect(_same(restored.snapshot(), before) and store.source == "primary", "Coins, layout, food, customer progress and camera reopen unchanged")
	_expect(restored.restore(store.load_session()) and _same(restored.snapshot(), before), "Repeated reopening awards no extra sales and advances no time")
	var expected_events := original.advance(32.027777777)
	var restored_events := restored.advance(32.027777777)
	_expect(_same(restored_events, expected_events) and _same(original.snapshot(), restored.snapshot()), "Disk continuation matches uninterrupted service, including IDs and fractional time")
	_expect(store.save_session(original.save_data()), "A newer restaurant generation commits")
	_expect(not store.save_session({}), "An empty write cannot erase valid progress")
	var latest := Session.new_session()
	_expect(latest.restore(store.load_session()) and _same(latest.snapshot(), original.snapshot()), "Reopen retains the latest committed sales")
	_write("session.json", "{truncated")
	var recovered := Session.new_session()
	_expect(recovered.restore(store.load_session()) and _same(recovered.snapshot(), before) and store.source == "backup", "A torn primary recovers the prior playable restaurant without replaying sales")
	_expect(store.save_session(original.save_data()), "Saving after recovery repairs the primary")
	_write("session.json", "{}")
	_expect(recovered.restore(store.load_session()) and _same(recovered.snapshot(), before), "Damaged primary data never replaces the playable backup")
	_expect(store.save_session(original.save_data()), "Recovered play can commit again")
	var envelope: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(test_directory.path_join("session.json")))
	var incompatible := original.save_data()
	incompatible.version = 999
	envelope.payload = JSON.stringify(incompatible, "", true, true)
	envelope.sha256 = str(envelope.payload).sha256_text()
	_write("session.json", JSON.stringify(envelope))
	_expect(recovered.restore(store.load_session()) and _same(recovered.snapshot(), before), "A hash-valid incompatible session falls back to the playable backup")
	_expect(not store.save_session(incompatible), "Game-invalid state cannot replace the saved session")
	_expect(store.save_session(original.save_data()), "A valid session can repair an incompatible primary")
	_write("session.json", "{}")
	_expect(recovered.restore(store.load_session()) and _same(recovered.snapshot(), before), "Domain-invalid primary data does not overwrite the valid backup")
	_expect(store.save_session(original.save_data()), "Repaired game state can commit normally")
	envelope = JSON.parse_string(FileAccess.get_file_as_string(test_directory.path_join("session.json")))
	envelope.payload = JSON.stringify({"coins": 999999})
	_write("session.json", JSON.stringify(envelope))
	_expect(recovered.restore(store.load_session()) and _same(recovered.snapshot(), before), "Altered payload bytes are rejected even when their JSON still parses")
	envelope.version = 999
	_write("session.backup.json", JSON.stringify(envelope))
	_expect(store.load_session().is_empty() and not store.last_error.is_empty(), "Two invalid saves report failure without inventing progress")
	_expect(not store.save_session(original.save_data()), "A failed restore preserves both files until deliberate recovery")
	_expect(store.clear_session(), "Clearing removes the saved generations")
	_expect(store.load_session().is_empty() and store.last_error.is_empty(), "An explicitly cleared save is an ordinary fresh start")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(test_directory))
	print("SaveStore: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)

func _valid_session(data: Dictionary) -> bool:
	return Session.new().restore(data)

func _same(a: Variant, b: Variant) -> bool:
	# JSON has one numeric representation. Compare public numeric values rather
	# than relying on GDScript's stricter Dictionary int/float equality.
	if (a is int or a is float) and (b is int or b is float):
		return absf(float(a) - float(b)) < 0.000000001
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for key in a:
			if not b.has(key) or not _same(a[key], b[key]):
				return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for index in a.size():
			if not _same(a[index], b[index]):
				return false
		return true
	if a != b:
		print("Observable mismatch: ", a, " != ", b)
	return a == b

func _write(name: String, content: String) -> void:
	var file := FileAccess.open(test_directory.path_join(name), FileAccess.WRITE)
	file.store_string(content)
	file.close()

func _expect(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(description)
