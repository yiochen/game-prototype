extends SceneTree
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
class Gate extends RefCounted:
	var entered := Semaphore.new()
	var release := Semaphore.new()
	var block_next := false
	func validate(data: Dictionary) -> bool:
		if block_next:
			block_next = false
			entered.post()
			release.wait()
		return Session.new().restore(data)
var checks := 0
var failures: Array[String] = []
func _init() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func same(a: Variant, b: Variant) -> bool:
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():return false
		for key in a:
			if not b.has(key) or not same(a[key],b[key]):return false
		return true
	if a is Array and b is Array:
		if a.size()!=b.size():return false
		for i in range(a.size()):
			if not same(a[i],b[i]):return false
		return true
	return a==b
func wait_entered(gate: Gate) -> bool:
	var deadline := Time.get_ticks_msec()+4000
	while not gate.entered.try_wait():
		if Time.get_ticks_msec()>deadline: return false
		await process_frame
	return true
func wait_completed(store: Store) -> Dictionary:
	var deadline := Time.get_ticks_msec()+4000
	while Time.get_ticks_msec()<=deadline:
		var result := store.poll_autosave()
		if not result.is_empty(): return result
		await process_frame
	return {}
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"):
		printerr("Autosave tests require isolated test storage.");quit(1);return
	var restaurant := Session.new_session(19)
	var initial: Dictionary = restaurant.save_data()
	var gate := Gate.new()
	var directory := "user://async-%s" % OS.get_process_id()
	var store := Store.new(directory)
	store.load_session(gate.validate)
	check(store.save_session(initial),"the fixture begins with an authentic durably saved restaurant")
	gate.block_next = true
	var first := initial.duplicate(true);first.state.coins = 130
	store.request_autosave(first)
	check(await wait_entered(gate),"autosave starts validation on the worker")
	# The worker cannot finish until release. These calls therefore prove the
	# simulation and newest-snapshot handoff do not wait for storage to complete.
	var middle := initial.duplicate(true);middle.state.coins = 140
	var newest := initial.duplicate(true);newest.state.coins = 150
	store.request_autosave(middle);store.request_autosave(newest)
	newest.state.coins = 999
	for i in range(5): restaurant.advance(.05);await process_frame
	check(restaurant.snapshot().elapsed>0 and store.poll_autosave().is_empty(),"foreground service and frames continue while a disk save is held")
	gate.release.post()
	check(store.finish_autosave() and int(store.load_session().state.coins)==150,"coalescing commits the newest independently owned snapshot")
	var invalid := initial.duplicate(true);invalid.state.coins = -1
	store.request_autosave(invalid)
	var failed := await wait_completed(store)
	check(not failed.is_empty() and not failed.ok and not failed.error.is_empty(),"worker validation failures return to the foreground")
	check(int(store.load_session().state.coins)==150,"an invalid autosave cannot replace playable progress")
	gate.block_next = true;store.request_autosave(first)
	check(await wait_entered(gate),"a later write can be held for an explicit-action race")
	store.request_autosave(middle)
	var action := initial.duplicate(true);action.state.coins = 200
	gate.release.post()
	check(store.save_session(action),"an explicit action joins the older writer and commits synchronously")
	for i in range(5):store.poll_autosave();await process_frame
	check(same(store.load_session(),action),"no older queued generation can overwrite an acknowledged action")
	gate.block_next = true;store.request_autosave(first)
	check(await wait_entered(gate),"the load-order fixture starts a worker")
	store.request_autosave(middle);gate.release.post()
	check(same(store.load_session(),middle),"a load flushes the most recent queued state before reading")
	store.request_autosave(action)
	check(store.clear_session(),"reset joins outstanding writes before removing the files")
	for i in range(5):store.poll_autosave();await process_frame
	check(store.load_session().is_empty() and not FileAccess.file_exists(directory.path_join("session.json")),"a completed older write cannot resurrect a reset restaurant")
	var app = load("res://main.tscn").instantiate()
	app.show_editor_gallery = true;app.simulation_enabled = false
	root.add_child(app);await process_frame;app.set_process(false)
	app.show_editor_gallery = false;app.session = Session.new_session(43)
	app.store = Store.new(directory.path_join("app"));app.store.load_session(gate.validate)
	gate.block_next = true;app.simulation_enabled = true
	app._process(.8)
	check(await wait_entered(gate),"the actual Live frame hands off an arrival save without blocking")
	app._process(.1)
	var before_pause: Dictionary = app.session.save_data()
	gate.release.post();app.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	check(same(app.store.load_session(),before_pause),"Android pause waits for the current exact restaurant, including newer foreground progress")
	app.notification(Node.NOTIFICATION_APPLICATION_RESUMED);app._process(120.0)
	check(same(app.session.save_data(),before_pause),"resuming asynchronous persistence still grants no offline income")
	app.queue_free();await process_frame
	print("Autosave: %s checks; %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
