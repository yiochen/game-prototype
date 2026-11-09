extends SceneTree
## #29: restaurant sound effects play only while the restaurant is on screen.
## A busy Live restaurant makes cook/load/coin cues; the full-screen Workshop
## room and an expedition (from Start through results) must not.
const Session = preload("res://scripts/session.gd")
const SERVICE_CUES := ["cook", "load", "coin"]
var count := 0
var failures: Array[String] = []
var heard: Array = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

## Real frames of the game's own loop for `seconds`, counting service cues.
func play(app, seconds: float) -> int:
	heard.clear()
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		app._process(0.1)
		await process_frame
	return heard.filter(func(cue): return cue in SERVICE_CUES).size()

func run() -> void:
	preload("res://scripts/game.gd").frozen_clock = 1000.0
	var app = load("res://main.tscn").instantiate()
	root.add_child(app)
	await process_frame
	app.set_process(false)
	app.audio.cue_played.connect(func(cue: String): heard.append(cue))
	var s := Session.new_session(29, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	for i in range(300): s.advance(0.1)
	app.session = s; app._refresh(); app._layout()
	check(await play(app, 4.0) > 0, "a busy Live restaurant plays service cues")
	app.workshop_ui.open(app.session.snapshot()); app._refresh()
	check(app.workshop_ui.visible, "Workshop room is open")
	var workshop := await play(app, 4.0)
	check(workshop == 0, "no restaurant cues behind the Workshop room (%d heard)" % workshop)
	app.workshop_ui.hide(); app._refresh()
	app.expedition_ui.open_prep(app.session.snapshot())
	app.expedition_ui.start()
	check(app.expedition_ui.mode == "travel", "dive started")
	var diving := await play(app, 4.0)
	check(diving == 0, "no restaurant cues during the dive (%d heard)" % diving)
	app.expedition_ui.pause(); app.expedition_ui.give_up()
	var results := await play(app, 2.0)
	check(results == 0, "no restaurant cues on the results (%d heard)" % results)
	print("Away audio: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)
