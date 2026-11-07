extends SceneTree
## Headless state-layer benchmark: simulation steps, snapshots, saving and
## commands, plus the app's per-frame process. Desktop timings are relative
## evidence only; phone GDScript runs several times slower.
##   python3 tools/test_native.py --script tests/profile_state.gd -- --output <dir>
const Session = preload("res://scripts/session.gd")
const Game = preload("res://scripts/game.gd")

func _initialize() -> void:
	call_deferred("run")

func summary(values: Array) -> Dictionary:
	values.sort()
	var total := 0.0
	for value in values: total += value
	return {"median_us": values[values.size() / 2], "p95_us": values[mini(values.size() - 1, int(values.size() * 0.95))], "mean_us": snappedf(total / values.size(), 0.1), "samples": values.size()}

func time(callable: Callable, count: int, setup := Callable()) -> Dictionary:
	var samples: Array = []
	for index in range(count):
		var argument = setup.call() if setup.is_valid() else null
		var start := Time.get_ticks_usec()
		if setup.is_valid(): callable.call(argument)
		else: callable.call()
		samples.append(float(Time.get_ticks_usec() - start))
	return summary(samples)

## A starter restaurant after a minute of service, so seats, belts and chefs are busy.
func busy_session() -> Variant:
	var session = Session.new_session(41, {"starting_coins": 100000})
	session.command({"type": "set_mode", "mode": "live"})
	for step in range(1200): session.advance(0.05)
	return session

func chef_id(session) -> String:
	for item in session.snapshot().objects:
		if item.kind == "chef": return str(item.id)
	return ""

func run() -> void:
	var report := {"engine": Engine.get_version_info().string, "cases": {}}
	var base = busy_session()
	var saved: Dictionary = base.save_data()
	var text := JSON.stringify(saved, "", true, true)
	var snapshot: Dictionary = base.snapshot()
	report["scene"] = {"objects": snapshot.objects.size(), "customers": snapshot.customers.size(), "save_bytes": text.length()}
	var live = Session.new(); live.restore(saved)
	report.cases["advance_frame"] = time(func(): live.advance(1.0 / 60.0), 1200)
	report.cases["snapshot"] = time(func(): live.snapshot(), 300)
	report.cases["save_data"] = time(func(): live.save_data(), 300)
	report.cases["save_serialize"] = time(func(): JSON.stringify(live.save_data(), "", true, true), 100)
	report.cases["save_validate"] = time(func(): Game._valid_saved_session(JSON.parse_string(text)), 60)
	report.cases["load_restore"] = time(func(): Session.new().restore(JSON.parse_string(text)), 60)
	var id := chef_id(base)
	report.cases["command_level_up"] = time(func(session):
		session.command({"type": "level_up_chef", "chef_id": id, "expected_level": session.snapshot().objects.filter(func(c): return c.id == id)[0].level}),
		60, func():
			var copy = Session.new(); copy.restore(saved); return copy)
	report.cases["command_editor_rotate"] = time(func(session):
		session.command({"type": "editor_rotate", "id": "seat-1"}),
		60, func():
			var copy = Session.new(); copy.restore(saved); copy.command({"type": "set_mode", "mode": "edit"}); copy.command({"type": "editor_layer", "layer": "layout"}); return copy)
	# The whole app: simulation, refresh and view work for one frame.
	var app = load("res://main.tscn").instantiate()
	root.add_child(app)
	app.audio.set_muted(true)
	for frame in range(6): await process_frame
	app.set_process(false)
	app.session = Session.new(); app.session.restore(saved)
	app._refresh()
	report.cases["app_frame_live"] = time(func(): app._process(1.0 / 60.0), 600)
	app.session.command({"type": "set_mode", "mode": "edit"})
	report.cases["app_refresh_edit"] = time(func(): app._refresh(), 300)
	var output := ""
	var arguments := OS.get_cmdline_user_args()
	var at := arguments.find("--output")
	if at >= 0 and at + 1 < arguments.size(): output = arguments[at + 1]
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output)
		var file := FileAccess.open(output.path_join("state-profile.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(report, "\t"))
		file.close()
	print("PROFILE " + JSON.stringify(report))
	app.queue_free()
	for frame in range(3): await process_frame
	quit(0)
