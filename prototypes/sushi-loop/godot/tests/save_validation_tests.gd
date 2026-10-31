extends SceneTree
const Store = preload("res://scripts/save_store.gd")
var calls := 0
var checks := 0
var failures: Array[String] = []
func _init() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func accept(data: Dictionary) -> bool:
	calls += 1;return data.get("valid",false) == true
func reject(_data: Dictionary) -> bool:
	calls += 1;return false
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"):quit(1);return
	var directory := "user://validation-performance-%s" % Time.get_ticks_usec()
	var store := Store.new(directory);store.load_session(accept)
	check(store.save_session({"valid":true,"generation":1}),"valid first generation writes and verifies")
	var loaded: Dictionary = store.load_session();loaded.valid = false
	check(store.load_session().valid == true,"caller mutations cannot change the verified stored payload")
	var before := calls
	check(store.save_session({"valid":true,"generation":2}),"a fresh generation still passes domain and file verification")
	check(calls-before <= 2,"backup rotation does not repeatedly restore unchanged payloads during a frame")
	check(not store.save_session({"valid":false,"generation":3}) and store.load_session().generation == 2,"every incoming invalid state still rejects without replacing progress")
	var path := directory.path_join("session.json")
	var envelope: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	envelope.payload = JSON.stringify({"valid":false,"generation":4});envelope.sha256 = str(envelope.payload).sha256_text()
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(envelope))
	check(store.load_session().generation == 1 and store.source == "backup","changed hash-valid invalid bytes cannot reuse an older successful validation")
	check(store.load_session(reject).is_empty(),"replacing the validator rechecks previously valid primary and backup bytes")
	check(not store.save_session({"valid":true}),"failed recovery continues to preserve both files")
	check(store.clear_session(),"explicit test reset succeeds")
	store.load_session(accept);check(store.save_session({"valid":true,"generation":5}),"explicit validator/reset starts an independent valid generation")
	store.clear_session();DirAccess.remove_absolute(ProjectSettings.globalize_path(directory))
	print("Save validation: %s checks; %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
