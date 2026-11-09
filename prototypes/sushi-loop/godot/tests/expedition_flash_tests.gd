extends SceneTree
## A run that ends right after a hit must not carry the red damage flash (or
## the hit wobble) into the next dive. Drives the real expedition presentation.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
var app
var count := 0
var failures: Array[String] = []


## Waits out the shared scene transition (#28): close, loading beat, open.
func settle() -> void:
	for i in range(2): await process_frame
	var guard := 0
	while app.transition.busy and guard < 900:
		await process_frame; guard += 1

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func run() -> void:
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	var s = Session.new_session(24, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	app.session = s; app._refresh(); app._layout()
	var ui = app.expedition_ui
	app._open_landmark("Submarine"); await settle(); ui.start()
	await process_frame
	# A hit lands, and the run ends at once (Pause → Give up).
	ui._hit_flash = 1.0; ui._hull_pulse = 1.0; ui.view.damage(Vector2(5.5, 10.0), Vector2(5.5, 10.6))
	ui.pause(); ui.give_up()
	await process_frame
	check(ui.mode == "results", "the run ended on the hit")
	for i in range(3): await process_frame
	ui.finish_results(); await settle()
	app.session._state.expedition.charge = {"ready": true, "recharge_started": null}
	app._open_landmark("Submarine"); await settle()
	ui.start()
	await process_frame
	check(ui.mode == "travel", "a new dive starts")
	check(ui.damage_flash.modulate.a == 0.0 and ui._hit_flash == 0.0, "the new dive starts without the last run's red flash")
	check(ui.view._hurt == 0.0 and ui.view._knock == Vector2.ZERO, "and without its hit wobble or knock-back")
	print("Expedition flash tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() else 0)
