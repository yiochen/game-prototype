extends SceneTree
## Scene music: the restaurant, the Workshop room and a dive each have their own
## looping track, and a dive switches to the passage theme behind a portal and
## to the boss theme while the creature is there. Exactly one track sounds once a crossfade has settled.
const Session = preload("res://scripts/session.gd")
var app
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

## Real frames of the game's own loop until the crossfade has settled.
func play(seconds := 1.4) -> void:
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		app._process(0.05)
		await process_frame

## Lets a crossfade settle without advancing the game (an unsteered ship soon wrecks).
func rest(seconds := 1.4) -> void:
	await create_timer(seconds).timeout

## Plays on until the dive asks for `scene`.
func until(scene: String) -> bool:
	var guard := 0
	while app.expedition_ui.music_scene() != scene and guard < 900:
		app._process(0.05); await process_frame; guard += 1
	return app.expedition_ui.music_scene() == scene

func only(scene: String, where: String) -> void:
	check(app.audio.music_scene == scene, "%s asks for the %s track (got %s)" % [where, scene, app.audio.music_scene])
	for other in app.audio.MUSIC:
		var level: float = app.audio.music_level(other)
		check(is_equal_approx(level, 1.0 if other == scene else 0.0), "%s: %s track level %.2f" % [where, other, level])

func run() -> void:
	preload("res://scripts/game.gd").frozen_clock = 1000.0
	app = load("res://main.tscn").instantiate()
	root.add_child(app)
	await process_frame
	app.set_process(false)
	# The dive saves itself: keep it out of the folder later suites share.
	app.store = preload("res://scripts/save_store.gd").new("user://music-test")
	app.store.clear_session()
	# An earlier suite may have left a dive for the app to reopen.
	app.expedition_ui.mode = "hidden"; app.expedition_ui.hide()
	for scene in app.audio.MUSIC:
		check(app.audio.get_node_or_null("Music" + str(scene).capitalize()) != null, "%s track is loaded" % scene)
	var s := Session.new_session(29, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	app.session = s; app._refresh(); app._layout()
	await play()
	only("restaurant", "restaurant")
	app.workshop_ui.open(app.session.snapshot()); app._refresh()
	await play(0.3)
	check(app.audio.music_level("workshop") > 0.0 and app.audio.music_level("restaurant") > 0.0, "tracks crossfade rather than cut")
	await play()
	only("workshop", "Workshop room")
	app.workshop_ui.hide(); app._refresh()
	app.expedition_ui.open_prep(app.session.snapshot())
	await play()
	only("dive", "dive preparation")
	app.expedition_ui.start()
	await play()
	only("dive", "route")
	var dive: Dictionary = app.session._state.expedition.run
	var portal: Dictionary = preload("res://scripts/expedition/expedition_book.gd").run_route(dive).portals[0]
	dive.y = float(portal.y) + 0.3; dive.x = float(portal.x)
	check(await until("passage"), "entering a portal starts the passage theme")
	await rest()
	only("passage", "bonus passage")
	check(await until("dive") and app.expedition_ui.mode == "travel", "leaving the passage returns to the dive theme")
	await rest()
	only("dive", "route after the passage")
	app.expedition_ui.cheat_encounter()
	check(await until("boss"), "the creature's arrival starts the boss theme")
	await play()
	only("boss", "creature encounter")
	app.expedition_ui.pause()
	await play(0.3)
	check(app.audio.music_scene == "boss", "Pause keeps the boss theme")
	app.expedition_ui.give_up()
	await play()
	only("dive", "results")
	app.expedition_ui.mode = "hidden"; app.expedition_ui.hide()
	await play()
	only("restaurant", "back in the restaurant")
	app.audio.set_muted(true)
	app.store.clear_session()
	print("Scene music: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)
