extends SceneTree
## Issue #28 native presentation: hut → iris → full-screen Workshop, tabs,
## one-level Upgrade that stays in the room, doubled presses, disabled and MAX
## cards, doorway/Back exits with NEW acknowledged, the outlined dock landmarks,
## and layouts that keep the ship clear of the tray on several portrait shapes.
const Session = preload("res://scripts/session.gd")
var app
var checks := 0
var failures: Array[String] = []

func _init() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func frames(n := 3) -> void:
	for i in range(n): await process_frame

func settle() -> void:
	# Waits out a running scene transition (close, loading beat, open).
	await frames(2)
	var guard := 0
	while app.transition.busy and guard < 600:
		await process_frame; guard += 1

func track(id: String) -> Dictionary:
	for t in app.session.snapshot().workshop.tracks:
		if t.id == id: return t
	return {}

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"): quit(1); return
	var dims := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dims.size() == 2: root.size = Vector2i(int(dims[0]), int(dims[1]))
	app = load("res://main.tscn").instantiate(); app.simulation_enabled = false; root.add_child(app)
	await frames()
	app.session = Session.new_session(19, {"starting_coins": 9180})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]:
		app.session.command({"type": "clear_trash", "id": identity})
	app.session.command({"type": "reveal_dock"})
	app.session.command({"type": "set_camera", "x": 4, "y": 0})
	app.session._state.expedition.salvage = 300
	app._refresh(); app._layout(); await frames()

	# Restaurant: in Live the dock landmarks are interactable (outlined), in Edit they are plain.
	check(app.world.landmarks_interactable(), "the open dock's ship and hut are interactable in Live")
	var plan: Array = app.world.render_plan()
	check(plan.filter(func(p): return p.get("kind") == "ship").size() == 1, "the dock draws the ImageGen ship")
	var camera: Dictionary = app.session.snapshot().camera.duplicate()

	# Hut → iris → Workshop.
	app._open_landmark("Workshop")
	check(app.transition.busy, "entering the Workshop runs the shared scene transition")
	await settle()
	check(app.workshop_ui.visible, "the Workshop room opens")
	check(app.workshop_ui.group == "equipment" and app.workshop_ui.rows.size() == 3, "Equipment shows three cards")
	check(app.get_viewport().gui_get_focus_owner() == app.workshop_ui.rows.hull.buy, "focus starts on the first affordable Upgrade")

	# Upgrade: one level, stays in the room; a doubled press of the same purchase pays once.
	var salvage: int = app.session.snapshot().workshop.salvage
	# The same purchase delivered twice (a replayed press) carries the same token and pays once.
	var request := {"type": "workshop_upgrade", "id": "hull", "token": "hull:1"}
	app._workshop_upgrade(request)
	app._workshop_upgrade(request)
	await frames()
	check(track("hull").level == 2 and app.session.snapshot().workshop.salvage == salvage - 60, "a replayed press pays one level")
	check(app.workshop_ui.visible, "the Workshop stays open after Upgrade")
	app.workshop_ui._request("hull")
	await frames()
	check(track("hull").level == 3 and track("hull").new and app.workshop_ui.rows.hull.new_tag.visible, "a later press buys the next level and shows NEW at the new look")
	check(app.workshop_ui.ship.tiers.get("hull") == 2, "the ship on the cradle swaps to the reinforced hull")

	# Tabs: the shared control switches to Power-ups; copy has no internal units.
	app.workshop_ui.select_group("powerup"); await frames()
	check(app.workshop_ui.rows.keys() == ["shield", "passage", "launch"], "Power-ups shows Shield, Passage and Shield at start")
	for id in app.workshop_ui.rows:
		var text: String = app.workshop_ui.rows[id].line_a.text + " " + app.workshop_ui.rows[id].next.text
		check(not ("rows" in text or "tiles" in text or " s " in text), "%s card shows no internal units" % id)
	check(app.workshop_ui.rows.launch.next.text == "Unlock", "Shield at start starts at Unlock")

	# Unaffordable: disabled with no shortage message; MAX keeps the card without cost.
	app.session._state.expedition.salvage = 5
	app._refresh(); await frames()
	check(app.workshop_ui.rows.values().all(func(r): return r.buy.disabled), "every Upgrade is disabled without enough salvage")
	app.session._state.expedition.salvage = 5000
	app.workshop_ui.select_group("equipment"); await frames()
	for i in range(3): app.workshop_ui._request("collector"); await frames()
	check(track("collector").max and not app.workshop_ui.rows.collector.buy.visible and app.workshop_ui.rows.collector.marks.maxed, "a capped track keeps its card with MAX and no cost")

	# Layout: the ship sits in the free floor above the tray; touch targets ≥ 44 px.
	var physical := maxf(.001, app.get_viewport_transform().get_scale().x)
	var tray_top: float = app.workshop_ui.tray.get_global_rect().position.y
	check(app.workshop_ui.hero.get_global_rect().end.y <= tray_top + 1.0, "the cradle stays above the card tray")
	for button in [app.workshop_ui.door, app.workshop_ui.tabs[0], app.workshop_ui.rows.hull.buy]:
		check(minf(button.size.x, button.size.y) * physical >= 43.9, "touch target is at least 44 px: " + str(button.accessibility_name))

	# Back leaves through the same transition; NEW is acknowledged; the camera is unchanged.
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST)
	await settle()
	check(not app.workshop_ui.visible, "Back leaves the Workshop")
	check(not track("hull").new, "leaving acknowledges NEW")
	check(app.session.snapshot().camera == camera, "the restaurant camera is restored exactly")

	# Every portrait shape keeps the room usable.
	for shape in [Vector2i(360, 640), Vector2i(390, 844), Vector2i(360, 840), Vector2i(600, 800)]:
		root.size = shape; app._layout(); await frames()
		app._open_landmark("Workshop"); await settle()
		var hero: Rect2 = app.workshop_ui.hero.get_global_rect()
		var tray: Rect2 = app.workshop_ui.tray.get_global_rect()
		check(hero.end.y <= tray.position.y + 1.0 and hero.size.y > 40.0, "%s: the ship has floor above the tray" % shape)
		check(app.workshop_ui.sign_label.get_global_rect().position.y >= 0.0, "%s: the sign stays on screen" % shape)
		app.workshop_ui.leave(); await settle()

	print("Workshop native tests: %d checks, %d failures" % [checks, failures.size()])
	quit(1 if failures.size() else 0)
